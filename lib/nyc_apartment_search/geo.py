"""Geographic range classification per references/data-model.md's geo_status enum."""

from typing import Literal

GeoStatus = Literal["IN_RANGE", "GEOGRAPHY_NEEDS_CONFIRMATION", "OUT_OF_RANGE"]


def classify_geo(
    street_number: int | None,
    is_numbered_cross_street: bool,
    min_street: int | None = None,
    max_street: int | None = None,
) -> GeoStatus:
    """Classify whether a location falls within the configured street range.

    `min_street`/`max_street` are `None` unless the user has configured an area --
    citywide is the default, so no range configured means no restriction at all:
    everything is `IN_RANGE`. Once a range is configured, numbered cross streets
    are checked directly against it. Avenue addresses (not a numbered cross
    street) can't be range-checked from the street number alone, so an
    unconfirmable location is kept and flagged rather than rejected -- never
    silently dropped.
    """
    if min_street is None or max_street is None:
        return "IN_RANGE"
    if street_number is None:
        return "GEOGRAPHY_NEEDS_CONFIRMATION"
    if not is_numbered_cross_street:
        return "GEOGRAPHY_NEEDS_CONFIRMATION"
    if min_street <= street_number <= max_street:
        return "IN_RANGE"
    return "OUT_OF_RANGE"
