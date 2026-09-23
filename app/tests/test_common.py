"""Unit tests for sources/common.py's shared JSON-LD helpers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sources.common import area_keywords_from_config, merge_residence_blocks


def test_merge_residence_blocks_empty_list():
    assert merge_residence_blocks([]) == {}


def test_merge_residence_blocks_single_block_unchanged():
    block = {"@type": "Apartment", "name": "123 Main St"}
    assert merge_residence_blocks([block]) == block


def test_merge_residence_blocks_first_value_wins_on_conflict():
    """Regression: a real Corcoran page has an Apartment block with a clean name
    ("126 Sandford Street, 5141, ...") and a separate Product block with a noisier
    one ("... for For Rent") for the same real unit -- the cleaner, earlier block's
    value should win, not get silently overwritten."""
    first = {"name": "126 Sandford Street, 5141, Brooklyn, NY 11205"}
    second = {"name": "126 Sandford Street, 5141, Brooklyn, NY 11205 for For Rent"}
    merged = merge_residence_blocks([first, second])
    assert merged["name"] == first["name"]


def test_merge_residence_blocks_fills_gaps_from_later_blocks():
    """Regression: the Apartment block has no `offers` (price); a separate Product
    block on the same page carries the real Offer. Calling listing_from_jsonld once
    per block used to create two fragmented Listings for the same real apartment --
    one with no price, one with a different address string dedupe couldn't match."""
    descriptive = {"name": "126 Sandford Street, 5141", "offers": None}
    pricing = {"name": "noisier duplicate name", "offers": {"price": 3875}}
    merged = merge_residence_blocks([descriptive, pricing])
    assert merged["name"] == descriptive["name"]
    assert merged["offers"] == {"price": 3875}


def test_merge_residence_blocks_does_not_overwrite_present_value_with_empty():
    first = {"description": "A real description"}
    second = {"description": ""}
    merged = merge_residence_blocks([first, second])
    assert merged["description"] == "A real description"


def test_area_keywords_from_config_none_when_citywide():
    assert area_keywords_from_config({}) is None
    assert area_keywords_from_config({"neighborhood": None, "borough": None}) is None


def test_area_keywords_from_config_derives_slug_variants():
    keywords = area_keywords_from_config({"neighborhood": "Little Italy"})
    assert "little-italy" in keywords
    assert "little_italy" in keywords
    assert "littleitaly" in keywords
