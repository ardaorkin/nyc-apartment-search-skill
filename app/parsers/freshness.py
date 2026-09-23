"""Classify listing freshness from availability language, timestamps, and status."""
from __future__ import annotations

from datetime import datetime, timezone

from models import ActiveStatus, Listing

_STALE_DAYS = 45
_UNCERTAIN_DAYS = 21


def classify_freshness(listing: Listing) -> ActiveStatus:
    text = (listing.description or "").lower()
    if any(p in text for p in ["no longer available", "off market", "rented", "leased", "taken"]):
        return ActiveStatus.OFF_MARKET

    if not listing.source_last_updated and not listing.checked_at:
        return ActiveStatus.UNCERTAIN

    reference = listing.checked_at
    updated_raw = listing.source_last_updated
    if updated_raw:
        try:
            updated = datetime.fromisoformat(updated_raw)
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            now = reference or datetime.now(timezone.utc)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            age_days = (now - updated).days
            if age_days > _STALE_DAYS:
                return ActiveStatus.STALE
            if age_days > _UNCERTAIN_DAYS:
                return ActiveStatus.UNCERTAIN
            return ActiveStatus.ACTIVE
        except ValueError:
            pass

    # No parseable source timestamp but we did see it fresh from a live fetch just now.
    return ActiveStatus.LIKELY_ACTIVE
