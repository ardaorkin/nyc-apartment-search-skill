"""Address normalization and geographic filtering against config.yaml's location block."""
from __future__ import annotations

import re
from typing import Optional

from models import GeoStatus

_DIRECTION_MAP = {
    "n": "North", "s": "South", "e": "East", "w": "West",
    "ne": "Northeast", "nw": "Northwest", "se": "Southeast", "sw": "Southwest",
}

_STREET_TYPE_MAP = {
    "st": "Street", "ave": "Avenue", "av": "Avenue", "blvd": "Boulevard",
    "pl": "Place", "sq": "Square", "ln": "Lane", "dr": "Drive",
    "ct": "Court", "rd": "Road", "pkwy": "Parkway", "ter": "Terrace",
    "hwy": "Highway",
}

_ORDINAL_RE = re.compile(r"^(\d+)(st|nd|rd|th)$", re.IGNORECASE)

_UNIT_RE = re.compile(
    r"[,#]?\s*(?:unit|apt|apartment|suite|ste|#)\s*[:\-]?\s*([\w\-]+)\s*$",
    re.IGNORECASE,
)


def _expand_token(token: str) -> str:
    bare = token.strip(".,").lower()
    if bare in _DIRECTION_MAP:
        return _DIRECTION_MAP[bare]
    if bare in _STREET_TYPE_MAP:
        return _STREET_TYPE_MAP[bare]
    m = _ORDINAL_RE.match(bare)
    if m:
        return f"{m.group(1)}{m.group(2).lower()}"
    return token


def normalize_address(raw: Optional[str]) -> Optional[str]:
    """Expand directional/street-type abbreviations and ordinal suffixes, strip unit
    designators (returned separately by extract_unit), collapse whitespace/case for
    comparison purposes."""
    if not raw or not raw.strip():
        return None
    without_unit = _UNIT_RE.sub("", raw).strip().rstrip(",")
    tokens = without_unit.replace(",", " ").split()
    expanded = [_expand_token(t) for t in tokens]
    normalized = " ".join(expanded)
    return re.sub(r"\s+", " ", normalized).strip().title()


def extract_unit(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    m = _UNIT_RE.search(raw)
    if m:
        return m.group(1).upper()
    return None


def extract_street_number(address: Optional[str]) -> Optional[int]:
    """Numbered cross-street parsing: pull the leading street number for direct
    comparison against a configured min/max street range."""
    if not address:
        return None
    m = re.match(r"^\s*(\d+)", address)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def classify_geo(
    listing_borough: Optional[str],
    listing_neighborhood: Optional[str],
    cross_street_number: Optional[int],
    location_config: dict,
) -> GeoStatus:
    """Apply config.yaml's location block as a hard filter. With no area configured
    (all fields null), everything is IN_RANGE by definition -- there is nothing to
    reject on location grounds."""
    borough = location_config.get("borough")
    neighborhood = location_config.get("neighborhood")
    min_street = location_config.get("min_street")
    max_street = location_config.get("max_street")

    if not borough and not neighborhood and min_street is None and max_street is None:
        return GeoStatus.IN_RANGE

    if borough and listing_borough:
        if listing_borough.strip().lower() != borough.strip().lower():
            return GeoStatus.OUT_OF_RANGE
    elif borough and not listing_borough:
        return GeoStatus.GEOGRAPHY_NEEDS_CONFIRMATION

    if neighborhood and listing_neighborhood:
        if listing_neighborhood.strip().lower() != neighborhood.strip().lower():
            return GeoStatus.OUT_OF_RANGE
    elif neighborhood and not listing_neighborhood:
        return GeoStatus.GEOGRAPHY_NEEDS_CONFIRMATION

    if min_street is not None or max_street is not None:
        if cross_street_number is None:
            return GeoStatus.GEOGRAPHY_NEEDS_CONFIRMATION
        if min_street is not None and cross_street_number < min_street:
            return GeoStatus.OUT_OF_RANGE
        if max_street is not None and cross_street_number > max_street:
            return GeoStatus.OUT_OF_RANGE

    return GeoStatus.IN_RANGE
