"""Geographic range classification per references/data-model.md's geo_status enum."""

from typing import Literal

GeoStatus = Literal["IN_RANGE", "GEOGRAPHY_NEEDS_CONFIRMATION", "OUT_OF_RANGE"]


def classify_geo(
    street_number: int | None,
    is_numbered_cross_street: bool,
    min_street: int = 60,
    max_street: int = 90,
) -> GeoStatus:
    """Classify whether a location falls within the configured street range.

    Numbered cross streets are checked directly against the range. Avenue
    addresses (not a numbered cross street) can't be range-checked from the
    street number alone, so an unconfirmable location is kept and flagged
    rather than rejected — never silently dropped.
    """
    if street_number is None:
        return "GEOGRAPHY_NEEDS_CONFIRMATION"
    if not is_numbered_cross_street:
        return "GEOGRAPHY_NEEDS_CONFIRMATION"
    if min_street <= street_number <= max_street:
        return "IN_RANGE"
    return "OUT_OF_RANGE"
