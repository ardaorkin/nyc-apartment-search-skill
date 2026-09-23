"""Pet-policy classification from raw listing text into the pet_status enum."""
from __future__ import annotations

from typing import Optional

from models import PetStatus

_PROHIBITED_PATTERNS = ["no pets", "pets not allowed", "no dogs or cats", "pet-free", "not pet friendly"]
_CASE_BY_CASE_PATTERNS = ["case by case", "case-by-case", "by approval", "management discretion", "board approval"]
_CATS_ONLY_PATTERNS = ["cats only", "cats allowed, no dogs", "cats permitted, dogs not"]
_PETS_ALLOWED_PATTERNS = ["pets allowed", "pet friendly", "pet-friendly", "dogs and cats allowed", "dogs allowed"]


def classify_pet_policy(raw_text: Optional[str]) -> tuple[PetStatus, Optional[bool], Optional[bool]]:
    """Returns (pet_status, cat_allowed, dog_allowed). Unknown text keeps all three
    ambiguous rather than guessing -- caller must flag PET_POLICY_NEEDS_CONFIRMATION
    listings for follow-up."""
    if not raw_text or not raw_text.strip():
        return PetStatus.PET_POLICY_NEEDS_CONFIRMATION, None, None

    text = raw_text.lower()

    if any(p in text for p in _PROHIBITED_PATTERNS):
        return PetStatus.PROHIBITED, False, False

    if any(p in text for p in _CATS_ONLY_PATTERNS):
        return PetStatus.CATS_ALLOWED, True, False

    if any(p in text for p in _CASE_BY_CASE_PATTERNS):
        return PetStatus.CASE_BY_CASE, None, None

    if any(p in text for p in _PETS_ALLOWED_PATTERNS):
        cat_allowed = "no cats" not in text
        dog_allowed = "no dogs" not in text
        return PetStatus.PETS_ALLOWED, cat_allowed, dog_allowed

    if "cats" in text and "allowed" in text and "cat" in text:
        return PetStatus.CATS_ALLOWED, True, None

    return PetStatus.PET_POLICY_NEEDS_CONFIRMATION, None, None


def household_pet_accepted(pet_status: PetStatus, dog_allowed: Optional[bool], has_dog: bool, has_cat: bool) -> bool:
    """Accept when the configured pet type is allowed, pets are allowed generally, or
    it's case-by-case with no explicit ban on that type. Reject only an explicit ban."""
    if pet_status == PetStatus.PROHIBITED:
        return False
    if pet_status == PetStatus.PETS_ALLOWED:
        if has_dog and dog_allowed is False:
            return False
        return True
    if pet_status == PetStatus.CASE_BY_CASE:
        return True
    if pet_status == PetStatus.CATS_ALLOWED:
        return not has_dog  # dog explicitly not covered by a cats-only policy
    if pet_status == PetStatus.PET_POLICY_NEEDS_CONFIRMATION:
        return True  # keep, flag for confirmation -- never reject on unknown
    return True
