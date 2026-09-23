# nyc-apartment-search

A [Claude Code](https://claude.com/claude-code) skill that searches and re-checks public NYC rental
listings, maintaining a deduplicated, ranked, change-tracked shortlist over time.

**Citywide by default.** It searches all five boroughs until you tell it otherwise — say "just the
Upper East Side" or "Brooklyn only" or "between E 60th and E 90th" and it narrows from there and
remembers it. Household and preferences are config-driven too — see `assets/config.yaml`.
(Originally built for one person's Upper East Side 2-bedroom search, which is why the starter
brokerage/property-manager source list in `references/sources.md` still leans Manhattan-heavy —
add borough-appropriate sources once you narrow the area.)

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
- On explicit, per-conversation opt-in only: installs a recurring schedule and/or sends a Slack
  digest to your own account after each run. Off by default — see "Scheduling and notifications"
  below.

## Hard rules

- **Read-only toward anyone but you.** Never applies, contacts brokers, sends messages to a
  listing contact, makes payments, or uploads documents. Any inquiry message is drafted for you to
  send by hand.
- **Public pages only.** No CAPTCHA solving, no auth bypass, no anti-bot evasion, no proxy
  rotation, no account-only content. Blocked sources are reported, not silently skipped.
- **Never fabricates a field.** Unknown data is `null` plus a note — never a guess, and never a
  Zestimate or cached snippet standing in for the current asking rent.
- **Personal details stay local.** `config.yaml`, `data/`, `cache/`, and `reports/` are git-ignored
  by the scaffolded project and never published anywhere.
- **Scheduling and Slack notifications are opt-in, every time.** A past yes doesn't carry forward
  to a new conversation.

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

## Scheduling and notifications (opt-in, off by default)

Manual by default — nothing runs unless you run it. If you ask for a recurring schedule and/or a
Slack digest after each run, the skill asks for explicit confirmation *in that conversation*
before installing or sending anything, shows you exactly what it's about to install/send, and
gives you the exact command to undo it in the same message. Neither carries over silently to a
future conversation — you're asked again each time.

Details: `references/scheduling.md` (cron/launchd install + uninstall) and
`references/slack-notifications.md` (Slack digest format + limits — self-DM only, one message per
run, never a channel).

## Tests

- **Deterministic** (`tests/test_deterministic.py`): pure-function unit tests for address
  normalization, geo filtering, pet-policy classification, dedup keys, and rent parsing — no
  network, no LLM. Run with `pip install pytest && pytest tests/test_deterministic.py`.
- **Agentic** (`tests/agentic/`): scenario-based checks that Claude actually follows the skill's
  hard rules — respects a robots.txt block instead of routing around it, never fabricates an
  unknown field, never sends a drafted message, never leaks immigration status, and asks before
  installing a schedule or sending a Slack message. Requires the `claude` CLI; run with
  `python3 tests/agentic/run_evals.py`. Unlike the deterministic suite, these can flake on LLM
  phrasing variance — re-run a lone failure before treating it as a real regression.

## Structure

```
SKILL.md                            # the skill definition Claude Code reads
assets/config.yaml                   # starter config — copy and fill in your own details
references/data-model.md             # required listing fields and status enums
references/sources.md                # source list, discovery procedure, access rules
references/scoring-and-output.md     # ranking rubric, risk checks, report formats
references/scheduling.md             # cron/launchd setup and teardown (opt-in)
references/slack-notifications.md    # Slack digest setup and teardown (opt-in)
lib/nyc_apartment_search/            # reference implementation of the pure-logic pieces
tests/test_deterministic.py          # deterministic unit tests
tests/agentic/                       # agentic guardrail eval scenarios + runner
```

## License

MIT — see [LICENSE](LICENSE).
