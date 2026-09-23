"""Address normalization for deduplication.

Expands/standardizes directional and street-type abbreviations plus ordinal
suffixes so the same address written two different ways compares equal.
"""

import re

_DIRECTIONALS = {
    "E": "EAST",
    "W": "WEST",
    "N": "NORTH",
    "S": "SOUTH",
}

_STREET_TYPES = {
    "ST": "STREET",
    "AVE": "AVENUE",
    "AV": "AVENUE",
    "BLVD": "BOULEVARD",
    "PL": "PLACE",
    "RD": "ROAD",
    "DR": "DRIVE",
    "LN": "LANE",
    "SQ": "SQUARE",
    "PKWY": "PARKWAY",
}

_ORDINAL_RE = re.compile(r"^(\d+)(ST|ND|RD|TH)$")


def _expand_token(token: str) -> str:
    bare = token.rstrip(".")
    if bare in _DIRECTIONALS:
        return _DIRECTIONALS[bare]
    if bare in _STREET_TYPES:
        return _STREET_TYPES[bare]
    match = _ORDINAL_RE.match(bare)
    if match:
        return match.group(1)
    return bare


def normalize_address(raw: str) -> str:
    """Normalize a street address to a canonical comparison form.

    Uppercases, strips punctuation, expands directional/street-type
    abbreviations, and drops ordinal suffixes on numbered cross streets so
    "E 85th St" and "East 85 Street" normalize identically.
    """
    if not raw:
        return ""
    cleaned = re.sub(r"[.,#]", " ", raw.upper())
    tokens = [t for t in cleaned.split() if t]
    expanded = [_expand_token(t) for t in tokens]
    return " ".join(expanded)


def normalize_unit(raw: str | None) -> str | None:
    """Normalize a unit designator for comparison. None stays None."""
    if raw is None:
        return None
    cleaned = re.sub(r"^(UNIT|APT|#)\s*", "", raw.strip().upper())
    return cleaned or None
