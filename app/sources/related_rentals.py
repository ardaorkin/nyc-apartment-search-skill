"""Related Rentals' actual consumer brand lives at relatedrentals.com, not
related.com (the corporate parent site the config previously pointed at, which has
no rental inventory at all). relatedrentals.com's sitemap has real per-unit detail
pages nested under /apartment-rentals/<city>/<neighborhood>/<building>/<unit>, across
multiple cities -- no JSON-LD, but a clean, consistent plain-text pattern on the unit
page itself: "<Building> | <Address> N Bedroom(s), M Bath[, Furnished] Price: X
Available: Y".

Always restricted to the /new-york-city/ path segment -- this skill's one fixed
setting -- regardless of what area within NYC is configured. The NYC sitemap alone
has ~5k unit pages across many neighborhoods; fetching all of them under the
configured rate limit isn't practical in one run, so when a specific neighborhood is
configured this also filters to that neighborhood's own path segment (verified
against the real URL structure, not a nearby-neighborhood guess). With no
neighborhood configured, no further filter is applied -- MAX_DETAIL_PAGES below caps
the actual page count either way, so the citywide case just gets the first N pages
across all neighborhoods rather than an arbitrary hardcoded pair."""
from __future__ import annotations

import logging
import re

from models import Listing, SourceResult, SourceStatus
from parsers.address import normalize_address
from parsers.pets import classify_pet_policy
from parsers.rent import parse_rent
from sources.base import BaseAdapter, BlockedError
from sources.common import parse_sitemap_urls

logger = logging.getLogger("nyc_apartment_search")

MAX_DETAIL_PAGES = 20
NYC_PATH_SEGMENT = "/apartment-rentals/new-york-city/"

# The page's own "More from Related" sidebar nav text ("...Our Company View All
# <Building> | <Address>") sits directly before the building/address pair with no
# other delimiter, so the regex over-captures those nav words; strip them off the
# front of the match rather than fighting the ambiguity in the regex itself.
_NAV_STOPWORDS = {
    "view", "all", "our", "company", "more", "from", "related", "luxury", "rentals",
    "condominiums", "page", "sections", "contact", "agent", "email", "benefits",
    "furnished", "apartments", "blog",
}
_ADDRESS_RE = re.compile(r"((?:[A-Z][\w'.]*\s+){0,4}[A-Z][\w'.]*)\s*\|\s*(\d[\w\s]*?New York,\s*NY\s*\d{5})")
_DETAIL_RE = re.compile(
    r"(Alcove\s+Studio|Studio|\d+(?:\.\d)?\s*Bedroom)s?,\s*(\d+(?:\.\d)?)\s*Bath.*?"
    r"Price:\s*\$?\s*([\d,]+)\s*Available:\s*([\w /]+?)(?:\s*DOWNLOAD|\s*VIEW|\s*$)",
    re.IGNORECASE,
)
# The sitemap lists unit pages that are no longer offered -- the site keeps the page
# up with this exact message instead of a 404. bed/bath/price/availability are gone
# from the page, so _DETAIL_RE can't match, but that's a real off-market signal, not
# a parse failure -- see the off-market branch in _parse_unit_page.
_OFF_MARKET_MARKER = "no longer available"


def _bedrooms_from_url(url: str) -> float | None:
    """bed count is also encoded in the unit URL's own slug (e.g. .../1-bedroom-1-
    bath-26300, .../studio-1-bath-26173) -- reading it from there for an off-market
    page (where the page text no longer states it) is using the site's own
    structured URL data, not a guess."""
    slug = url.rsplit("/", 1)[-1].lower()
    if "studio" in slug:
        return 0.0
    match = re.search(r"(\d+)-bedroom", slug)
    return float(match.group(1)) if match else None


def _clean_building_name(raw: str) -> str:
    words = raw.split()
    while words and words[0].lower() in _NAV_STOPWORDS:
        words.pop(0)
    return " ".join(words) or raw


class RelatedRentalsAdapter(BaseAdapter):
    name = "related_rentals"
    base_url = "https://www.relatedrentals.com"
    sitemap_index_url = "https://www.relatedrentals.com/sitemap.xml"

    def _collect_unit_urls(self) -> list[str]:
        neighborhood = self.config.get("location", {}).get("neighborhood")
        neighborhood_segment = None
        if neighborhood:
            slug = re.sub(r"[^a-z0-9]+", "-", neighborhood.strip().lower()).strip("-")
            if slug:
                neighborhood_segment = f"{NYC_PATH_SEGMENT}{slug}/"

        index_xml = self.get(self.sitemap_index_url)
        page_sitemaps = parse_sitemap_urls(index_xml)
        unit_urls: list[str] = []
        for sm_url in page_sitemaps:
            try:
                xml = self.get(sm_url)
            except BlockedError:
                continue
            for url in parse_sitemap_urls(xml):
                if NYC_PATH_SEGMENT not in url or not re.search(r"-\d{4,}$", url):
                    continue
                if neighborhood_segment and neighborhood_segment not in url:
                    continue
                unit_urls.append(url)
        return unit_urls

    @staticmethod
    def _neighborhood_from_url(url: str) -> str | None:
        m = re.search(r"/apartment-rentals/new-york-city/([a-z0-9-]+)/", url)
        if not m:
            return None
        return m.group(1).replace("-", " ").title()

    @staticmethod
    def _building_from_url(url: str) -> str | None:
        """.../new-york-city/<neighborhood>/<building>/<unit-slug> -- used only for
        the off-market branch, where the page's own "<Building> | <Address>" header
        is replaced by a "<Neighborhood> <Bed/Bath summary> | <Address>" line
        instead, so _ADDRESS_RE's group(1) is not a building name on those pages."""
        m = re.search(r"/apartment-rentals/new-york-city/[a-z0-9-]+/([a-z0-9-]+)/[^/]+$", url)
        if not m:
            return None
        return m.group(1).replace("-", " ").title()

    def _parse_unit_page(self, html: str, url: str) -> Listing | None:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)

        addr_match = _ADDRESS_RE.search(text)
        if not addr_match:
            return None
        building = _clean_building_name(addr_match.group(1))
        address = addr_match.group(2).strip()
        neighborhood = self._neighborhood_from_url(url)

        # No human-readable apartment number is exposed on the page, but every unit
        # URL ends in its own numeric ID (see the -\d{4,}$ check in
        # _collect_unit_urls) -- without this, dedupe.py's _similar() treats "both
        # units unknown" as compatible and silently merges two different apartments
        # in the same building into one listing, discarding the other's data.
        unit_id_match = re.search(r"-(\d{4,})$", url)
        unit = f"UNIT{unit_id_match.group(1)}" if unit_id_match else None

        detail_match = _DETAIL_RE.search(text[addr_match.end(): addr_match.end() + 300])
        if not detail_match:
            if _OFF_MARKET_MARKER in text.lower():
                # Never silently discard a stale listing -- classify it.
                # classify_freshness (parsers/freshness.py) reads this marker
                # straight from description and sets ActiveStatus.OFF_MARKET.
                # `building` (addr_match group 1) is unreliable here -- the
                # off-market page's header reads "<Neighborhood> <Bed/Bath> |
                # <Address>", not "<Building> | <Address>", so group 1 is a
                # bed/bath summary, not a building name. The URL's own building
                # slug is reliable on both page types; use that instead.
                off_market_building = self._building_from_url(url)
                return Listing(
                    source=self.name,
                    listing_url=url,
                    source_urls=[url],
                    address=normalize_address(f"{off_market_building} {address}" if off_market_building else address),
                    unit=unit,
                    neighborhood=neighborhood,
                    bedrooms=_bedrooms_from_url(url),
                    description="No longer available per source page.",
                )
            return None
        bed_label, baths, price_raw, available = detail_match.groups()
        bed_label_low = bed_label.strip().lower()
        bedrooms = 0.0 if "studio" in bed_label_low else float(re.search(r"[\d.]+", bed_label_low).group())
        rent = parse_rent(price_raw)
        furnished = "furnished" in text.lower()
        pet_status, cat_allowed, dog_allowed = classify_pet_policy(None)
        doorman = "doorman" in text.lower() or None

        return Listing(
            source=self.name,
            listing_url=url,
            source_urls=[url],
            address=normalize_address(f"{building} {address}"),
            unit=unit,
            neighborhood=neighborhood,
            bedrooms=bedrooms,
            bathrooms=float(baths),
            monthly_rent=rent,
            available_date=available.strip() or None,
            furnished=furnished or None,
            doorman=doorman,
            pet_status=pet_status,
            cat_allowed=cat_allowed,
            dog_allowed=dog_allowed,
            brokerage_or_management_company="Related Rentals",
        )

    def fetch(self) -> SourceResult:
        try:
            unit_urls = self._collect_unit_urls()
        except BlockedError as exc:
            return self.blocked_result(str(exc))
        except Exception as exc:  # noqa: BLE001
            return self.error_result(f"unexpected error collecting sitemap: {exc}")

        if not unit_urls:
            return SourceResult(
                name=self.name,
                status=SourceStatus.OK,
                listings=[],
                note="sitemap reachable but no NYC unit pages matched the configured area",
            )

        listings: list[Listing] = []
        errors = 0
        for url in unit_urls[:MAX_DETAIL_PAGES]:
            try:
                html = self.get(url)
            except BlockedError as exc:
                errors += 1
                logger.info("%s: skipping %s (%s)", self.name, url, exc)
                continue
            try:
                listing = self._parse_unit_page(html, url)
                if listing:
                    listings.append(listing)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning("%s: parse failure on %s: %s (cached at %s)", self.name, url, exc, self._cache_path(url))
                continue

        status = SourceStatus.OK if errors == 0 else SourceStatus.PARTIAL
        note = None if errors == 0 else f"{errors} of {len(unit_urls[:MAX_DETAIL_PAGES])} candidate detail pages failed"
        return SourceResult(name=self.name, status=status, listings=listings, note=note)
