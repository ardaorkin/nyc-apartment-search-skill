"""Integration-level tests for search.py's apply_filters -- regression coverage for
the borough hardcoding bug found via a real Brooklyn-configured run that silently
returned zero results."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Listing
from search import apply_filters


def _listing(**kwargs) -> Listing:
    base = dict(source="test", checked_at=datetime.now(timezone.utc))
    base.update(kwargs)
    return Listing(**base)


def test_unknown_borough_listing_kept_not_rejected_when_borough_configured():
    """A real Manhattan-Skyline-style listing (neighborhood set, no borough info) must
    not be silently rejected when the user has configured a different borough --
    the old hardcoded listing_borough="Manhattan" caused exactly this."""
    config = {"location": {"borough": "Brooklyn"}, "household": {}, "preferences": {}}
    listing = _listing(address="123 Main St", neighborhood="Hudson Yards")
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == [listing]
    assert rejected == []
    assert listing.geo_status == "GEOGRAPHY_NEEDS_CONFIRMATION"


def test_citywide_no_area_configured_keeps_everything():
    config = {"location": {}, "household": {}, "preferences": {}}
    listing = _listing(address="123 Main St", neighborhood="Hudson Yards")
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == [listing]
    assert listing.geo_status == "IN_RANGE"


def test_required_preference_rejection_flows_through():
    config = {"location": {}, "household": {}, "preferences": {"doorman": "required"}}
    listing = _listing(address="123 Main St", doorman=False)
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == []
    assert len(rejected) == 1
    assert "doorman" in rejected[0][1]


def test_over_budget_listing_rejected_not_just_deprioritized():
    """Regression: max_rent is documented (SKILL.md, README) as a hard filter once
    set, but nothing enforced that -- an over-budget listing only lost ranking
    points in scoring.py, it was never actually rejected."""
    config = {"location": {}, "household": {}, "preferences": {}, "apartment": {"max_rent": 3000}}
    listing = _listing(address="123 Main St", monthly_rent=10000)
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == []
    assert len(rejected) == 1
    assert "max rent" in rejected[0][1]


def test_within_budget_listing_kept():
    config = {"location": {}, "household": {}, "preferences": {}, "apartment": {"max_rent": 3000}}
    listing = _listing(address="123 Main St", monthly_rent=2500)
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == [listing]


def test_unknown_rent_kept_when_budget_configured():
    """Never reject on missing data -- an unknown rent might still be a fit."""
    config = {"location": {}, "household": {}, "preferences": {}, "apartment": {"max_rent": 3000}}
    listing = _listing(address="123 Main St", monthly_rent=None)
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == [listing]


def test_no_budget_configured_keeps_expensive_listing():
    config = {"location": {}, "household": {}, "preferences": {}, "apartment": {}}
    listing = _listing(address="123 Main St", monthly_rent=50000)
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == [listing]


def test_below_minimum_bedrooms_rejected_not_just_deprioritized():
    """Regression: minimum_bedrooms is named as a floor ("minimum"), but like
    max_rent it was only ever consulted by scoring.py's ranking rubric -- a studio
    could still show up in results for someone who configured a 3BR minimum."""
    config = {"location": {}, "household": {}, "preferences": {}, "apartment": {"minimum_bedrooms": 3}}
    listing = _listing(address="123 Main St", bedrooms=1)
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == []
    assert len(rejected) == 1
    assert "minimum" in rejected[0][1]


def test_at_or_above_minimum_bedrooms_kept():
    config = {"location": {}, "household": {}, "preferences": {}, "apartment": {"minimum_bedrooms": 2}}
    listing = _listing(address="123 Main St", bedrooms=2)
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == [listing]


def test_unknown_bedrooms_kept_when_minimum_configured():
    config = {"location": {}, "household": {}, "preferences": {}, "apartment": {"minimum_bedrooms": 2}}
    listing = _listing(address="123 Main St", bedrooms=None)
    kept, rejected, _stage_counts = apply_filters([listing], config)
    assert kept == [listing]


def test_stage_counts_reflect_where_each_listing_actually_dropped():
    """Regression: the terminal summary used to report `after_geo` as
    `len(kept) + len(rejected)` -- always equal to raw_count, regardless of what was
    actually rejected at the geo stage, once pet/preference/budget/bedroom filtering
    moved into the same combined pass. Each stage's count must reflect real
    survivors.

    Borough alone can't produce OUT_OF_RANGE here (listing_borough is always None --
    see the comment in apply_filters), so this uses a neighborhood mismatch instead,
    which classify_geo does reject on."""
    config = {
        "location": {"neighborhood": "Chelsea"},
        "household": {"dogs": 1},
        "preferences": {"doorman": "required"},
        "apartment": {"max_rent": 3000, "minimum_bedrooms": 2},
    }
    out_of_range = _listing(neighborhood="Astoria")
    pet_rejected = _listing(neighborhood="Chelsea", pet_status="PROHIBITED")
    pref_rejected = _listing(neighborhood="Chelsea", doorman=False)
    over_budget = _listing(neighborhood="Chelsea", monthly_rent=5000)
    too_small = _listing(neighborhood="Chelsea", monthly_rent=2000, doorman=True, bedrooms=1)
    survivor = _listing(neighborhood="Chelsea", monthly_rent=2000, doorman=True, bedrooms=2)

    kept, rejected, stage_counts = apply_filters(
        [out_of_range, pet_rejected, pref_rejected, over_budget, too_small, survivor], config
    )

    assert kept == [survivor]
    assert stage_counts["geo"] == 5  # everyone except out_of_range
    assert stage_counts["pets"] == 4  # geo survivors minus pet_rejected
    assert stage_counts["preferences"] == 3  # pet survivors minus pref_rejected
    assert stage_counts["budget"] == 2  # preference survivors minus over_budget
    assert stage_counts["bedrooms"] == 1  # budget survivors minus too_small
