"""Glenwood: no JSON-LD anywhere on the site. Real per-unit detail pages exist at
/listing-detail/?lid=N (a plain info page, distinct from the leads.glenwoodnyc.com
scheduling-CTA links that sit next to them on the card) and render clean, consistent
plain text: "<Building> | N BR M Bath <layout> | $ X,XXX /mo." plus a fees/description
block. Structured data isn't available, so this parses that semantic text directly.

The homepage's "featured properties" carousel is server-rendered with real
/listing-detail/?lid= links; the /search-result/ page that would otherwise be the
fuller index is client-rendered (AJAX) with none in the initial HTML, so the
homepage is used as the discovery index instead."""
from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup

from models import Listing, SourceResult, SourceStatus
from parsers.address import normalize_address
from parsers.pets import classify_pet_policy
from parsers.rent import parse_rent
from sources.base import BaseAdapter, BlockedError

logger = logging.getLogger("nyc_apartment_search")

MAX_DETAIL_PAGES = 20

_BEDBATH_RE = re.compile(r"(\d+)\s*BR\s*(\d+)\s*Bath", re.IGNORECASE)
_PRICE_RE = re.compile(r"[\d,]+")


class GlenwoodAdapter(BaseAdapter):
    name = "glenwood"
    base_url = "https://www.glenwoodnyc.com"
    listing_index_url = "https://www.glenwoodnyc.com/"

    def _detail_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls = []
        for a in soup.find_all("a", href=re.compile(r"listing-detail/\?lid=\d+")):
            href = a.get("href")
            if not href:
                continue
            urls.append(href if href.startswith("http") else self.base_url + href)
        seen: set[str] = set()
        deduped = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped

    def _parse_detail(self, html: str, url: str) -> Listing | None:
        soup = BeautifulSoup(html, "lxml")

        title_el = soup.find("h2", class_="properties_title")
        price_els = title_el.find_all("p", class_="pprice") if title_el else []
        building_link = title_el.find("a") if title_el else None
        if not title_el or not building_link or len(price_els) < 2:
            return None
        building = building_link.get_text(strip=True)
        bedbath_match = _BEDBATH_RE.search(price_els[0].get_text(" ", strip=True))
        price_match = _PRICE_RE.search(price_els[1].get_text(strip=True))
        if not bedbath_match or not price_match:
            return None
        beds, baths = bedbath_match.groups()
        rent = parse_rent(price_match.group())

        breadcrumb_links = soup.select("div.bbreanb ul li a") or soup.select("ol.breadcrumb li a")
        # breadcrumb is Home > Properties > <Area> > <Building> -- the area is always
        # second-to-last regardless of how many crumbs precede it.
        neighborhood = breadcrumb_links[-2].get_text(strip=True) if len(breadcrumb_links) > 1 else None

        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        desc_match = re.search(r"Apartment Description\s+Apartment Description\s+(.*?)(?:--------|\Z)", text)
        description = desc_match.group(1).strip() if desc_match else None
        pet_status, cat_allowed, dog_allowed = classify_pet_policy(description)
        doorman = "doorman" in text.lower()

        # The page exposes no human-readable apartment number, but each unit has its
        # own /listing-detail/?lid=N page -- without this, dedupe.py's _similar()
        # treats "both units unknown" as compatible and silently merges two
        # different apartments in the same building into one listing, discarding
        # the other's data entirely.
        lid_match = re.search(r"lid=(\d+)", url)
        unit = f"LID{lid_match.group(1)}" if lid_match else None

        return Listing(
            source=self.name,
            listing_url=url,
            source_urls=[url],
            address=normalize_address(building.strip()),
            unit=unit,
            neighborhood=neighborhood,
            bedrooms=float(beds),
            bathrooms=float(baths),
            monthly_rent=rent,
            description=description,
            doorman=doorman or None,
            pet_policy=description,
            pet_status=pet_status,
            cat_allowed=cat_allowed,
            dog_allowed=dog_allowed,
            brokerage_or_management_company="Glenwood",
        )

    def fetch(self) -> SourceResult:
        try:
            index_html = self.get(self.listing_index_url)
        except BlockedError as exc:
            return self.blocked_result(str(exc))

        detail_urls = self._detail_urls(index_html)
        if not detail_urls:
            return SourceResult(
                name=self.name,
                status=SourceStatus.OK,
                listings=[],
                note="listing index reachable but no /listing-detail/ links found",
            )

        listings: list[Listing] = []
        errors = 0
        for url in detail_urls[:MAX_DETAIL_PAGES]:
            try:
                html = self.get(url)
            except BlockedError as exc:
                errors += 1
                logger.info("%s: skipping %s (%s)", self.name, url, exc)
                continue
            try:
                listing = self._parse_detail(html, url)
                if listing:
                    listings.append(listing)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning("%s: parse failure on %s: %s (cached at %s)", self.name, url, exc, self._cache_path(url))
                continue

        status = SourceStatus.OK if errors == 0 else SourceStatus.PARTIAL
        note = None if errors == 0 else f"{errors} of {len(detail_urls[:MAX_DETAIL_PAGES])} candidate detail pages failed"
        return SourceResult(name=self.name, status=status, listings=listings, note=note)
