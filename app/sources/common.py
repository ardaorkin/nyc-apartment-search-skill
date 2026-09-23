"""Shared extraction helpers for source adapters: sitemap parsing, JSON-LD extraction,
generic HTML fallbacks. Structured data first, semantic HTML second, per the adapter
contract in references/sources.md."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Iterable
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from models import Listing
from parsers.address import extract_street_number, extract_unit, normalize_address
from parsers.pets import classify_pet_policy
from parsers.rent import parse_rent

def parse_sitemap_urls(xml_text: str) -> list[str]:
    urls: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return urls
    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            urls.append(elem.text.strip())
    return urls


def filter_urls_by_area(urls: Iterable[str], keywords: list[str]) -> list[str]:
    lowered = [(u, u.lower()) for u in urls]
    matches = [u for u, low in lowered if any(k in low for k in keywords)]
    return matches


def area_keywords_from_config(location: dict) -> list[str] | None:
    """Derive URL/sitemap-path matching keywords from the configured neighborhood/borough.
    Returns None (no filter -- citywide) when neither is set. Generates the common slug
    variants a site's URL paths tend to use (hyphenated, underscored, no separator) for
    each configured value; doesn't know site-specific alternate/adjacent neighborhood
    names (e.g. a specific site listing a sub-neighborhood under a different label) --
    that kind of domain knowledge has to be added per-source, not guessed generically."""
    values = [location.get("neighborhood"), location.get("borough")]
    keywords: list[str] = []
    for raw in values:
        if not raw:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", raw.strip().lower()).strip("-")
        if not slug:
            continue
        keywords.extend({slug, slug.replace("-", "_"), slug.replace("-", "")})
    return sorted(set(keywords)) or None


def looks_like_rental_url(url: str) -> bool:
    low = url.lower()
    return any(k in low for k in ["rent", "rental", "lease"]) and not any(
        k in low for k in ["for-sale", "/sale/", "sold"]
    )


def _add_jsonld_payload(data, blocks: list[dict]) -> None:
    if isinstance(data, list):
        blocks.extend(d for d in data if isinstance(d, dict))
    elif isinstance(data, dict):
        if "@graph" in data and isinstance(data["@graph"], list):
            blocks.extend(d for d in data["@graph"] if isinstance(d, dict))
        else:
            blocks.append(data)


_NEXTJS_STREAM_DECODER = json.JSONDecoder()


def _extract_nextjs_streamed_jsonld(html: str) -> list[dict]:
    """Next.js (app router) streams JSON-LD via `self.__next_s.push([0,{"type":
    "application/ld+json","children":"<escaped json>"}])` instead of a literal
    `<script type="application/ld+json">` tag, so the normal BeautifulSoup lookup
    never sees it. Locate each `"children":"..."` JSON string token directly with
    raw_decode (handles the escaping correctly regardless of surrounding content)
    and parse the resulting JSON-LD payload from inside it."""
    blocks: list[dict] = []
    for marker in re.finditer(r'"type":"application/ld\+json","children":"', html):
        start = marker.end() - 1  # position of the opening quote of the JSON string
        try:
            inner_str, _ = _NEXTJS_STREAM_DECODER.raw_decode(html, start)
        except json.JSONDecodeError:
            continue
        if not isinstance(inner_str, str):
            continue
        try:
            data = json.loads(inner_str)
        except json.JSONDecodeError:
            continue
        _add_jsonld_payload(data, blocks)
    return blocks


def extract_jsonld_blocks(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    blocks: list[dict] = []
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        if not tag.string:
            continue
        try:
            data = json.loads(tag.string)
        except (json.JSONDecodeError, TypeError):
            continue
        _add_jsonld_payload(data, blocks)
    blocks.extend(_extract_nextjs_streamed_jsonld(html))
    return blocks


def find_residence_blocks(blocks: list[dict]) -> list[dict]:
    types = {"Apartment", "Residence", "House", "Product", "Offer", "SingleFamilyResidence", "ApartmentComplex"}
    return [b for b in blocks if str(b.get("@type", "")) in types or any(t in types for t in (b.get("@type") or []) if isinstance(b.get("@type"), list))]


def merge_residence_blocks(blocks: list[dict]) -> dict:
    """A single listing page can carry more than one matching JSON-LD block for the
    same real apartment -- e.g. an `Apartment`/`Residence` block with the clean
    name/address/description, plus a separate `Product` block that only exists to
    carry the `Offer` (price). Calling listing_from_jsonld once per block (the old
    behavior) created two fragmented Listings for one real unit -- often with
    different address text, so dedupe.py couldn't even merge them back together.
    Merges into one dict instead: first block's values win, later blocks only fill
    genuine gaps, so the cleaner descriptive block's name/address wins over a
    price-only block's noisier one."""
    if not blocks:
        return {}
    merged = dict(blocks[0])
    for block in blocks[1:]:
        for key, value in block.items():
            if value in (None, "", {}, []):
                continue
            if merged.get(key) in (None, "", {}, []):
                merged[key] = value
    return merged


def listing_from_jsonld(block: dict, source: str, url: str, user_agent_neighborhood_hint: str | None = None) -> Listing | None:
    name = block.get("name") or block.get("headline")
    address_block = block.get("address") or {}
    if isinstance(address_block, dict):
        street = address_block.get("streetAddress")
        locality = address_block.get("addressLocality")
    else:
        street = str(address_block) if address_block else None
        locality = None
    address = street or name
    offers = block.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price") if isinstance(offers, dict) else None
    rent = parse_rent(price)
    description = block.get("description")
    pet_status, cat_allowed, dog_allowed = classify_pet_policy(description)

    if not address and not rent:
        return None

    floor_plan = block.get("accommodationFloorPlan") or {}
    bedrooms = floor_plan.get("numberOfBedroomsTotal") if isinstance(floor_plan, dict) else None
    if bedrooms is None:
        bedrooms = block.get("numberOfBedroomsTotal")
    # Deliberately NOT falling back to numberOfRooms: schema.org's own spec allows
    # it to mean either bedroom count or total room count depending on the site,
    # and real Corcoran data confirmed it means the latter here (a $3,875/mo
    # Bed-Stuy 1BR reported numberOfRooms=4) -- trusting it produced a fabricated,
    # wrong bedroom count rather than an honest unknown.
    if bedrooms is None:
        bedrooms = guess_bedrooms_from_text(description) if description else guess_bedrooms_from_text(name)
    try:
        bedrooms = float(bedrooms) if bedrooms is not None else None
    except (TypeError, ValueError):
        bedrooms = None

    doorman = None
    if description:
        doorman = "doorman" in description.lower()

    return Listing(
        source=source,
        listing_url=url,
        source_urls=[url],
        address=normalize_address(address),
        unit=extract_unit(name or ""),
        neighborhood=locality or user_agent_neighborhood_hint,
        street_number=str(extract_street_number(address)) if extract_street_number(address) else None,
        monthly_rent=rent,
        bedrooms=bedrooms,
        description=description,
        doorman=doorman,
        pet_policy=description if description and ("pet" in description.lower() or "dog" in description.lower() or "cat" in description.lower()) else None,
        pet_status=pet_status,
        cat_allowed=cat_allowed,
        dog_allowed=dog_allowed,
        brokerage_or_management_company=source,
        checked_at=datetime.now(timezone.utc),
    )


_BED_RE = re.compile(r"(\d+(?:\.\d)?)\s*(?:bed|br)\b", re.IGNORECASE)
_STUDIO_RE = re.compile(r"\bstudio\b", re.IGNORECASE)


def guess_bedrooms_from_text(text: str | None) -> float | None:
    if not text:
        return None
    if _STUDIO_RE.search(text):
        return 0.0
    m = _BED_RE.search(text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None
