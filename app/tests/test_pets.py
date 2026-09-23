import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import PetStatus
from parsers.pets import classify_pet_policy, household_pet_accepted


def test_no_pets_text():
    status, cat, dog = classify_pet_policy("No pets allowed in this building.")
    assert status == PetStatus.PROHIBITED
    assert cat is False and dog is False


def test_pets_allowed_text():
    status, cat, dog = classify_pet_policy("Pets allowed, dogs and cats welcome.")
    assert status == PetStatus.PETS_ALLOWED
    assert cat is True and dog is True


def test_case_by_case_text():
    status, _, _ = classify_pet_policy("Pets considered case by case with board approval.")
    assert status == PetStatus.CASE_BY_CASE


def test_missing_text_needs_confirmation():
    status, cat, dog = classify_pet_policy(None)
    assert status == PetStatus.PET_POLICY_NEEDS_CONFIRMATION
    assert cat is None and dog is None


def test_household_dog_rejected_on_prohibited():
    assert household_pet_accepted(PetStatus.PROHIBITED, False, has_dog=True, has_cat=False) is False


def test_household_dog_accepted_on_pets_allowed():
    assert household_pet_accepted(PetStatus.PETS_ALLOWED, True, has_dog=True, has_cat=False) is True


def test_household_dog_kept_on_unknown_policy():
    assert household_pet_accepted(PetStatus.PET_POLICY_NEEDS_CONFIRMATION, None, has_dog=True, has_cat=False) is True


def test_cats_only_policy_rejects_dog_household():
    assert household_pet_accepted(PetStatus.CATS_ALLOWED, False, has_dog=True, has_cat=False) is False
