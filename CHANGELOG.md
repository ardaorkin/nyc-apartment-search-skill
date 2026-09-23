# Changelog

Semantic versioning: **patch** = bug fixes/wording, **minor** = new capability (non-breaking),
**major** = breaking behavior change. Bump the version in `SKILL.md`'s frontmatter `version:`
field and description, and in `INTRO.md`, with every change — add an entry here at the same time.

## 2.2.0 — 2026-09-23

Continued testing after v2.1.0, same loop:

- **Critical bug: `max_rent` was documented (SKILL.md, README, this file) as a hard filter but
  was never actually enforced as one.** `parsers/scoring.py`'s `_value_score` only gave an
  over-budget listing a low ranking score (4/20) -- it was never rejected. A user with a firm
  $3,000 budget could still see a $10,000 listing in their top 10 if it scored well on every
  other dimension. `apply_filters` (`search.py`) now rejects `monthly_rent > max_rent` when a
  budget is configured, same "never reject on unknown rent" philosophy as every other filter.
  Verified live against real listings with a strict budget.
- **Reporting bug this session's own earlier fixes had made worse:** the terminal summary's
  "After geographic filtering" / "After pet filtering" counts collapsed to just echoing
  `raw_count` once preference (v2.1.0) and budget (this release) filtering moved into the same
  combined per-listing pass -- `after_geo` was literally computed as `len(kept) + len(rejected)`,
  which is always the raw total regardless of what was actually rejected at that stage.
  `apply_filters` now returns real cumulative stage counts (geo/pets/preferences/budget); the
  summary and `SKILL.md`'s Step 5 spec both updated to match, verified live.

9 new/updated tests (56 total), including one asserting the exact stage-by-stage funnel counts
for a mix of listings each dropped at a different stage.

## 2.1.0 — 2026-09-23

Found via a real user's own run (Brooklyn, 3BR, $20k budget, wants a doorman) shortly after
v2.0.0 shipped -- not synthetic testing:

- **Critical bug: any search configured for a borough other than Manhattan returned zero
  results.** `search.py` hardcoded `listing_borough="Manhattan"` for any listing with a
  neighborhood set, regardless of the listing's actual borough -- so a Brooklyn-configured
  search silently rejected every real listing (all genuinely in Manhattan) as
  `OUT_OF_RANGE`. No adapter actually threads a real per-listing borough through today, so the
  honest fix is `listing_borough=None`: `classify_geo` already correctly flags an unknown
  borough as `GEOGRAPHY_NEEDS_CONFIRMATION` instead of silently rejecting it. Verified against
  the real Brooklyn config that originally produced zero results -- now returns real candidates
  flagged for confirmation instead of nothing.
- **Missing capability: `preferences.*: required` was documented as a hard filter but nothing
  enforced it, for any field.** New `parsers/preferences.py` (`required_preference_rejections`)
  wires this up for the five fields with an unambiguous mapping to an existing listing field:
  `in_unit_laundry`, `dishwasher`, `doorman`, `no_fee`, `rent_stabilized`. Never rejects on
  unknown/unconfirmed data, only on an explicit contradiction -- same philosophy as the geo/pet
  filters.
- **Missing field: `doorman` wasn't in the starter config's `preferences` block at all**, even
  though `parsers/scoring.py` already scored it -- a real user's doorman preference had nowhere
  to go and was silently dropped. Added to `assets/config.yaml`.
- **Known, documented gap (not fabricated):** `elevator_above_floor` is still not wired into
  filtering or scoring -- `listing.floor` is free text ("5", "PH", "Garden", ...) with no parser
  to compare it against a numeric threshold. Tracked honestly in `assets/config.yaml`'s comment
  and `FIRST-TIME-SETUP.md` rather than guessing at a comparison. Fix by adding a real floor
  parser before wiring it in.
- **Display bug: raw HTML markup leaked into listing addresses** (e.g. "West River House
  `<sup>®</sup>`") from a source's display-name field. `normalize_address` now strips HTML tags.
- **Display bug: a possessive apostrophe triggered incorrect capitalization** ("Claridge's" ->
  "Claridge'S", via `str.title()`'s "capitalize after any non-alpha character" behavior -- kept
  for `"4th"` -> `"4Th"`, wrong for an apostrophe). First fix only matched the ASCII apostrophe;
  the real source used the Unicode right single quote (U+2019), so the first attempt still
  failed live -- fixed to match both, verified against the live site both times.

17 new/updated tests (51 total): `test_preferences.py`, `test_search_filters.py`
(`apply_filters` integration coverage, not just the pure `classify_geo` unit), plus regression
tests for the borough, HTML-stripping, and apostrophe (both quote characters) bugs.

## 2.0.0 — 2026-09-23

**Breaking change to how this skill operates.** Previously, Step 1 told Claude to write the
entire codebase from scratch on every first run — slow, and prone to re-introducing bugs a
previous run had already found and fixed. This skill now ships a real, working, tested
implementation in `app/` (models, CLI, parsers, one adapter per source, reports, pytest suite)
that Step 1 copies verbatim instead of generating.

The shipped code came from a real debugging session that ran it against the actual sites. Before
shipping it, found and fixed a real bug in that session's adapters: `sources/common.py`, the
Compass/Corcoran/Brown Harris Stevens/Equity Residential adapters, and especially
`sources/douglas_elliman.py` (hardcoded to fetch exactly two neighborhood search pages) and
`sources/related_rentals.py` (hardcoded to a "nearest neighborhoods" heuristic) all hardcoded the
specific neighborhood that debugging session happened to be testing with. Shipped as-is, every
other user's search would have silently kept searching that neighborhood regardless of their own
`config.yaml`. Fixed by deriving area filtering from `config.yaml`'s `location` block at fetch
time everywhere (`sources/common.py`'s new `area_keywords_from_config`), verified against the
live sites both citywide (no area configured) and with a different configured neighborhood
(Chelsea) to confirm the fix generalizes rather than just moving the hardcoding somewhere else.

Also retired `lib/nyc_apartment_search/` and `tests/test_deterministic.py` (the earlier minimal
reference implementation used only to demonstrate the deterministic-test pattern before a real
app existed) — `app/tests/` now covers the same ground against the real implementation, more
thoroughly. `tests/agentic/` (guardrail evals) and all `references/*.md` (now documentation of
what `app/` actually does, not build instructions) are unchanged in role.

## 1.0.2 — 2026-09-23

- The 1.0.1 fix wasn't sufficient: the banner still came out mangled (whole lines missing, not
  just individual escaped characters), reported after another real run. The actual root cause
  is broader than markdown escaping — dense, special-character-heavy art isn't reliably
  reproduced by a model's text generation at all, code-fence or not; "output it verbatim" doesn't
  guarantee character-exact output. Replaced the figlet-style art with a plain bordered banner
  (`+`/`-`/`|` and plain text only) specifically because it has nothing dense enough to garble.

## 1.0.1 — 2026-09-22

- Fixed the intro banner getting silently corrupted outside a code fence: a markdown renderer
  treats the art's backslashes as escape characters and underscores as italics markers, eating
  exactly those characters. `SKILL.md` Step 0 and `INTRO.md` now say explicitly to output the
  fenced code block verbatim, including the triple-backtick markers, not just "print the art."

## 1.0.0 — 2026-09-22

First versioned release. Consolidates everything up to this point:

- Core search/dedupe/rank/report pipeline, geography and pet filtering, change tracking.
- Verified per-source access status: major aggregators (StreetEasy, RentHop, Apartments.com,
  Realtor.com) correctly blocked by their own ToS; Zillow partial; 10 of 14 brokerage/
  property-manager sources confirmed open.
- Deterministic unit tests (`tests/test_deterministic.py`) and agentic guardrail evals
  (`tests/agentic/`), with CI.
- Opt-in, ask-every-time scheduling (launchd) and Slack notifications, each with the exact
  undo command shown at setup time.
- First-run intro banner (`INTRO.md`), shown once per session.
- New York City established as the one fixed, non-configurable setting; every other criterion
  (area, household, bedrooms, budget, move timing, preferences) starts `null` and is asked about
  one question at a time during first-time setup (`FIRST-TIME-SETUP.md`), then stays mutable.
