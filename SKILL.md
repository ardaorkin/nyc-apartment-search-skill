---
name: nyc-apartment-search
version: 2.4.0
description: (v2.4.0) Search and re-check public New York City rental listings using a real, ready-to-use codebase this skill deploys (not generates from scratch) — NYC is the one fixed, non-configurable setting; everything else (area within the city, household, bedrooms, budget, move timing, preferences) starts with no default and is asked on first run, written to config.yaml, and mutable anytime after. Maintains a deduplicated, ranked, change-tracked shortlist. Writes CSV, JSON, a Markdown shortlist, and a change report. Can optionally, only on explicit opt-in, install a recurring schedule and send Slack digests to the user. Use when asked to "search for apartments", "check for new listings", "run the apartment search", "any price drops", "add a source", "set my max rent", "search in <neighborhood/borough>", "schedule the search", "notify me on Slack", or to draft inquiry messages for a listing. Never contacts brokers or applies on the user's behalf.
user-invocable: true
---

# NYC Apartment Search

Operate a local, reusable apartment-search tool: crawl public rental listings, normalize and
deduplicate them, validate geography, rank them, and report what changed since the last run.

New York City is fixed — this skill doesn't search anywhere else, and that's not a setting.
Every other search criterion (area within NYC, household, bedrooms, budget, move timing,
preferences) starts unset and is asked about during first-time setup (Step 1) — see
[FIRST-TIME-SETUP.md](FIRST-TIME-SETUP.md). All of it is mutable afterward; nothing here is a
one-time choice.

Project root: `~/nyc-apartment-search/` (override if the user names a different path).

**Expect most major aggregators (StreetEasy, RentHop, Apartments.com, Realtor.com) to come back
`BLOCKED_OR_MANUAL_REVIEW_REQUIRED`** — their robots.txt/ToS forbid it, and this skill's hard rule
below means it won't route around that. Zillow allows only its rental search-index pages, not
individual listings. Real coverage comes from brokerage and property-management sites, most of
which are open — see `references/sources.md` for the current, periodically re-checked status of
each platform. This is expected, correct behavior, not a broken source.

## Hard rules — never violate

- **Read-only toward anyone but the user.** Never submit an application, contact a broker, send a
  message or email to a listing contact, make a payment, or upload personal documents. Inquiry
  messages to brokers/landlords are *drafted for the user to send by hand* — never sent. This does
  not cover notifying the user themselves — see Step 7.
- **Public pages only.** Respect robots.txt and site terms, rate-limit, cache, and prefer
  APIs / JSON-LD / structured data / sitemaps over HTML scraping and browser automation.
- **Never defeat access controls** — no CAPTCHA solving, no auth bypass, no anti-bot evasion, no
  proxy rotation, no account-only content. A blocked source is recorded as
  `BLOCKED_OR_MANUAL_REVIEW_REQUIRED` and the run continues.
- **Never fabricate a field.** Unknown is `null` plus a note in `confidence_notes`. A Zestimate,
  rent estimate, historical price, or cached search snippet is never the current asking rent.
- Personal details stay local. Don't commit `config.yaml`, `data/`, or `cache/` to git, and don't
  publish reports publicly. A Slack digest sent to the user's own account (Step 7) is not
  "publishing" — it's still just the user, on a channel they explicitly opted into.
- **Scheduling and Slack notifications are opt-in, every time.** Never install a cron/launchd job
  or send a Slack message unless the user explicitly says yes *in this conversation* — a past yes
  doesn't carry forward, and neither does inferring consent from context. See Step 7.
- **New York City is fixed, not configurable.** Every other criterion is asked about and can be
  changed; the city cannot. A request to search a different city is a different tool, not a
  setting to change on this one — say so rather than trying to accommodate it.

## Step 0 — First-run intro

If this is the first invocation of this skill in the current session, read
[INTRO.md](INTRO.md) and output its fenced code block **verbatim, including the triple-backtick
markers** — don't strip the fence, and don't swap in fancier art than what's actually there (see
INTRO.md for why: dense special-character art has repeatedly failed to reproduce correctly in
practice). Then continue below. Skip on subsequent invocations within the same session.

## Step 1 — Deploy the ready-made codebase if the project doesn't exist

Check for `~/nyc-apartment-search/`. If absent, create it by **copying this skill's `app/`
directory verbatim** — `models.py`, `search.py`, `reports.py`, `requirements.txt`, `parsers/`,
`sources/`, `tests/`, `.gitignore`, `README.md`. Don't write any of this from scratch: it's a
real, working, tested implementation, built and debugged against the actual sites (robots.txt/ToS
compliance already applied, actual JSON-LD/API shapes handled, per-source access status recorded
in `references/sources.md`). Regenerating it from the spec below would be strictly worse — slower,
untested, and prone to reintroducing bugs the real thing has already had fixed.

```
nyc-apartment-search/
  config.yaml          # created via FIRST-TIME-SETUP.md on first run -- not part of app/
  <everything else copied verbatim from this skill's app/ directory>
```

Then `cd ~/nyc-apartment-search && python3 -m venv .venv && source .venv/bin/activate && pip
install -r requirements.txt`.

Check for `~/nyc-apartment-search/config.yaml`. If missing, read
[FIRST-TIME-SETUP.md](FIRST-TIME-SETUP.md) and follow it to create it by asking the user — don't
silently write defaults. If present, use it as-is.

`app/README.md` documents the codebase; read it before touching any copied file. Only edit the
copied code if something's actually broken or you're adding a new source/capability — and if you
do, the one rule that matters most: **never hardcode an area** (neighborhood, borough, specific
URL) into an adapter. Derive it from `config.yaml`'s `location` block at fetch time instead (see
`sources/common.py`'s `area_keywords_from_config`, or `sources/douglas_elliman.py` /
`sources/related_rentals.py` for adapters that build their own request URLs from it) — a
hardcoded area silently breaks results for every user whose configured area differs from whatever
it was built against, and that exact bug has already happened once. Run `pytest tests/` after any
change; extend the suite when you add a source or change parsing logic, don't just remove
coverage.

`references/data-model.md`, `references/sources.md`, and `references/scoring-and-output.md`
describe what the shipped code in `app/` already does — read them as the spec the implementation
follows (useful for debugging or extending it), not as instructions to build something new.

## Step 2 — Run

```bash
cd ~/nyc-apartment-search && python search.py
```

Useful flags to support: `--sources a,b`, `--no-cache`, `--max-rent N`, `--dry-run`.

## Step 3 — Filter: geography and pets

**Geography.** New York City is fixed (see Hard rules); the area within it is asked about during
first-time setup, not assumed. `config.yaml`'s `location` block (`borough`, `neighborhood`,
`min_street`, `max_street`) is `null` — citywide, no filter — unless the user named an area during
setup or since. Whenever the user names or changes an area ("just the Upper East Side", "Brooklyn
only", "between E 60th and E 90th", "actually widen it back to all boroughs"), update
`config.yaml`'s `location` block and apply it as a hard filter from then on, same as the budget
filter below — this is mutable at any time, not a one-time setup answer. Numbered cross streets:
parse the street number directly against the configured range. Avenue addresses within a
configured area: infer cross streets from listing text, map metadata, geocoding, or named
intersections. Can't confirm whether a listing falls inside a *configured* area? Keep it and flag
`GEOGRAPHY_NEEDS_CONFIRMATION`. Clearly outside a *configured* area → rejected, with the reason
recorded. With no area configured, every listing is `IN_RANGE` by definition — there's nothing to
reject on location grounds; still record borough/neighborhood for display and ranking.

Once an area is configured, `references/sources.md`'s brokerage/property-manager list may need
borough-specific additions — the current list leans Manhattan-heavy since that's what it was
originally built against. Check each newly relevant source's own robots.txt/ToS before adding it,
same as any other source.

**Pets.** `config.yaml`'s `household` block (`adults`, `cats`, `dogs`) is `null` until set during
first-time setup or since. With no pets configured, don't filter on pet policy at all — just
record it. Once pets are configured: accept when cats/dogs are allowed, pets are allowed, or pets
are case-by-case with no ban on the configured pet type. Reject only an explicit ban covering the
configured pet(s). Unknown → keep and flag `PET_POLICY_NEEDS_CONFIRMATION` (matches the
`pet_status` enum in `references/data-model.md` — use the underscored form consistently). Extract
pet deposit, pet fee, monthly pet rent, approval requirements, and any other restriction
regardless of whether pets are configured — useful information either way.

**Budget.** `max_rent` is `null` until the user gives one — collect everything otherwise suitable
and make rent a prominent, sortable field. When the user supplies a budget, write it to
`config.yaml` and apply it as a hard filter from then on.

**Minimum bedrooms.** `minimum_bedrooms` is a floor, not a preference — reject anything with a
known bedroom count below it. `preferred_bedrooms` is ranking-only (`references/scoring-and-output.md`);
don't confuse the two. Unknown bedroom count is never rejected on either.

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
a terminal summary: sources searched, raw listings, and the cumulative survivor count after each
filter stage in order (geographic, pet, required-preference, budget, minimum-bedroom), then after
dedupe, active/likely-active, and the top 10.

Report to the user in chat: the top matches, what changed since last run, and — explicitly — which
sources could not be accessed automatically.

## Step 6 — Questions and draft messages (on request or for top-tier listings)

Generate only questions whose answers aren't already known (availability, cats and pet fees,
broker fee, total upfront cost, lease terms, application requirements, gross vs. net-effective
rent, rent stabilization, mandatory building/amenity fees).

Draft short, friendly, professional WhatsApp/SMS-style inquiries using the `identity.intro` line
from `config.yaml`. If `identity.intro` is `null`, ask for one before drafting rather than
inventing an intro. Mention pets only when the pet policy needs confirming, the listing asks, or
pets are configured in `household`. Never invent salary, credit score, savings, SSN, guarantor,
rental history, lease length, or an exact move-in date, and leave immigration details out
entirely. **Show the draft; never send it.**

## Step 7 — Scheduling and Slack notifications (ask first, every time)

Both are opt-in. Never set either up because a run went well, because the user set it up before,
or because it seems convenient — always ask, in this conversation, before touching either.

**Scheduling.** After a successful manual run, ask: *"Want this running on a recurring schedule
instead of manually?"* If no (or no answer), stop — manual (`python search.py`) stays the only way
it runs. If yes, read `references/scheduling.md` and follow it exactly. Unlike before, this now
means actually installing the job, not just handing over text — but show the user the exact
plist/crontab content and the exact uninstall command *before* installing it, in the same message.

**Slack notifications.** Ask separately: *"Want a Slack message after each run with what
changed?"* — a yes to scheduling is not a yes to this. If no, reports stay local files only. If
yes, read `references/slack-notifications.md` and follow it exactly.

Both reference files include how to undo what they set up. Mention that explicitly when you set
either one up, not just when asked — the easiest way to end up with a forgotten background job is
to bury the uninstall step somewhere the user has to go looking for it.

## References

- `app/` — the ready-to-use codebase; copy verbatim in Step 1 (see `app/README.md`)
- `CHANGELOG.md` — version history
- `INTRO.md` — first-run banner (Step 0)
- `FIRST-TIME-SETUP.md` — config creation wizard (read only when `config.yaml` is missing)
- `references/data-model.md` — required listing fields and status enums
- `references/sources.md` — source list, discovery procedure, access rules
- `references/scoring-and-output.md` — ranking rubric, risk checks, report formats
- `references/scheduling.md` — cron/launchd setup and teardown (read only after the user opts in)
- `references/slack-notifications.md` — Slack digest setup and teardown (read only after the user opts in)
- `assets/config.yaml` — starter configuration

## Versioning

`version:` in this file's frontmatter, the `(vX.Y.Z)` prefix on `description` above, and the
version line in `INTRO.md` must always match. Bump on every change to this skill (patch for
fixes/wording, minor for a new non-breaking capability, major for a breaking behavior change) and
add a `CHANGELOG.md` entry in the same change — never edit the skill without doing both.
