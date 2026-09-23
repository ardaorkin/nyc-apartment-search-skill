# app/

The ready-to-use codebase this skill copies to `~/nyc-apartment-search/` on first run, instead of
writing it from scratch each time. Built and debugged against the real sites (robots.txt/ToS
compliance, actual site structure, actual JSON-LD/API shapes) — see `references/sources.md` for
per-source access status.

Area (and every other search criterion) is entirely config-driven — nothing here hardcodes a
neighborhood, borough, or any other user-specific value. If you're adding a source or changing
one, never hardcode an area; derive it from `config.yaml`'s `location` block at fetch time (see
`sources/common.py`'s `area_keywords_from_config`, or `sources/douglas_elliman.py` /
`sources/related_rentals.py` for adapters that build their own request URLs from it) so it keeps
working correctly for every user, not just whoever's search it was built against.

## Structure

```
models.py          # Listing/SourceResult data model, all the status enums
search.py          # CLI entry point -- orchestrates adapters, filters, dedupe, scoring, reports
reports.py         # writes listings.csv/json, shortlist.md, changes.md
requirements.txt
parsers/           # address normalization, dedupe, pet-policy, rent parsing, freshness, risk, scoring
sources/           # one adapter per site, see sources/base.py for the shared contract
tests/             # pytest suite for the above
```

## Running

```bash
pip install -r requirements.txt
python search.py [--sources a,b] [--no-cache] [--max-rent N] [--dry-run]
pytest tests/
```

Needs `config.yaml` next to it (created by `FIRST-TIME-SETUP.md`, not shipped here — it holds
personal details and is gitignored).
