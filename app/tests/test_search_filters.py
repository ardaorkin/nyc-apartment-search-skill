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
    kept, rejected = apply_filters([listing], config)
    assert kept == [listing]
    assert rejected == []
    assert listing.geo_status == "GEOGRAPHY_NEEDS_CONFIRMATION"


def test_citywide_no_area_configured_keeps_everything():
    config = {"location": {}, "household": {}, "preferences": {}}
    listing = _listing(address="123 Main St", neighborhood="Hudson Yards")
    kept, rejected = apply_filters([listing], config)
    assert kept == [listing]
    assert listing.geo_status == "IN_RANGE"


def test_required_preference_rejection_flows_through():
    config = {"location": {}, "household": {}, "preferences": {"doorman": "required"}}
    listing = _listing(address="123 Main St", doorman=False)
    kept, rejected = apply_filters([listing], config)
    assert kept == []
    assert len(rejected) == 1
    assert "doorman" in rejected[0][1]
