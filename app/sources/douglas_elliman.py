"""Douglas Elliman: area search pages are server-rendered (Next.js) with real listing
cards linking to per-unit detail pages. Detail pages carry JSON-LD, but streamed via
Next.js's `__next_s.push` mechanism rather than a literal <script type="application/
ld+json"> tag -- sources/common.py's extract_jsonld_blocks handles both forms.

Search page URL is `/rentals/<slug>-new-york-ny`. Verified directly (not guessed): a
configured neighborhood or borough slugs straight into that pattern and returns real
listing cards (e.g. /rentals/manhattan-new-york-ny, /rentals/brooklyn-new-york-ny, all
five boroughs checked); with nothing configured, /rentals/new-york-ny is a real citywide
index with the same card markup, also verified directly against the live site."""
from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup

from models import Listing, SourceResult, SourceStatus
from sources.base import BaseAdapter, BlockedError
from sources.common import extract_jsonld_blocks, find_residence_blocks, listing_from_jsonld

logger = logging.getLogger("nyc_apartment_search")

MAX_DETAIL_PAGES = 20


class DouglasEllimanAdapter(BaseAdapter):
    name = "douglas_elliman"
    base_url = "https://www.elliman.com"

    def _search_urls(self) -> list[str]:
        location = self.config.get("location", {})
        slugs = []
        for raw in (location.get("neighborhood"), location.get("borough")):
            if raw:
                slug = re.sub(r"[^a-z0-9]+", "-", raw.strip().lower()).strip("-")
                if slug:
                    slugs.append(slug)
        if not slugs:
            return [f"{self.base_url}/rentals/new-york-ny"]
        return [f"{self.base_url}/rentals/{slug}-new-york-ny" for slug in slugs]

    def _card_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls = []
        for a in soup.find_all("a", attrs={"data-test-id": re.compile(r"^listings-card-\d+$")}):
            href = a.get("href")
            if href:
                urls.append(href if href.startswith("http") else self.base_url + href)
        return urls

    def fetch(self) -> SourceResult:
        search_urls = self._search_urls()
        candidate_urls: list[str] = []
        search_errors = 0
        for search_url in search_urls:
            try:
                html = self.get(search_url)
            except BlockedError as exc:
                search_errors += 1
                logger.info("%s: skipping search page %s (%s)", self.name, search_url, exc)
                continue
            candidate_urls.extend(self._card_urls(html))

        if search_errors == len(search_urls):
            return self.blocked_result("every configured area search page failed to fetch")

        # de-dupe while preserving order
        seen: set[str] = set()
        detail_urls = []
        for url in candidate_urls:
            if url not in seen:
                seen.add(url)
                detail_urls.append(url)

        if not detail_urls:
            return SourceResult(
                name=self.name,
                status=SourceStatus.OK,
                listings=[],
                note="search pages reachable but no listing cards found for the configured area",
            )

        neighborhood_hint = self.config.get("location", {}).get("neighborhood")

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
                blocks = find_residence_blocks(extract_jsonld_blocks(html))
                for block in blocks:
                    listing = listing_from_jsonld(block, self.name, url, user_agent_neighborhood_hint=neighborhood_hint)
                    if listing:
                        listings.append(listing)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning("%s: parse failure on %s: %s (cached at %s)", self.name, url, exc, self._cache_path(url))
                continue

        status = SourceStatus.OK if errors == 0 else SourceStatus.PARTIAL
        note = None if errors == 0 else f"{errors} of {len(detail_urls[:MAX_DETAIL_PAGES])} candidate detail pages failed"
        return SourceResult(name=self.name, status=status, listings=listings, note=note)
