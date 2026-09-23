import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parsers.rent import parse_rent


def test_parse_plain_dollar_string():
    assert parse_rent("$4,500") == 4500.0


def test_parse_plain_number():
    assert parse_rent(4500) == 4500.0


def test_parse_rejects_zestimate_language():
    assert parse_rent("Zestimate: $3,200/mo") is None


def test_parse_rejects_estimate_language():
    assert parse_rent("Rent estimate: $3,200") is None


def test_parse_rejects_implausibly_low():
    assert parse_rent("$50") is None


def test_parse_rejects_implausibly_high():
    assert parse_rent("$5,000,000") is None


def test_parse_none_input():
    assert parse_rent(None) is None
