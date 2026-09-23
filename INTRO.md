# Intro

Display this ASCII art on the first invocation of this skill in a session. Skip on subsequent
invocations within the same session. Print it exactly as-is, then continue to Step 0.

```
 _   ___   ______      _          _     ____                      _
| \ | \ \ / / ___|    / \   _ __ | |_  / ___|  ___  __ _ _ __ ___| |__
|  \| |\ V / |       / _ \ | '_ \| __| \___ \ / _ \/ _` | '__/ __| '_ \
| |\  | | || |___   / ___ \| |_) | |_   ___) |  __/ (_| | | | (__| | | |
|_| \_| |_| \____| /_/   \_\ .__/ \__| |____/ \___|\__,_|_|  \___|_| |_|
                           |_|

  Search and re-check public NYC rental listings, keeping a deduplicated, ranked,
  change-tracked shortlist over time. Citywide by default -- narrows to a specific
  neighborhood, borough, or street range only if you ask. Never applies, contacts
  brokers, or sends anything on your behalf.

  Storage:  ~/nyc-apartment-search/

  Usage (just ask, no slash command):
    "search for apartments"          run a search / re-check, citywide by default
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
