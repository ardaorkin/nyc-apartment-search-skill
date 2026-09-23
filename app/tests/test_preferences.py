import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Listing
from parsers.preferences import required_preference_rejections


def _listing(**kwargs) -> Listing:
    base = dict(source="test", checked_at=datetime.now(timezone.utc))
    base.update(kwargs)
    return Listing(**base)


def test_no_preferences_configured_never_rejects():
    listing = _listing(in_unit_washer_dryer=False, dishwasher=False, doorman=False)
    assert required_preference_rejections(listing, {}) == []


def test_required_laundry_rejects_explicit_absence():
    listing = _listing(in_unit_washer_dryer=False)
    reasons = required_preference_rejections(listing, {"in_unit_laundry": "required"})
    assert reasons


def test_required_laundry_keeps_unknown():
    listing = _listing(in_unit_washer_dryer=None)
    assert required_preference_rejections(listing, {"in_unit_laundry": "required"}) == []


def test_preferred_never_rejects():
    listing = _listing(dishwasher=False)
    assert required_preference_rejections(listing, {"dishwasher": "preferred"}) == []


def test_required_doorman_rejects_explicit_absence():
    listing = _listing(doorman=False)
    reasons = required_preference_rejections(listing, {"doorman": "required"})
    assert reasons


def test_required_doorman_keeps_unknown():
    listing = _listing(doorman=None)
    assert required_preference_rejections(listing, {"doorman": "required"}) == []


def test_required_rent_stabilized_rejects_explicit_false():
    listing = _listing(rent_stabilized=False)
    reasons = required_preference_rejections(listing, {"rent_stabilized": "required"})
    assert reasons


def test_required_no_fee_rejects_when_fee_applies():
    listing = _listing(broker_fee_amount=2500, broker_fee_status="One month's fee")
    reasons = required_preference_rejections(listing, {"no_fee": "required"})
    assert reasons


def test_required_no_fee_keeps_when_status_says_no_fee():
    listing = _listing(broker_fee_amount=0, broker_fee_status="No fee")
    assert required_preference_rejections(listing, {"no_fee": "required"}) == []


def test_required_no_fee_keeps_when_fee_status_unknown():
    listing = _listing(broker_fee_amount=None, broker_fee_status=None)
    assert required_preference_rejections(listing, {"no_fee": "required"}) == []
