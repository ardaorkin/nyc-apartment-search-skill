"""Deterministic unit tests for the pure-logic pieces SKILL.md requires tests for:
address normalization, street-range filtering, pet-policy classification,
deduplication, and rent parsing. No network, no LLM -- fixed input, fixed
expected output.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from nyc_apartment_search.address import normalize_address, normalize_unit
from nyc_apartment_search.dedupe import dedupe_key
from nyc_apartment_search.geo import classify_geo
from nyc_apartment_search.pets import classify_pet_policy
from nyc_apartment_search.rent import parse_rent


class TestNormalizeAddress:
    def test_expands_directional_and_street_type(self):
        assert normalize_address("E 85th St") == "EAST 85 STREET"

    def test_matches_fully_spelled_out_equivalent(self):
        assert normalize_address("E 85th St") == normalize_address("East 85 Street")

    def test_expands_avenue_abbreviation(self):
        assert normalize_address("1st Ave") == normalize_address("1 Avenue")

    def test_empty_input_returns_empty_string(self):
        assert normalize_address("") == ""

    def test_none_input_returns_empty_string(self):
        assert normalize_address(None) == ""


class TestNormalizeUnit:
    def test_strips_unit_prefix(self):
        assert normalize_unit("Unit 4B") == "4B"

    def test_strips_apt_prefix(self):
        assert normalize_unit("Apt 4B") == "4B"

    def test_strips_hash_prefix(self):
        assert normalize_unit("#4B") == "4B"

    def test_none_stays_none(self):
        assert normalize_unit(None) is None


class TestClassifyGeo:
    def test_in_range_numbered_cross_street(self):
        assert classify_geo(85, is_numbered_cross_street=True) == "IN_RANGE"

    def test_out_of_range_below_min(self):
        assert classify_geo(45, is_numbered_cross_street=True) == "OUT_OF_RANGE"

    def test_out_of_range_above_max(self):
        assert classify_geo(95, is_numbered_cross_street=True) == "OUT_OF_RANGE"

    def test_boundary_min_is_in_range(self):
        assert classify_geo(60, is_numbered_cross_street=True) == "IN_RANGE"

    def test_boundary_max_is_in_range(self):
        assert classify_geo(90, is_numbered_cross_street=True) == "IN_RANGE"

    def test_avenue_address_needs_confirmation_not_rejection(self):
        assert (
            classify_geo(1450, is_numbered_cross_street=False)
            == "GEOGRAPHY_NEEDS_CONFIRMATION"
        )

    def test_missing_street_number_needs_confirmation(self):
        assert classify_geo(None, is_numbered_cross_street=True) == "GEOGRAPHY_NEEDS_CONFIRMATION"

    def test_custom_range_bounds(self):
        assert classify_geo(65, is_numbered_cross_street=True, min_street=40, max_street=59) == "OUT_OF_RANGE"
        assert classify_geo(45, is_numbered_cross_street=True, min_street=40, max_street=59) == "IN_RANGE"


class TestClassifyPetPolicy:
    def test_explicit_cat_ban_is_prohibited(self):
        assert classify_pet_policy("Sorry, no cats allowed") == "PROHIBITED"

    def test_general_no_pets_is_prohibited(self):
        assert classify_pet_policy("No pets in this building") == "PROHIBITED"

    def test_cats_allowed_marker(self):
        assert classify_pet_policy("Cats allowed, dogs case by case") == "CATS_ALLOWED"

    def test_pets_allowed_marker(self):
        assert classify_pet_policy("Pet friendly building") == "PETS_ALLOWED"

    def test_case_by_case_marker(self):
        assert classify_pet_policy("Pets case-by-case, ask management") == "CASE_BY_CASE"

    def test_unknown_text_needs_confirmation_not_a_guess(self):
        assert classify_pet_policy("Spacious 2BR with great light") == "PET_POLICY_NEEDS_CONFIRMATION"

    def test_missing_text_needs_confirmation(self):
        assert classify_pet_policy(None) == "PET_POLICY_NEEDS_CONFIRMATION"
        assert classify_pet_policy("") == "PET_POLICY_NEEDS_CONFIRMATION"


class TestDedupeKey:
    def test_same_address_different_formatting_same_key(self):
        assert dedupe_key("E 85th St", "4B") == dedupe_key("East 85 Street", "Unit 4B")

    def test_different_units_different_keys(self):
        assert dedupe_key("E 85th St", "4B") != dedupe_key("E 85th St", "5C")

    def test_missing_unit_is_stable(self):
        assert dedupe_key("E 85th St", None) == dedupe_key("East 85 Street", None)


class TestParseRent:
    def test_strips_currency_and_commas(self):
        assert parse_rent("$3,500") == 3500

    def test_plain_number(self):
        assert parse_rent("3500") == 3500

    def test_implausibly_low_value_rejected(self):
        assert parse_rent("$5") is None

    def test_implausibly_high_value_rejected(self):
        assert parse_rent("$99,999,999") is None

    def test_empty_input_rejected(self):
        assert parse_rent("") is None
        assert parse_rent(None) is None

    def test_non_numeric_input_rejected(self):
        assert parse_rent("Call for pricing") is None
