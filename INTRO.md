# Intro

Display this ASCII art on the first invocation of this skill in a session. Skip on subsequent
invocations within the same session. Output the fenced code block below **verbatim, including
the triple-backtick markers** — outside a code fence, a markdown renderer treats the art's
backslashes as escape characters and underscores as italics markers, silently eating exactly
those characters. Then continue to Step 0.

```
 _  ___   _____     _   ___ _____   ___ ___   _   ___  ___ _  _
| \| \ \ / / __|   /_\ | _ \_   _| / __| __| /_\ | _ \/ __| || |
| .` |\ V / (__   / _ \|  _/ | |   \__ \ _| / _ \|   / (__| __ |
|_|\_| |_| \___| /_/ \_\_|   |_|   |___/___/_/ \_\_|_\\___|_||_|

  Search and re-check public New York City rental listings, keeping a deduplicated,
  ranked, change-tracked shortlist over time. NYC is the only fixed setting -- area,
  budget, household, and preferences all start unset and get asked about on first
  run, then stay mutable anytime after. Never applies, contacts brokers, or sends
  anything on your behalf.

  Version:  1.0.1  (see CHANGELOG.md)

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
