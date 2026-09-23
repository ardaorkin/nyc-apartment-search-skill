"""Generic sitemap + JSON-LD adapter shared by the confirmed-open brokerage/property
manager sources. A layout change degrades fields (via listing_from_jsonld's None-safe
extraction) rather than killing the source; any hard failure is caught and turned into
BLOCKED_OR_MANUAL_REVIEW_REQUIRED or ERROR by fetch()."""
from __future__ import annotations

import logging

from models import Listing, SourceResult, SourceStatus
from sources.base import BaseAdapter, BlockedError
from sources.common import (
    area_keywords_from_config,
    extract_jsonld_blocks,
    filter_urls_by_area,
    find_residence_blocks,
    listing_from_jsonld,
    looks_like_rental_url,
    parse_sitemap_urls,
)

logger = logging.getLogger("nyc_apartment_search")

MAX_LISTING_PAGES = 15


class SitemapAdapter(BaseAdapter):
    """Configure sitemap_index_url (or sitemap_urls, plural). Area narrowing is derived
    from config.yaml's location block at fetch time (area_keywords_from_config) --
    never hardcode a specific neighborhood/borough in a subclass; that would silently
    keep searching the wrong area for every user who configures a different one.
    require_area_match is a per-adapter behavior choice, not area-specific: whether an
    unmatched area falls back to the full sitemap (False) or to nothing (True)."""

    sitemap_index_url: str | None = None
    sitemap_urls: list[str] = []
    require_area_match: bool = True

    def _collect_sitemap_urls(self) -> list[str]:
        top_level = list(self.sitemap_urls)
        if self.sitemap_index_url:
            top_level.append(self.sitemap_index_url)

        listing_urls: list[str] = []
        for sm_url in top_level:
            xml = self.get(sm_url)
            entries = parse_sitemap_urls(xml)
            # If these entries are themselves sitemaps (sitemap index), recurse one level.
            sub_sitemaps = [u for u in entries if u.lower().endswith(".xml")]
            rental_sub = [u for u in sub_sitemaps if looks_like_rental_url(u)]
            if sub_sitemaps and not any(looks_like_rental_url(u) is False and u == e for u, e in zip(entries, entries)):
                targets = rental_sub or sub_sitemaps[:3]
                for sub in targets:
                    try:
                        sub_xml = self.get(sub)
                    except BlockedError:
                        continue
                    listing_urls.extend(parse_sitemap_urls(sub_xml))
            else:
                listing_urls.extend(entries)

        rental_urls = [u for u in listing_urls if looks_like_rental_url(u)] or listing_urls
        return rental_urls

    def fetch(self) -> SourceResult:
        try:
            candidate_urls = self._collect_sitemap_urls()
        except BlockedError as exc:
            return self.blocked_result(str(exc))
        except Exception as exc:  # noqa: BLE001 -- adapter must never raise to caller
            return self.error_result(f"unexpected error collecting sitemap: {exc}")

        if not candidate_urls:
            return self.blocked_result("no rental URLs found in sitemap")

        keywords = area_keywords_from_config(self.config.get("location", {}))
        area_urls = filter_urls_by_area(candidate_urls, keywords) if keywords else []
        target_urls = area_urls if area_urls else (candidate_urls if not self.require_area_match else [])

        if not target_urls:
            return SourceResult(
                name=self.name,
                status=SourceStatus.OK,
                listings=[],
                note="sitemap reachable but no listing URLs matched the configured area",
            )

        listings: list[Listing] = []
        errors = 0
        for url in target_urls[:MAX_LISTING_PAGES]:
            try:
                html = self.get(url)
            except BlockedError as exc:
                errors += 1
                logger.info("%s: skipping %s (%s)", self.name, url, exc)
                continue
            try:
                blocks = find_residence_blocks(extract_jsonld_blocks(html))
                for block in blocks:
                    listing = listing_from_jsonld(block, self.name, url)
                    if listing:
                        listings.append(listing)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning("%s: parse failure on %s: %s (cached at %s)", self.name, url, exc, self._cache_path(url))
                continue

        if not listings and errors == len(target_urls[:MAX_LISTING_PAGES]):
            return self.blocked_result("every candidate listing page failed to fetch or parse")

        status = SourceStatus.OK if errors == 0 else SourceStatus.PARTIAL
        note = None if errors == 0 else f"{errors} of {len(target_urls[:MAX_LISTING_PAGES])} candidate pages failed"
        return SourceResult(name=self.name, status=status, listings=listings, note=note)
