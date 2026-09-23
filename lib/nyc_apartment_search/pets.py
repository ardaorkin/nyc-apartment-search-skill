"""Pet-policy classification per references/data-model.md's pet_status enum.

Reject only an explicit cat/all-pet ban. Unknown text is kept and flagged for
confirmation, never coerced to a guess.
"""

from typing import Literal

PetStatus = Literal[
    "CATS_ALLOWED",
    "PETS_ALLOWED",
    "CASE_BY_CASE",
    "PET_POLICY_NEEDS_CONFIRMATION",
    "PROHIBITED",
]

_PROHIBITED_MARKERS = ("no pets", "no cats", "pets not allowed", "pet-free")
_CASE_BY_CASE_MARKERS = ("case by case", "case-by-case", "by request", "ask about pets")
_CATS_MARKERS = ("cats allowed", "cats ok", "cat friendly", "cat-friendly")
_PETS_MARKERS = ("pets allowed", "pet friendly", "pet-friendly", "pets ok")


def classify_pet_policy(raw_text: str | None) -> PetStatus:
    if not raw_text:
        return "PET_POLICY_NEEDS_CONFIRMATION"
    text = raw_text.lower()

    if any(marker in text for marker in _PROHIBITED_MARKERS):
        return "PROHIBITED"
    if any(marker in text for marker in _CATS_MARKERS):
        return "CATS_ALLOWED"
    if any(marker in text for marker in _PETS_MARKERS):
        return "PETS_ALLOWED"
    if any(marker in text for marker in _CASE_BY_CASE_MARKERS):
        return "CASE_BY_CASE"
    return "PET_POLICY_NEEDS_CONFIRMATION"
