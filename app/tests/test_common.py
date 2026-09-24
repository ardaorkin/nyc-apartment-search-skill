"""Unit tests for sources/common.py's shared JSON-LD helpers."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import ActiveStatus, Listing
from parsers.freshness import classify_freshness
from sources.common import area_keywords_from_config, listing_from_jsonld, merge_residence_blocks, parse_sitemap_entries, parse_sitemap_urls


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


_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://example.com/listing/1</loc><lastmod>2026-09-23T19:08:26.048Z</lastmod></url>
<url><loc>https://example.com/listing/2</loc></url>
</urlset>"""


def test_parse_sitemap_entries_pairs_loc_with_lastmod():
    entries = parse_sitemap_entries(_SITEMAP_XML)
    assert entries == [
        ("https://example.com/listing/1", "2026-09-23T19:08:26.048Z"),
        ("https://example.com/listing/2", None),
    ]


def test_parse_sitemap_urls_still_returns_just_urls():
    """parse_sitemap_urls must stay a pure URL list -- every existing caller
    (SitemapAdapter's sub-sitemap recursion, related_rentals.py) depends on that,
    unchanged, even though it's now a thin wrapper over parse_sitemap_entries."""
    assert parse_sitemap_urls(_SITEMAP_XML) == [
        "https://example.com/listing/1",
        "https://example.com/listing/2",
    ]


def test_parse_sitemap_entries_malformed_xml_returns_empty():
    assert parse_sitemap_entries("not xml") == []


def _listing(**kwargs) -> Listing:
    base = dict(source="test", checked_at=datetime.now(timezone.utc))
    base.update(kwargs)
    return Listing(**base)


def test_listing_from_jsonld_threads_source_last_updated():
    """Regression: no adapter ever set source_last_updated, so classify_freshness
    could never return ACTIVE (only LIKELY_ACTIVE) for any listing, from any
    source, ever -- even though real, already-published lastmod data exists in
    the sitemaps these adapters already fetch."""
    block = {"name": "123 Main St", "offers": {"price": 3000}}
    listing = listing_from_jsonld(block, "test_source", "https://example.com/1", source_last_updated="2026-09-23T19:08:26.048Z")
    assert listing.source_last_updated == "2026-09-23T19:08:26.048Z"
    assert classify_freshness(listing) == ActiveStatus.ACTIVE


def test_listing_from_jsonld_source_last_updated_defaults_to_none():
    block = {"name": "123 Main St", "offers": {"price": 3000}}
    listing = listing_from_jsonld(block, "test_source", "https://example.com/1")
    assert listing.source_last_updated is None


def test_listing_from_jsonld_neighborhood_hint_wins_over_locality():
    """Regression: schema.org's addressLocality is the postal city, not a
    neighborhood -- a real Douglas Elliman listing in the West Village reported
    addressLocality="New York" (the city), and the old `locality or
    user_agent_neighborhood_hint` order let that silently override the specific,
    reliable neighborhood hint an adapter passes only when it already knows the
    real area (e.g. the URL was built from it). That defeated area-scoped search
    entirely: a genuinely-in-area listing got neighborhood="New York", failed to
    match the user's configured neighborhood, and was wrongly rejected as
    OUT_OF_RANGE. Found via a real West Village search that returned zero
    results despite real matching inventory existing."""
    block = {
        "name": "87 Perry Street",
        "address": {"streetAddress": "87 Perry Street", "addressLocality": "New York"},
        "offers": {"price": 21000},
    }
    listing = listing_from_jsonld(
        block, "douglas_elliman", "https://example.com/1", user_agent_neighborhood_hint="West Village"
    )
    assert listing.neighborhood == "West Village"


def test_listing_from_jsonld_locality_used_when_no_hint_given():
    """Sources that don't pass a hint (most of them) keep using locality as
    before -- this fix only reorders precedence, it doesn't remove locality."""
    block = {
        "name": "123 Main St",
        "address": {"streetAddress": "123 Main St", "addressLocality": "Brooklyn"},
        "offers": {"price": 3000},
    }
    listing = listing_from_jsonld(block, "test_source", "https://example.com/1")
    assert listing.neighborhood == "Brooklyn"
