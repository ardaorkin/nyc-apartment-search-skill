# Changelog

Semantic versioning: **patch** = bug fixes/wording, **minor** = new capability (non-breaking),
**major** = breaking behavior change. Bump the version in `SKILL.md`'s frontmatter `version:`
field and description, and in `INTRO.md`, with every change — add an entry here at the same time.

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
