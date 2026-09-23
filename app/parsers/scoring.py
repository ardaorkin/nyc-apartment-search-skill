"""0-100 ranking rubric. Scores ACTIVE / LIKELY_ACTIVE listings only.

Note: `preferences.elevator_above_floor` isn't scored here (or filtered anywhere) -- listing.floor
is free text ("5", "PH", "Garden", ...) with no parser to compare it against a numeric threshold.
See the comment above that field in assets/config.yaml before wiring it in."""
from __future__ import annotations

import statistics

from models import ActiveStatus, GeoStatus, Listing, PetStatus


def _location_score(listing: Listing, area_configured: bool) -> tuple[int, str | None]:
    if area_configured:
        if listing.geo_status == GeoStatus.IN_RANGE:
            return 20, "Matches the configured area"
        if listing.geo_status == GeoStatus.GEOGRAPHY_NEEDS_CONFIRMATION:
            return 10, "Area unconfirmed"
        return 0, None
    return 15, "No area configured -- generic location credit"


def _value_score(listing: Listing, comparable_rents: list[float], max_rent: float | None) -> tuple[int, str | None]:
    if listing.monthly_rent is None:
        return 5, "Rent unknown"
    if max_rent:
        if listing.monthly_rent <= max_rent * 0.85:
            return 20, "Comfortably under budget"
        if listing.monthly_rent <= max_rent:
            return 14, "Within budget"
        return 4, "Over configured max rent"
    if comparable_rents:
        median = statistics.median(comparable_rents)
        if listing.monthly_rent <= median:
            return 18, "At or below comparable median rent"
        return 10, "Above comparable median rent"
    return 12, None


def _layout_score(listing: Listing, preferred_bedrooms: float | None, minimum_bedrooms: float | None) -> tuple[int, str | None]:
    if listing.bedrooms is None:
        return 6, "Bedroom count unknown"
    if preferred_bedrooms and listing.bedrooms == preferred_bedrooms:
        return 15, f"Matches preferred {preferred_bedrooms:g}BR"
    if minimum_bedrooms and listing.bedrooms >= minimum_bedrooms:
        return 12, "Meets minimum bedroom count"
    if minimum_bedrooms and listing.bedrooms < minimum_bedrooms:
        return 2, "Below minimum bedroom count"
    return 10, None


def _amenity_score(listing: Listing, preferences: dict) -> tuple[int, list[str]]:
    points, reasons = 0, []
    checks = [
        ("in_unit_washer_dryer", "in_unit_laundry", 6, "In-unit laundry"),
        ("dishwasher", "dishwasher", 5, "Dishwasher"),
    ]
    for field, pref_key, weight, label in checks:
        val = getattr(listing, field)
        pref = preferences.get(pref_key)
        if val is True:
            points += weight
            reasons.append(label)
        elif pref in ("required", "preferred") and val is None:
            reasons.append(f"{label} unconfirmed")
    if listing.laundry and "in unit" not in (listing.laundry or "").lower():
        points += 2
    return min(points, 15), reasons


def _pet_score(listing: Listing, has_dog: bool, has_cat: bool) -> tuple[int, str | None]:
    if listing.pet_status == PetStatus.PETS_ALLOWED:
        return 10, "Pets allowed"
    if has_dog and listing.dog_allowed:
        return 10, "Dog explicitly allowed"
    if listing.pet_status == PetStatus.CASE_BY_CASE:
        return 6, "Pets case-by-case"
    if listing.pet_status == PetStatus.CATS_ALLOWED and not has_dog:
        return 10, "Cats allowed"
    if listing.pet_status == PetStatus.PET_POLICY_NEEDS_CONFIRMATION:
        return 4, "Pet policy needs confirmation"
    if listing.pet_status == PetStatus.PROHIBITED:
        return 0, "Pets prohibited"
    return 5, None


def _fee_score(listing: Listing, preferences: dict) -> tuple[int, str | None]:
    if listing.broker_fee_status and "no fee" in listing.broker_fee_status.lower():
        return 10, "No broker fee"
    if listing.broker_fee_amount:
        return 3, "Broker fee applies"
    return 6, None


def _building_score(listing: Listing, doorman_pref: str | None) -> tuple[int, list[str]]:
    points, reasons = 0, []
    if listing.elevator:
        points += 2
        reasons.append("Elevator building")
    if listing.doorman:
        points += 3 if doorman_pref in ("required", "preferred") else 2
        reasons.append("Doorman")
    if listing.brokerage_or_management_company:
        points += 0  # informational only, no extra credit beyond presence
    return min(points, 5), reasons


def _freshness_score(listing: Listing) -> tuple[int, str | None]:
    if listing.active_status == ActiveStatus.ACTIVE:
        return 5, "Confirmed active"
    if listing.active_status == ActiveStatus.LIKELY_ACTIVE:
        return 3, "Likely active, unconfirmed timestamp"
    return 1, None


def score_listing(listing: Listing, config: dict, comparable_rents: list[float]) -> tuple[int, list[str]]:
    location = config.get("location", {})
    apartment = config.get("apartment", {})
    household = config.get("household", {})
    preferences = config.get("preferences", {})

    area_configured = any([location.get("borough"), location.get("neighborhood"), location.get("min_street"), location.get("max_street")])
    has_dog = bool(household.get("dogs"))
    has_cat = bool(household.get("cats"))

    reasons: list[str] = []
    total = 0

    pts, why = _location_score(listing, area_configured)
    total += pts
    if why:
        reasons.append(why)

    pts, why = _value_score(listing, comparable_rents, apartment.get("max_rent"))
    total += pts
    if why:
        reasons.append(why)

    pts, why = _layout_score(listing, apartment.get("preferred_bedrooms"), apartment.get("minimum_bedrooms"))
    total += pts
    if why:
        reasons.append(why)

    pts, whys = _amenity_score(listing, preferences)
    total += pts
    reasons.extend(whys)

    pts, why = _pet_score(listing, has_dog, has_cat)
    total += pts
    if why:
        reasons.append(why)

    pts, why = _fee_score(listing, preferences)
    total += pts
    if why:
        reasons.append(why)

    pts, whys = _building_score(listing, preferences.get("doorman"))
    total += pts
    reasons.extend(whys)

    pts, why = _freshness_score(listing)
    total += pts
    if why:
        reasons.append(why)

    return min(total, 100), reasons
