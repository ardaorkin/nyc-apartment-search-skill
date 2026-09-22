---
name: nyc-apartment-search
description: Search and re-check public NYC rental listings for an Upper East Side apartment (E 60th–E 90th, 2 adults + 1 cat), maintaining a deduplicated, ranked, change-tracked shortlist. Scaffolds and operates a local Python tool that writes CSV, JSON, a Markdown shortlist, and a change report. Use when asked to "search for apartments", "check for new listings", "run the apartment search", "any price drops", "add a source", "set my max rent", or to draft inquiry messages for a listing. Never applies, contacts brokers, or sends anything.
user-invocable: true
---

# NYC Upper East Side Apartment Search

Operate a local, reusable apartment-search tool: crawl public rental listings, normalize and
deduplicate them, validate geography, rank them, and report what changed since the last run.

Project root: `~/nyc-apartment-search/` (override if the user names a different path).

**Expect most major aggregators (StreetEasy, RentHop, Apartments.com, Realtor.com) to come back
`BLOCKED_OR_MANUAL_REVIEW_REQUIRED`** — their robots.txt/ToS forbid it, and this skill's hard rule
below means it won't route around that. Zillow allows only its rental search-index pages, not
individual listings. Real coverage comes from brokerage and property-management sites, most of
which are open — see `references/sources.md` for the current, periodically re-checked status of
each platform. This is expected, correct behavior, not a broken source.

## Hard rules — never violate

- **Read-only toward the outside world.** Never submit an application, contact a broker, send a
  message or email, make a payment, or upload personal documents. Inquiry messages are *drafted
  for the user to send by hand* — never sent.
- **Public pages only.** Respect robots.txt and site terms, rate-limit, cache, and prefer
  APIs / JSON-LD / structured data / sitemaps over HTML scraping and browser automation.
- **Never defeat access controls** — no CAPTCHA solving, no auth bypass, no anti-bot evasion, no
  proxy rotation, no account-only content. A blocked source is recorded as
  `BLOCKED_OR_MANUAL_REVIEW_REQUIRED` and the run continues.
- **Never fabricate a field.** Unknown is `null` plus a note in `confidence_notes`. A Zestimate,
  rent estimate, historical price, or cached search snippet is never the current asking rent.
- Personal details stay local. Don't commit `config.yaml`, `data/`, or `cache/`, and don't publish
  reports anywhere outside this machine.

## Step 1 — Scaffold if the project doesn't exist

Check for `~/nyc-apartment-search/`. If absent, create it:

```
nyc-apartment-search/
  config.yaml          # copy from this skill's assets/config.yaml, then fill in identity
  search.py            # CLI entry point
  sources/             # one adapter per site
  parsers/             # extraction + normalization helpers
  data/                # snapshots (one per run) + canonical listing store
  reports/             # listings.csv, listings.json, shortlist.md, changes.md
  cache/               # raw fetched responses, keyed by URL + date
  tests/
  README.md            # how to run, how to add a source, how to schedule
  .gitignore           # config.yaml, data/, cache/, reports/
```

Python, stdlib-first plus `httpx`, `beautifulsoup4`, `lxml`, `pydantic`, `pandas`, `rapidfuzz`,
`tenacity`, `rich`; `playwright` only where a public page genuinely requires it.

Build in this order, and get each piece working before the next:

1. Shared `Listing` model (`references/data-model.md`) with strict `null` handling.
2. Address normalization + geographic filter (Step 3).
3. Deduplication (Step 4).
4. Source adapters, easiest reputable source first (`references/sources.md`).
5. Ranking, reports, change tracking.

Every parser: robust selectors, graceful degradation on layout changes, logged parse failures,
raw response retained in `cache/`. **One failing source never aborts the run.**

Unit tests are required for address normalization, street-range filtering, pet-policy
classification, deduplication, and rent parsing.

## Step 2 — Run

```bash
cd ~/nyc-apartment-search && python search.py
```

Useful flags to support: `--sources a,b`, `--no-cache`, `--max-rent N`, `--dry-run`.

## Step 3 — Filter: geography and pets

**Geography (hard).** Accept only Upper East Side / Lenox Hill / Yorkville addresses east of
Central Park between **E 60th and E 90th**. Numbered cross streets: parse the street number
directly. Avenue addresses: infer cross streets from listing text, map metadata, geocoding, or
named intersections. Can't confirm? Keep it and flag `GEOGRAPHY_NEEDS_CONFIRMATION`. Clearly
outside the range → rejected, with the reason recorded.

**Pets (2 adults, 1 cat).** Accept when cats are allowed, pets are allowed, or pets are
case-by-case with no cat prohibition. Reject only an explicit cat/all-pet ban. Unknown → keep and
flag `PET POLICY NEEDS CONFIRMATION`. Extract pet deposit, pet fee, monthly pet rent, approval
requirements, and any other restriction.

**Budget.** `max_rent` is `null` until the user gives one — collect everything otherwise suitable
and make rent a prominent, sortable field. When the user supplies a budget, write it to
`config.yaml` and apply it as a hard filter from then on.

## Step 4 — Deduplicate, then classify

Dedupe primarily on normalized street address + unit; break ties with bedroom count, rent,
brokerage, listing IDs, and photo/description similarity. Keep **every** source URL on the
canonical record. When prices disagree across sources, show all observed prices and mark the
most recently updated one.

Classify freshness as `ACTIVE`, `LIKELY_ACTIVE`, `UNCERTAIN`, `STALE`, or `OFF_MARKET` from
availability language, updated timestamps, visible contact/application controls, listing history,
and removal status. Never silently discard a stale listing — classify it.

Also assign a scam/risk level (`LOW_RISK` / `REVIEW` / `HIGH_RISK`) with a one-line reason, and
flag `APPLICATION_REQUIREMENTS_NEED_CONFIRMATION` where an international transferee may hit
credit-history, SSN, guarantor, or income-multiple requirements. Never call something a scam
without evidence; never assume the user lacks a document. Details in
`references/scoring-and-output.md`.

## Step 5 — Rank and report

Score active / likely-active listings 0–100 using the rubric in
`references/scoring-and-output.md`, always with the top reasons for the score.

Every run writes `reports/listings.csv`, `reports/listings.json`, `reports/shortlist.md`, and
`reports/changes.md` (diffed against the previous snapshot: `NEW`, `PRICE_DROP`, `PRICE_INCREASE`,
`REMOVED`, `BACK_ON_MARKET`, `DETAIL_CHANGED`, each with previous and current values), then prints
a terminal summary: sources searched, raw listings, count after geographic filtering, after pet
filtering, after dedupe, active/likely-active, and the top 10.

Report to the user in chat: the top matches, what changed since last run, and — explicitly — which
sources could not be accessed automatically.

## Step 6 — Questions and draft messages (on request or for top-tier listings)

Generate only questions whose answers aren't already known (availability, cats and pet fees,
broker fee, total upfront cost, lease terms, application requirements, gross vs. net-effective
rent, rent stabilization, mandatory building/amenity fees).

Draft short, friendly, professional WhatsApp/SMS-style inquiries using the `identity.intro` line
from `config.yaml`. Mention the cat only when the pet policy needs confirming or the listing asks.
Never invent salary, credit score, savings, SSN, guarantor, rental history, lease length, or an
exact move-in date, and leave immigration details out entirely. **Show the draft; never send it.**

## Scheduling

Manual by default. On request only, provide (don't install) a `cron` or `launchd` entry —
every 3–6 hours is sensible during an active search, and the cadence stays configurable.

## References

- `references/data-model.md` — required listing fields and status enums
- `references/sources.md` — source list, discovery procedure, access rules
- `references/scoring-and-output.md` — ranking rubric, risk checks, report formats
- `assets/config.yaml` — starter configuration
