"""Rent parsing. Never substitutes a Zestimate/estimate/historical price -- callers must
pass only text that the source explicitly labels as the current asking rent."""
from __future__ import annotations

import re
from typing import Optional

_RENT_RE = re.compile(r"\$?\s*([\d,]+(?:\.\d{1,2})?)")

# Plausible monthly-rent bounds for NYC. Anything outside this is rejected rather than
# guessed at -- it's more likely a sale price, a deposit, or a parsing error.
_MIN_PLAUSIBLE = 500
_MAX_PLAUSIBLE = 100_000


def parse_rent(raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        text = str(raw).lower()
        if "estimate" in text or "zestimate" in text:
            return None
        m = _RENT_RE.search(str(raw).replace(",", ""))
        if not m:
            return None
        try:
            value = float(m.group(1).replace(",", ""))
        except ValueError:
            return None
    if value <= 0:
        return None
    if value < _MIN_PLAUSIBLE or value > _MAX_PLAUSIBLE:
        return None
    return value
