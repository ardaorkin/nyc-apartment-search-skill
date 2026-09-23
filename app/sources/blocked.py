"""Sources recorded as BLOCKED_OR_MANUAL_REVIEW_REQUIRED (or ambiguous/inconclusive) per
references/sources.md, without attempting live access -- their robots.txt/ToS/edge
protection already rules them out, and the hard rules forbid trying to route around
that (no proxy rotation, no headless-browser evasion, no alternate hostnames)."""
from __future__ import annotations

from models import SourceResult, SourceStatus

KNOWN_BLOCKED = {
    "streeteasy": "robots.txt disallows /rental/*",
    "renthop": "Cloudflare WAF challenge blocks even fetching robots.txt",
    "apartments_com": "Edge/WAF returns Access Denied on robots.txt itself",
    "realtor_com": "robots.txt legal notice: scraping unauthorized without written permission",
    "bond_new_york": "Cloudflare WAF challenge blocks even fetching robots.txt, same pattern as RentHop",
    "sothebys_nyc": "Returns empty HTTP 202 on every attempt -- likely edge/bot-protected, needs a manual browser check",
    "rudin_management": "robots.txt Disallow: /node/* -- ambiguous whether it covers listing pages, needs manual confirmation against real listing URLs before crawling",
    "ues_management": "No identifiable real site found under a reasonable domain guess -- likely a placeholder name, needs manual research or should be dropped from config.yaml",
}

KNOWN_PARTIAL = {
    "zillow": "robots.txt allows only the rental search-index pages, not individual listing detail pages -- index-only, not usable for full listing extraction",
}


def blocked_results() -> list[SourceResult]:
    results = [
        SourceResult(name=name, status=SourceStatus.BLOCKED_OR_MANUAL_REVIEW_REQUIRED, listings=[], note=note)
        for name, note in KNOWN_BLOCKED.items()
    ]
    results.extend(
        SourceResult(name=name, status=SourceStatus.PARTIAL, listings=[], note=note)
        for name, note in KNOWN_PARTIAL.items()
    )
    return results
