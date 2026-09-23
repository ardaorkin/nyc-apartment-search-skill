# nyc-apartment-search

**Version 2.6.0** — see [CHANGELOG.md](CHANGELOG.md).

A [Claude Code](https://claude.com/claude-code) skill that searches and re-checks public NYC rental
listings, maintaining a deduplicated, ranked, change-tracked shortlist over time.

**New York City is the only fixed setting.** Everything else — area within the city, household,
bedrooms, budget, move timing, preferences — starts unset and is asked about on first run (see
`FIRST-TIME-SETUP.md`), written to `config.yaml`, and mutable anytime after: say "just the Upper
East Side," "Brooklyn only," "between E 60th and E 90th," "actually widen it back to all
boroughs," "set my max rent to $4,000" — whatever, whenever. Skipping a question at setup just
means "no preference," not a guess.

(Originally built for one person's Upper East Side 2-bedroom search, which is why the starter
brokerage/property-manager source list in `references/sources.md` still leans Manhattan-heavy —
add borough-appropriate sources once you narrow the area.)

## What it does

- Deploys a ready-to-use, tested Python tool (from `app/`, copied verbatim — not generated from
  scratch) to `~/nyc-apartment-search/` on first run. See `app/README.md`.
- Crawls public rental listings — public pages only, respecting robots.txt and site terms, never
  bypassing access controls. Real coverage comes from **brokerages and property managers**: as of
  2026-09-23, 7 of 14 are confirmed open (Corcoran, Douglas Elliman, Glenwood, Rose Associates,
  Manhattan Skyline, Related Rentals, PREX), 1 is unresolved pending re-verification (Compass), 1
  is ambiguous pending a URL-structure check (Rudin Management), and 4 are blocked or inconclusive
  (BOND New York, Sotheby's, Brown Harris Stevens, Equity Residential — see
  `references/sources.md` for why the last two might be temporary, not permanent). The big
  aggregators (StreetEasy, RentHop, Apartments.com, Realtor.com) forbid scraping in their
  robots.txt/ToS and will correctly come back
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
- **New York City is fixed, not configurable.** Every other criterion is asked about and can be
  changed; the city cannot.

## Install

Copy this directory into your Claude Code skills folder:

```bash
git clone https://github.com/ardaorkin/nyc-apartment-search-skill.git ~/.claude/skills/nyc-apartment-search
```

Then, in Claude Code, just ask it to search for apartments — the skill copies the ready-made
`app/` codebase to `~/nyc-apartment-search/` on first use and walks you through setting your
neighborhood, budget, and preferences (written to `config.yaml`, not part of the repo).

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

- **App** (`app/tests/`): pytest suite for the real, shipped implementation — address
  normalization, geo filtering (including the citywide-default and configured-area cases),
  dedup, pet-policy, rent parsing, and adapter failure resilience. Run with
  `pip install -r app/requirements.txt pytest && cd app && pytest tests/`.
- **Agentic** (`tests/agentic/`): scenario-based checks that Claude actually follows the skill's
  hard rules — respects a robots.txt block instead of routing around it, never fabricates an
  unknown field, never sends a drafted message, never leaks immigration status, and asks before
  installing a schedule or sending a Slack message. Requires the `claude` CLI; run with
  `python3 tests/agentic/run_evals.py`. Unlike the deterministic suite, these can flake on LLM
  phrasing variance — re-run a lone failure before treating it as a real regression.

## Structure

```
SKILL.md                            # the skill definition Claude Code reads
INTRO.md                             # first-run banner
FIRST-TIME-SETUP.md                  # config creation wizard (read when config.yaml is missing)
assets/config.yaml                   # starter config — everything but `city` starts null
references/data-model.md             # spec: required listing fields and status enums
references/sources.md                # spec: source list, discovery procedure, access rules
references/scoring-and-output.md     # spec: ranking rubric, risk checks, report formats
references/scheduling.md             # cron/launchd setup and teardown (opt-in)
references/slack-notifications.md    # Slack digest setup and teardown (opt-in)
app/                                 # the ready-to-use codebase -- copied verbatim, see app/README.md
  models.py, search.py, reports.py, requirements.txt
  parsers/                           # address, dedupe, pets, rent, freshness, risk, scoring
  sources/                           # one adapter per site
  tests/                             # pytest suite for the above
tests/agentic/                       # agentic guardrail eval scenarios + runner
```

## License

MIT — see [LICENSE](LICENSE).
