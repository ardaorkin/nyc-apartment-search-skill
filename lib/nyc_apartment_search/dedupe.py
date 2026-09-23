"""Deduplication key construction.

Dedupe primarily on normalized street address + unit, per references/sources.md.
"""

from .address import normalize_address, normalize_unit


def dedupe_key(address: str, unit: str | None) -> str:
    norm_address = normalize_address(address)
    norm_unit = normalize_unit(unit)
    return f"{norm_address}|{norm_unit or ''}"
