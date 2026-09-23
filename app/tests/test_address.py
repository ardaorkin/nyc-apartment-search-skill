import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import GeoStatus
from parsers.address import classify_geo, extract_street_number, extract_unit, normalize_address


def test_normalize_expands_abbreviations():
    assert normalize_address("123 E 4th St") == "123 East 4Th Street"


def test_normalize_expands_avenue():
    assert normalize_address("45 Mulberry Ave") == "45 Mulberry Avenue"


def test_normalize_strips_unit():
    assert normalize_address("200 Mott St, Apt 5B") == "200 Mott Street"


def test_normalize_none_input():
    assert normalize_address(None) is None
    assert normalize_address("") is None


def test_normalize_strips_html_markup():
    """Regression: Manhattan Skyline's API returns display names with literal HTML
    (a trademark symbol wrapped in <sup>), which was leaking straight into listing
    addresses as visible markup instead of being stripped."""
    assert normalize_address("West River House<sup>®</sup>") == "West River House®"


def test_normalize_apostrophe_does_not_trigger_capitalization():
    """Regression: str.title() capitalizes the letter after ANY non-alpha character,
    including a possessive apostrophe -- "claridge's".title() -> "Claridge'S"."""
    assert normalize_address("Claridge's") == "Claridge's"


def test_normalize_unicode_right_quote_does_not_trigger_capitalization():
    """Regression: Manhattan Skyline's API uses the Unicode right single quote
    (U+2019), not an ASCII apostrophe -- "Claridge’s".title() ->
    "Claridge’S", and a fix that only matched ASCII "'" missed it entirely."""
    assert normalize_address("Claridge’s") == "Claridge’s"


def test_extract_unit():
    assert extract_unit("200 Mott St, Apt 5B") == "5B"
    assert extract_unit("200 Mott St, Unit 3") == "3"
    assert extract_unit("200 Mott St") is None


def test_extract_street_number():
    assert extract_street_number("200 Mott St") == 200
    assert extract_street_number(None) is None
    assert extract_street_number("Mott St") is None


def test_geo_no_area_configured_is_in_range():
    cfg = {"borough": None, "neighborhood": None, "min_street": None, "max_street": None}
    assert classify_geo("Brooklyn", "Williamsburg", None, cfg) == GeoStatus.IN_RANGE


def test_geo_borough_mismatch_out_of_range():
    cfg = {"borough": "Manhattan", "neighborhood": None, "min_street": None, "max_street": None}
    assert classify_geo("Brooklyn", None, None, cfg) == GeoStatus.OUT_OF_RANGE


def test_geo_borough_match_in_range():
    cfg = {"borough": "Manhattan", "neighborhood": None, "min_street": None, "max_street": None}
    assert classify_geo("Manhattan", None, None, cfg) == GeoStatus.IN_RANGE


def test_geo_neighborhood_unknown_needs_confirmation():
    cfg = {"borough": None, "neighborhood": "Little Italy", "min_street": None, "max_street": None}
    assert classify_geo(None, None, None, cfg) == GeoStatus.GEOGRAPHY_NEEDS_CONFIRMATION


def test_geo_borough_configured_unknown_listing_borough_needs_confirmation():
    """Regression: search.py used to hardcode listing_borough="Manhattan" for any
    listing with a neighborhood set, silently rejecting every real result as
    OUT_OF_RANGE for any borough other than Manhattan. An unknown listing borough
    must be kept and flagged, never guessed."""
    cfg = {"borough": "Brooklyn", "neighborhood": None, "min_street": None, "max_street": None}
    assert classify_geo(None, "Hudson Yards", None, cfg) == GeoStatus.GEOGRAPHY_NEEDS_CONFIRMATION


def test_street_range_filter_in_range():
    cfg = {"borough": None, "neighborhood": None, "min_street": 60, "max_street": 90}
    assert classify_geo(None, None, 75, cfg) == GeoStatus.IN_RANGE


def test_street_range_filter_out_of_range():
    cfg = {"borough": None, "neighborhood": None, "min_street": 60, "max_street": 90}
    assert classify_geo(None, None, 30, cfg) == GeoStatus.OUT_OF_RANGE


def test_street_range_filter_unknown_needs_confirmation():
    cfg = {"borough": None, "neighborhood": None, "min_street": 60, "max_street": 90}
    assert classify_geo(None, None, None, cfg) == GeoStatus.GEOGRAPHY_NEEDS_CONFIRMATION
