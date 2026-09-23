# Changelog

Semantic versioning: **patch** = bug fixes/wording, **minor** = new capability (non-breaking),
**major** = breaking behavior change. Bump the version in `SKILL.md`'s frontmatter `version:`
field and description, and in `INTRO.md`, with every change — add an entry here at the same time.

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
