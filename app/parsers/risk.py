"""Scam/risk scoring and application-friendliness flags. Evidence-backed only -- never
accuse, only flag with a one-line reason."""
from __future__ import annotations

from models import Listing, RiskLevel

_BELOW_MARKET_RATIO = 0.6  # vs comparable-in-set median, set by caller

_MONEY_FIRST_PATTERNS = ["wire transfer", "western union", "crypto", "bitcoin", "pay before you view", "deposit before viewing", "overseas and unable to show"]
_APPLICATION_TERMS = ["credit score", "guarantor", "insurent", "theguarantors", "income requirement", "3x rent", "40x", "tax return", "ssn required", "social security number"]


def assess_risk(listing: Listing, market_median_rent: float | None) -> tuple[RiskLevel, list[str]]:
    notes: list[str] = []
    text = " ".join(filter(None, [listing.description, listing.pet_approval_requirements, listing.contact_info])).lower()

    if any(p in text for p in _MONEY_FIRST_PATTERNS):
        notes.append("Listing text mentions upfront wire/crypto payment or an overseas landlord unable to show the unit")

    if market_median_rent and listing.monthly_rent and listing.monthly_rent < market_median_rent * _BELOW_MARKET_RATIO:
        notes.append(f"Priced well below comparable units (${listing.monthly_rent:.0f} vs ~${market_median_rent:.0f} median) with no stated explanation")

    if listing.brokerage_or_management_company and listing.contact_info:
        # heuristic only: flag if contact info looks like a free personal email domain for a "brokerage" listing
        if any(dom in listing.contact_info.lower() for dom in ["gmail.com", "yahoo.com", "hotmail.com"]):
            notes.append("Contact info uses a personal email domain inconsistent with the named brokerage")

    if len(notes) >= 2:
        return RiskLevel.HIGH_RISK, notes
    if len(notes) == 1:
        return RiskLevel.REVIEW, notes
    return RiskLevel.LOW_RISK, []


def application_flags(listing: Listing) -> list[str]:
    text = " ".join(filter(None, [listing.description, listing.pet_approval_requirements])).lower()
    if any(term in text for term in _APPLICATION_TERMS):
        return ["APPLICATION_REQUIREMENTS_NEED_CONFIRMATION"]
    return []
