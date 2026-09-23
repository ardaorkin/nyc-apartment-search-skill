"""Unit tests for related_rentals.py's URL-parsing helpers -- regression coverage
for the off-market-listing fix (a stale page's own header text is unreliable, but
the URL's own structure isn't)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sources.related_rentals import RelatedRentalsAdapter, _bedrooms_from_url

_STUDIO_URL = "https://www.relatedrentals.com/apartment-rentals/new-york-city/hudson-yards/abington-house/studio-1-bath-26173"
_ONE_BED_URL = "https://www.relatedrentals.com/apartment-rentals/new-york-city/hudson-yards/abington-house/1-bedroom-1-bath-26300"
_TWO_BED_URL = "https://www.relatedrentals.com/apartment-rentals/new-york-city/hudson-yards/abington-house/corner-2-bedroom-2-bath-terrace-26099"


def test_bedrooms_from_url_studio():
    assert _bedrooms_from_url(_STUDIO_URL) == 0.0


def test_bedrooms_from_url_one_bedroom():
    assert _bedrooms_from_url(_ONE_BED_URL) == 1.0


def test_bedrooms_from_url_two_bedroom():
    assert _bedrooms_from_url(_TWO_BED_URL) == 2.0


def test_bedrooms_from_url_no_match_returns_none():
    assert _bedrooms_from_url("https://www.relatedrentals.com/apartment-rentals/new-york-city/hudson-yards/abington-house/mystery-99999") is None


def test_building_from_url():
    assert RelatedRentalsAdapter._building_from_url(_ONE_BED_URL) == "Abington House"


def test_building_from_url_no_match_returns_none():
    assert RelatedRentalsAdapter._building_from_url("https://example.com/nope") is None


def test_neighborhood_from_url():
    assert RelatedRentalsAdapter._neighborhood_from_url(_ONE_BED_URL) == "Hudson Yards"
