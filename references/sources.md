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

Start with whichever sources are most accessible under the rules above, then widen. In practice,
most real coverage comes from brokerages and property managers, not the major aggregators — see
below.

**Known access status of the major rental platforms** (checked 2026-09-22 against live
robots.txt/ToS — re-verify periodically, sites change these):

| Platform | Status | Basis |
| --- | --- | --- |
| StreetEasy | `BLOCKED_OR_MANUAL_REVIEW_REQUIRED` | robots.txt disallows `/rental/*` |
| RentHop | `BLOCKED_OR_MANUAL_REVIEW_REQUIRED` | Cloudflare WAF challenge blocks even fetching robots.txt |
| Apartments.com | `BLOCKED_OR_MANUAL_REVIEW_REQUIRED` | Edge/WAF returns Access Denied on robots.txt itself |
| Realtor.com | `BLOCKED_OR_MANUAL_REVIEW_REQUIRED` | robots.txt opens with an explicit legal notice that scraping is unauthorized without written permission |
| Zillow | Partial | robots.txt allows the rental search-index pages (`/homes/for_rent/$` and friends) and a for-rent sitemap, but disallows `/homes/` broadly otherwise — treat individual listing detail pages as not clearly allowed |

Don't try to route around any of these (no proxy rotation, no headless-browser evasion, no
alternate hostnames) — that would violate the hard rule above. Record each as
`BLOCKED_OR_MANUAL_REVIEW_REQUIRED` (or Zillow's index-only partial) and move on; this is the
correct, expected outcome for most runs, not a failure to fix.

**Brokerages** — Compass, Corcoran, Douglas Elliman, BOND New York, Brown Harris Stevens,
Sotheby's and local NYC affiliates. These are the primary real source of coverage: most publish
their own rental inventory on pages robots.txt leaves open.

**Property managers / owners** — Glenwood, Rose Associates, Rudin Management, Equity Residential,
Manhattan Skyline, Related Rentals, UES Management, PREX, plus other reputable Upper East Side
management companies discovered along the way. Same story — usually open, and often the freshest
listing data since it comes straight from the landlord.

Publicly accessible individual broker and management-company inventory pages count too. Record any
newly discovered reputable source in `config.yaml` so later runs pick it up. Check each new
source's own robots.txt/ToS before adding it — don't assume it's open because a peer site is.

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
