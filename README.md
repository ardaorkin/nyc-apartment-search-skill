# nyc-apartment-search

A [Claude Code](https://claude.com/claude-code) skill that searches and re-checks public NYC rental
listings, maintaining a deduplicated, ranked, change-tracked shortlist over time.

Originally built for an Upper East Side 2-bedroom search (2 adults + 1 cat), but the geography,
household, and preferences are all config-driven — adapt `assets/config.yaml` to any NYC
neighborhood or household shape.

## What it does

- Scaffolds a local Python tool under `~/nyc-apartment-search/` on first run.
- Crawls public rental listings — public pages only, respecting robots.txt and site terms, never
  bypassing access controls. Real coverage comes from **brokerages and property managers**: of the
  14 checked, 10 are confirmed open (Compass, Corcoran, Douglas Elliman, Brown Harris Stevens,
  Glenwood, Rose Associates, Equity Residential, Manhattan Skyline, Related Rentals, PREX), 1 is
  ambiguous pending a URL-structure check (Rudin Management), and 2 are blocked or inconclusive
  (BOND New York, Sotheby's). The big aggregators (StreetEasy, RentHop, Apartments.com,
  Realtor.com) forbid scraping in their robots.txt/ToS and will correctly come back
  `BLOCKED_OR_MANUAL_REVIEW_REQUIRED`; Zillow allows only its search-index pages, not individual
  listings. See `references/sources.md` for the full per-source status — blocked sources are the
  skill correctly respecting ToS, not a bug to route around.
- Normalizes, deduplicates, and geographically filters listings.
- Classifies pet policy, freshness (`ACTIVE` / `STALE` / `OFF_MARKET` / etc.), and scam risk.
- Ranks active listings 0–100 against a configurable rubric.
- Writes `reports/listings.csv`, `listings.json`, `shortlist.md`, and a `changes.md` diff
  (`NEW`, `PRICE_DROP`, `PRICE_INCREASE`, `REMOVED`, `BACK_ON_MARKET`, ...) against the previous run.
- On request, drafts (never sends) short inquiry messages to listing contacts.

## Hard rules

- **Read-only toward the outside world.** Never applies, contacts brokers, sends messages, makes
  payments, or uploads documents. Any inquiry message is drafted for you to send by hand.
- **Public pages only.** No CAPTCHA solving, no auth bypass, no anti-bot evasion, no proxy
  rotation, no account-only content. Blocked sources are reported, not silently skipped.
- **Never fabricates a field.** Unknown data is `null` plus a note — never a guess, and never a
  Zestimate or cached snippet standing in for the current asking rent.
- **Personal details stay local.** `config.yaml`, `data/`, `cache/`, and `reports/` are git-ignored
  by the scaffolded project and never published anywhere.

## Install

Copy this directory into your Claude Code skills folder:

```bash
git clone https://github.com/ardaorkin/nyc-apartment-search-skill.git ~/.claude/skills/nyc-apartment-search
```

Then, in Claude Code, just ask it to search for apartments — the skill scaffolds the local project
on first use and walks you through setting your neighborhood, budget, and preferences via
`assets/config.yaml`.

## Usage

Once installed, trigger phrases include:

- "search for apartments"
- "check for new listings"
- "run the apartment search"
- "any price drops?"
- "add a source"
- "set my max rent"
- "draft a message for this listing"

## Scheduling (optional)

Manual by default. On request, the skill can hand you a `cron` or `launchd` entry (every 3–6 hours
is a reasonable cadence during an active search) — it won't install one for you.

## Structure

```
SKILL.md                       # the skill definition Claude Code reads
assets/config.yaml              # starter config — copy and fill in your own details
references/data-model.md        # required listing fields and status enums
references/sources.md           # source list, discovery procedure, access rules
references/scoring-and-output.md  # ranking rubric, risk checks, report formats
```

## License

MIT — see [LICENSE](LICENSE).
