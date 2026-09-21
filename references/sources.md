# Sources and access rules

## Access rules (non-negotiable)

**Always:** public pages only; respect robots.txt and site terms; rate-limit
(`request_delay_seconds`, `max_concurrent_requests` from `config.yaml`); send a normal browser
user-agent; cache every fetch under `cache/` and reuse it; prefer official APIs, feeds, JSON-LD,
embedded structured data, and sitemaps over HTML scraping; use browser automation only when a
public page genuinely can't be read otherwise.

**Never:** solve or bypass CAPTCHAs; bypass authentication; evade bot protection; rotate proxies to
get around blocking; scrape account-only or private content; submit applications; contact brokers;
send messages; make payments; hand over personal documents.

When a site blocks automated access, record the source as `BLOCKED_OR_MANUAL_REVIEW_REQUIRED` with
the URL and what was attempted, then move on. Blocked sources get their own section in
`shortlist.md` so they can be checked by hand — they are a reported outcome, not a failure.

## Source list

Start with whichever sources are most accessible under the rules above, then widen.

**Major rental platforms** — StreetEasy, Zillow, Apartments.com, Realtor.com, RentHop

**Brokerages** — Compass, Corcoran, Douglas Elliman, BOND New York, Brown Harris Stevens,
Sotheby's and local NYC affiliates

**Property managers / owners** — Glenwood, Rose Associates, Rudin Management, Equity Residential,
Manhattan Skyline, Related Rentals, UES Management, PREX, plus other reputable Upper East Side
management companies discovered along the way

Publicly accessible individual broker and management-company inventory pages count too. Record any
newly discovered reputable source in `config.yaml` so later runs pick it up.

## Per-source discovery procedure

1. Locate the current rental-inventory page(s) covering the Upper East Side.
2. Apply the site's own filters for the neighborhood / E 60th–E 90th where possible.
3. Follow through to individual listing pages when the index lacks required fields.
4. Extract into the shared `Listing` model.
5. Record the source URL and the listing URL.
6. Record `checked_at`.
7. Classify `active_status` — never silently drop something that looks stale.

## Adapter contract

Each adapter in `sources/` exposes `fetch() -> list[Listing]` and:

- reads only from `cache/` when the cache is warm and `use_cache` is on;
- raises nothing to the caller — it logs, records a partial/failed status, and returns what it has;
- keeps selectors semantic and layered (structured data → semantic HTML → fallback selector), so a
  layout change degrades fields rather than killing the source;
- logs every parse failure with the cached response path for debugging.
