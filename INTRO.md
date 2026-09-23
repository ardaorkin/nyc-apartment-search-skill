# Intro

Display this banner on the first invocation of this skill in a session. Skip on subsequent
invocations within the same session. Output the fenced code block below **verbatim, including
the triple-backtick markers**. Deliberately plain: earlier, denser figlet-style art (lots of
`\` and `_`, tight monospace alignment) got garbled in practice — not just by markdown escaping
`\`/`_`, but because reproducing dense character art exactly isn't reliable in the first place.
This banner uses only `+`, `-`, `|`, and plain text specifically so there's nothing dense enough
to garble. Don't replace it with fancier art later without confirming it survives an actual run,
not just how it looks in the source file.

```
+--------------------------------------------------------------+
|                     NYC APARTMENT SEARCH                     |
+--------------------------------------------------------------+

  Search and re-check public New York City rental listings, keeping a deduplicated,
  ranked, change-tracked shortlist over time. NYC is the only fixed setting -- area,
  budget, household, and preferences all start unset and get asked about on first
  run, then stay mutable anytime after. Never applies, contacts brokers, or sends
  anything on your behalf.

  Version:  2.2.0  (see CHANGELOG.md)

  Storage:  ~/nyc-apartment-search/

  Usage (just ask, no slash command):
    "search for apartments"          first run asks area/budget/household/etc.
    "just the Upper East Side"       narrow to an area (any neighborhood/borough/range)
    "any price drops?"               what changed since last time
    "set my max rent to $X"          update the budget filter
    "add a source"                   add a brokerage/property manager
    "draft a message for this one"   draft (never sends) an inquiry

  Scheduling and Slack notifications are opt-in only — ask any time, nothing runs
  in the background until you say yes.

  Coverage: see references/sources.md — most major aggregators (StreetEasy, RentHop,
  Apartments.com, Realtor.com) are correctly blocked by their own ToS; real coverage
  comes from brokerages and property managers.
```
