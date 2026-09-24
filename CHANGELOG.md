# Changelog

Semantic versioning: **patch** = bug fixes/wording, **minor** = new capability (non-breaking),
**major** = breaking behavior change. Bump the version in `SKILL.md`'s frontmatter `version:`
field and description, and in `INTRO.md`, with every change — add an entry here at the same time.

## 2.7.0 — 2026-09-24

Found on a genuinely clean second machine, running the skill for real for the first time (fresh
git clone, real first-time-setup Q&A, a real search for a 2BR in the West Village under $8k with
required in-unit laundry) -- not a hand-built test scenario:

- **Critical bug: area-scoped search was completely broken for every listing going through the
  shared JSON-LD path.** `listing_from_jsonld`'s `neighborhood=locality or
  user_agent_neighborhood_hint` let schema.org's `addressLocality` field -- which is the postal
  city ("New York" for every Manhattan address, regardless of neighborhood) -- silently override
  the specific, reliable neighborhood hint an adapter passes only when it already knows the real
  area (Douglas Elliman's URL is built directly from the configured neighborhood). The real,
  observed effect: a live search for "West Village" returned **zero results**, even though real,
  genuinely-in-area inventory existed -- unmistakable West Village addresses (87 Perry Street, 184
  Waverly Place, 68 Bank Street, 28 Jones Street, 111 Barrow Street) all got
  `neighborhood="New York"` instead of "West Village", failed the exact-match comparison against
  the configured area, and were silently rejected as `OUT_OF_RANGE`.
- Fixed by reordering precedence: the hint wins when an adapter provides one (it's only ever
  passed when already confirmed reliable); `locality` remains the fallback for adapters that don't
  pass a hint. Verified live, end to end: after the fix, all of the above addresses correctly
  report `neighborhood="West Village"`, and a real listing (401 West Street, the Superior Ink
  building) survived the full pipeline into the final ranked results for the first time. The
  small remaining result count for that specific search is real and expected, not a bug --
  West Village's largely pre-war housing stock plus a strict 2BR-minimum/$8k-budget/required-
  in-unit-laundry combination genuinely narrows the field this much; the other real West Village
  matches found were correctly rejected for genuine, visible reasons (over budget, under the
  bedroom minimum), not silently dropped.
- Deployed to a real `~/nyc-apartment-search/` project on a second machine as part of finding
  this -- confirmed the codebase installs and all tests pass cleanly on Python 3.14.7 too (not
  previously tested on this Python version).

2 new tests (80 total): the exact West Village/`addressLocality="New York"` regression, plus a
control test confirming sources that don't pass a hint are unaffected.

## 2.6.0 — 2026-09-23

Kept going ("And?", again) -- this time asking why every single listing across this whole
session's live testing always showed "Likely active, unconfirmed timestamp" and never once
showed as confidently `ACTIVE`:

- **Found: `source_last_updated` (read by `parsers/freshness.py`'s `classify_freshness` to
  distinguish `ACTIVE`/`STALE`/`UNCERTAIN`) was never set by any adapter, anywhere.** Every
  listing from every source always fell through to the same `LIKELY_ACTIVE` catch-all -- not
  wrong, but strictly less informative than it should be, and it silently made the scoring
  rubric's freshness dimension (5 vs 3 vs 1 points) never actually differentiate.
- **Fixed for the shared `SitemapAdapter` path** (Compass, Corcoran, Brown Harris Stevens, Equity
  Residential -- the bulk of real coverage): sitemap XML already publishes a per-URL `<lastmod>`
  timestamp that was being discarded entirely by `parse_sitemap_urls`, which only ever extracted
  `<loc>`. New `parse_sitemap_urls` is a thin wrapper over `parse_sitemap_entries`. Threaded
  through `SitemapAdapter` (`self._lastmod_by_url`) into `listing_from_jsonld`'s new
  `source_last_updated` parameter. Verified live: Corcoran listings now genuinely reach
  `ActiveStatus.ACTIVE` for the first time in this entire session's testing, using real,
  already-published data -- not fabricated.
- **Deliberately not extended to Related Rentals'** custom sitemap parsing: its per-URL
  `<lastmod>` values looked less clearly tied to individual-unit freshness on inspection (more
  consistent with a Drupal sitemap-generation batch stamp than genuine per-listing modification
  tracking) -- threading it through without being confident it's trustworthy would risk exactly
  the kind of fabricated-signal mistake this session has been fixing all day. Left as `null`,
  honestly, rather than guessed.

5 new tests (78 total): `parse_sitemap_entries` pairing and malformed-XML handling,
`parse_sitemap_urls`'s backward-compatible contract, and `listing_from_jsonld`'s new parameter
actually reaching `ActiveStatus.ACTIVE` end-to-end through `classify_freshness`.

## 2.5.1 — 2026-09-23

Continued the loop again (the user kept asking "And?" after each summary) -- cross-checking the
adapter registry, the blocked-sources list, and `config.yaml`'s `sources:` block against each
other for consistency:

- **Fixed a real documentation gap: `config.yaml`'s entire `sources:` block (`platforms`,
  `brokerages`, `managers`, `discovered`) is never read by `app/search.py` at all.** `ADAPTERS`
  is a hardcoded Python list; editing `config.yaml` to "add a source" has zero effect on what
  actually gets searched. This matters because "add a source" is one of this skill's own listed
  trigger phrases, but nothing in `SKILL.md` explained the real procedure -- a future session
  asked to add a source could easily believe editing `discovered: []` was sufficient. Fixed by
  being honest in `config.yaml`'s own comments (it's a human-tracking list only) and adding a
  real "Adding a source" procedure to `SKILL.md` Step 1: check robots.txt/ToS first, write an
  adapter file (subclass `SitemapAdapter` or write a custom one), set a real `unit` field, wire
  it into `ADAPTERS`, add tests, update `references/sources.md`.
- No code behavior changed -- documentation/process only, so this is a patch release. Adapter
  registry (`ADAPTERS`), the blocked-sources dict, and every name in `config.yaml`'s `sources:`
  lists were all cross-checked against each other and found consistent (no orphaned or
  double-counted source names).

## 2.5.0 — 2026-09-23

Continued the loop further, checking real per-source health (the user asked "And?" after an
earlier summary that stopped short):

- **Fixed: Corcoran's sitemap URL had gone stale.** The `/sitemap.xml` this skill was built
  against now 404s -- Corcoran restructured their sitemaps since 2026-09-22. Found the current
  location in their own robots.txt (dozens of per-region sitemaps; the NYC-rentals one is
  already for-rent-only). Verified live with today's real lastmod timestamps.
- **Fixed a real data-corruption bug, found while verifying the above:** a single listing page
  commonly carries *two* separate matching JSON-LD blocks -- an `Apartment`/`Residence` block
  with the descriptive fields, and a separate `Product`/`Offer` block that exists only to carry
  the price. Calling `listing_from_jsonld` once per block (the old behavior, shared by
  Compass/Corcoran/Brown Harris Stevens/Equity Residential/Douglas Elliman) created two
  fragmented Listings per real apartment, with different address text each -- so dedupe.py
  couldn't even merge them back together. Worse: one real Corcoran page's `Apartment` block
  reported `numberOfRooms: 4` for a $3,875/mo Bed-Stuy unit that is not a 4BR -- schema.org
  allows this field to mean either bedroom count or total room count depending on the site, and
  trusting it fabricated a wrong bedroom count rather than an honest unknown. Fixed both: new
  `merge_residence_blocks` combines same-page blocks into one dict (first block wins, later
  blocks only fill genuine gaps) so `listing_from_jsonld` runs once per page, and dropped the
  `numberOfRooms` fallback entirely. Verified live: Corcoran's raw listing count halved (28 -> 14,
  one clean listing per real apartment instead of two fragments) with correct bedroom counts and
  real prices throughout.
- **Verified, not fixed:** Brown Harris Stevens and Equity Residential now return HTTP 403 on
  their own homepages (not just their sitemaps), confirmed independently of this skill's code via
  a direct `curl`. This looks like active bot-defense, not a moved URL like Corcoran's -- and
  could be a real policy change, or same-day heavy testing triggering temporary rate-limiting on
  those two specific hosts. Recorded honestly as `BLOCKED_OR_MANUAL_REVIEW_REQUIRED` either way,
  with the ambiguity noted in `references/sources.md` rather than asserting a cause I can't
  confirm. Not attempted to route around regardless. Compass similarly stopped returning any
  sitemap URLs and is recorded as unresolved pending re-verification.

7 new tests (73 total), including dedicated coverage for `merge_residence_blocks`.

## 2.4.0 — 2026-09-23

Continued the same loop past the filter-enforcement sweep into dedupe correctness, on a real
non-dry-run search across multiple adapters together:

- **Bug: two genuinely different apartments in the same building silently merged into one
  listing, discarding one entirely.** `glenwood.py` and `related_rentals.py` never set a
  `unit` field on the listings they build. `parsers/dedupe.py`'s `_similar()` only rejects a
  match when *both* listings have a unit *and* they differ -- with both unset, two different
  1BRs in the same building (matching address + bedroom count + reasonably similar marketing
  copy) satisfied every remaining check and got merged, keeping only one's price/details.
  Fixed by deriving a stable per-listing identifier from each adapter's own detail-page URL
  (Glenwood's `?lid=N`, Related Rentals' trailing numeric ID) -- exactly the kind of
  "structured data over guesswork" the adapter contract already calls for elsewhere. Verified
  live: "The Bamford" and "The Barclay" (each genuinely two distinct units) now correctly
  appear as two rows instead of one.
- **Separate bug found while verifying the above:** `related_rentals.py` was silently dropping
  every listing whose page now reads "no longer available" instead of the real bed/bath/price
  block -- a `return None` that violated this skill's own explicit rule ("never silently
  discard a stale listing -- classify it"). Fixed to construct a proper `Listing` with
  `ActiveStatus.OFF_MARKET` (via the description marker `classify_freshness` already reads)
  instead of vanishing. In building this fix, found and fixed a third, adjacent bug: the
  off-market page's own header text isn't `"<Building> | <Address>"` like the live page,
  it's `"<Neighborhood> <Bed/Bath summary> | <Address>"` -- so reusing the live-page
  regex capture for "building name" produced garbage ("Bath 500 West 30th Street...").
  Fixed by reading the building name from the URL's own path segment instead (same
  pattern already used for neighborhood), verified live both before and after.

7 new tests (66 total): dedicated coverage for the two new URL-parsing helpers
(`_bedrooms_from_url`, `_building_from_url`).

## 2.3.0 — 2026-09-23

Same loop, same pattern found a third time -- once for max_rent (2.2.0), now for
`minimum_bedrooms`:

- **Bug: `minimum_bedrooms` is named as a floor but was only ever consulted by
  `scoring.py`'s ranking rubric** -- a studio could still appear in results for someone who
  configured a 3BR minimum, just scored low (2 points). `apply_filters` now rejects a known
  bedroom count below the configured minimum; unknown bedroom count is still never rejected.
  Verified live: 34 raw Manhattan Skyline listings dropped to exactly the 2 genuinely-3BR+
  units under a 3BR-minimum config.
- Added the new `bedrooms` stage to the terminal summary's funnel breakdown and `SKILL.md`'s
  Step 5 spec, plus a new Step 3 paragraph distinguishing `minimum_bedrooms` (hard filter) from
  `preferred_bedrooms` (ranking-only) explicitly, since the two are easy to conflate.

6 new/updated tests (59 total).

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
