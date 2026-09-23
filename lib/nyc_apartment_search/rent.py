"""Rent parsing per references/data-model.md.

Never substitutes a Zestimate, historical price, or search-snippet number for
the current asking rent -- this only parses a value explicitly labeled as
the monthly rent by the caller.
"""

import re

_PLAUSIBLE_MIN = 100
_PLAUSIBLE_MAX = 50_000


def parse_rent(raw: str | None) -> int | None:
    """Parse a monthly-rent string into an int, or None if implausible/unparseable."""
    if not raw:
        return None
    digits_only = re.sub(r"[^\d]", "", raw)
    if not digits_only:
        return None
    value = int(digits_only)
    if not (_PLAUSIBLE_MIN <= value <= _PLAUSIBLE_MAX):
        return None
    return value
