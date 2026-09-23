"""Deduplicate Listings across sources onto one canonical record per apartment."""
from __future__ import annotations

from rapidfuzz import fuzz

from models import Listing, ObservedPrice
from parsers.address import normalize_address


def _dedupe_key(listing: Listing) -> str:
    addr = normalize_address(listing.address) or ""
    unit = (listing.unit or "").strip().upper()
    return f"{addr}|{unit}"


def _similar(a: Listing, b: Listing) -> bool:
    if a.unit and b.unit and a.unit.strip().upper() != b.unit.strip().upper():
        return False
    addr_a, addr_b = normalize_address(a.address), normalize_address(b.address)
    if not addr_a or not addr_b:
        return False
    if fuzz.ratio(addr_a, addr_b) < 90:
        return False
    if a.bedrooms is not None and b.bedrooms is not None and a.bedrooms != b.bedrooms:
        return False
    if a.description and b.description:
        if fuzz.token_set_ratio(a.description, b.description) < 60 and fuzz.ratio(addr_a, addr_b) < 97:
            return False
    return True


def _merge(primary: Listing, other: Listing) -> Listing:
    merged = primary.model_copy(deep=True)
    for url in other.source_urls or ([other.listing_url] if other.listing_url else []):
        if url and url not in merged.source_urls:
            merged.source_urls.append(url)
    # other.observed_prices is already seeded with its own monthly_rent by deduplicate()
    # before _merge is called -- don't append it again here.
    merged.observed_prices = list(merged.observed_prices) + list(other.observed_prices)
    # keep most-recently-updated price as canonical
    if merged.observed_prices:
        latest = max(merged.observed_prices, key=lambda p: p.observed_at)
        merged.monthly_rent = latest.value
    for field in type(merged).model_fields:
        if field in ("source_urls", "observed_prices", "monthly_rent"):
            continue
        if getattr(merged, field) in (None, [], "") and getattr(other, field) not in (None, [], ""):
            setattr(merged, field, getattr(other, field))
    if other.checked_at and (not merged.last_seen or (other.checked_at.date() > merged.last_seen)):
        merged.last_seen = other.checked_at.date()
    return merged


def deduplicate(listings: list[Listing]) -> list[Listing]:
    canonical: list[Listing] = []
    for listing in listings:
        # seed observed_prices with this source's own rent if not already present
        if listing.monthly_rent is not None and not listing.observed_prices:
            listing.observed_prices = [
                ObservedPrice(value=listing.monthly_rent, source=listing.source, observed_at=listing.checked_at)
            ]
        if listing.listing_url and listing.listing_url not in listing.source_urls:
            listing.source_urls.append(listing.listing_url)

        match_idx = None
        for i, existing in enumerate(canonical):
            if _similar(existing, listing):
                match_idx = i
                break
        if match_idx is None:
            canonical.append(listing)
        else:
            canonical[match_idx] = _merge(canonical[match_idx], listing)
    return canonical
