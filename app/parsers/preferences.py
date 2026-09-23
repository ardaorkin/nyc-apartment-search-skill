"""Apply config.yaml's `preferences` block as a hard filter when a value is
"required" (as opposed to "preferred", which is a ranking boost only -- see
parsers/scoring.py). Never rejects on unknown/unconfirmed data -- only on an
explicit, positive contradiction, same philosophy as the geo and pet filters."""
from __future__ import annotations

from models import Listing

_REQUIRED = "required"


def required_preference_rejections(listing: Listing, preferences: dict) -> list[str]:
    """Reasons this listing fails a "required" preference, or [] if it passes
    (including when a field is simply unknown -- unknown is never a rejection)."""
    reasons: list[str] = []

    if preferences.get("in_unit_laundry") == _REQUIRED and listing.in_unit_washer_dryer is False:
        reasons.append("in-unit laundry required but this listing doesn't have it")

    if preferences.get("dishwasher") == _REQUIRED and listing.dishwasher is False:
        reasons.append("dishwasher required but this listing doesn't have one")

    if preferences.get("doorman") == _REQUIRED and listing.doorman is False:
        reasons.append("doorman required but this listing doesn't have one")

    if preferences.get("rent_stabilized") == _REQUIRED and listing.rent_stabilized is False:
        reasons.append("rent stabilization required but this listing isn't rent-stabilized")

    if preferences.get("no_fee") == _REQUIRED and listing.broker_fee_amount and listing.broker_fee_status:
        if "no fee" not in listing.broker_fee_status.lower():
            reasons.append(f"no-fee required but a broker fee applies ({listing.broker_fee_status})")

    return reasons
