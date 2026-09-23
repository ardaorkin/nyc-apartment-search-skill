# Intro

Display this ASCII art on the first invocation of this skill in a session. Skip on subsequent
invocations within the same session. Print it exactly as-is, then continue to Step 0.

```
 _   _ ___ ___     _        _     ___                  _
| | | | __/ __|   /_\  _ __| |_  / __| ___ __ _ _ _ __| |_
| |_| | _|\__ \  / _ \| '_ \  _| \__ \/ -_) _` | '_/ _| ' \
 \___/|___|___/ /_/ \_\ .__/\__| |___/\___\__,_|_| \__|_||_|
                      |_|

  Search and re-check public NYC rental listings, keeping a deduplicated, ranked,
  change-tracked shortlist over time. Never applies, contacts brokers, or sends
  anything on your behalf.

  Storage:  ~/nyc-apartment-search/

  Usage (just ask, no slash command):
    "search for apartments"          run a search / re-check
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
