import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Listing
from parsers.dedupe import deduplicate


def _listing(**kwargs) -> Listing:
    base = dict(source="test", checked_at=datetime.now(timezone.utc))
    base.update(kwargs)
    return Listing(**base)


def test_dedupe_merges_same_address_different_sources():
    a = _listing(source="compass", address="200 Mott St", unit="5B", monthly_rent=4500, bedrooms=2)
    b = _listing(source="corcoran", address="200 Mott Street", unit="5B", monthly_rent=4600, bedrooms=2, listing_url="https://corcoran.com/x")
    merged = deduplicate([a, b])
    assert len(merged) == 1
    assert len(merged[0].observed_prices) == 2


def test_dedupe_keeps_distinct_addresses_separate():
    a = _listing(address="200 Mott St", unit="5B", bedrooms=2)
    b = _listing(address="45 Mulberry St", unit="2A", bedrooms=2)
    merged = deduplicate([a, b])
    assert len(merged) == 2


def test_dedupe_keeps_distinct_units_at_same_address_separate():
    a = _listing(address="200 Mott St", unit="5B", bedrooms=2)
    b = _listing(address="200 Mott St", unit="5C", bedrooms=2)
    merged = deduplicate([a, b])
    assert len(merged) == 2


def test_dedupe_merges_source_urls():
    a = _listing(address="200 Mott St", unit="5B", listing_url="https://a.com/1")
    b = _listing(address="200 Mott St", unit="5B", listing_url="https://b.com/1")
    merged = deduplicate([a, b])
    assert len(merged) == 1
    assert "https://a.com/1" in merged[0].source_urls
    assert "https://b.com/1" in merged[0].source_urls
