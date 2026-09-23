"""Shared Listing data model. See references/data-model.md in the skill for the spec this
implements. Every field defaults to None -- nothing here is ever guessed."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GeoStatus(str, Enum):
    IN_RANGE = "IN_RANGE"
    GEOGRAPHY_NEEDS_CONFIRMATION = "GEOGRAPHY_NEEDS_CONFIRMATION"
    OUT_OF_RANGE = "OUT_OF_RANGE"


class PetStatus(str, Enum):
    CATS_ALLOWED = "CATS_ALLOWED"
    PETS_ALLOWED = "PETS_ALLOWED"
    CASE_BY_CASE = "CASE_BY_CASE"
    PET_POLICY_NEEDS_CONFIRMATION = "PET_POLICY_NEEDS_CONFIRMATION"
    PROHIBITED = "PROHIBITED"


class ActiveStatus(str, Enum):
    ACTIVE = "ACTIVE"
    LIKELY_ACTIVE = "LIKELY_ACTIVE"
    UNCERTAIN = "UNCERTAIN"
    STALE = "STALE"
    OFF_MARKET = "OFF_MARKET"


class RiskLevel(str, Enum):
    LOW_RISK = "LOW_RISK"
    REVIEW = "REVIEW"
    HIGH_RISK = "HIGH_RISK"


class SourceStatus(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    BLOCKED_OR_MANUAL_REVIEW_REQUIRED = "BLOCKED_OR_MANUAL_REVIEW_REQUIRED"
    ERROR = "ERROR"


class ObservedPrice(BaseModel):
    value: float
    source: str
    observed_at: datetime


class Listing(BaseModel):
    # Provenance
    source: str
    source_listing_id: Optional[str] = None
    listing_url: Optional[str] = None
    source_urls: list[str] = Field(default_factory=list)
    first_seen: Optional[date] = None
    last_seen: Optional[date] = None
    source_last_updated: Optional[str] = None
    checked_at: Optional[datetime] = None

    # Location
    address: Optional[str] = None
    unit: Optional[str] = None
    neighborhood: Optional[str] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    cross_streets: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geo_status: Optional[GeoStatus] = None

    # Price and fees
    monthly_rent: Optional[float] = None
    observed_prices: list[ObservedPrice] = Field(default_factory=list)
    broker_fee_status: Optional[str] = None
    broker_fee_amount: Optional[float] = None
    application_fee: Optional[float] = None
    security_deposit: Optional[float] = None
    amenity_fees: Optional[str] = None
    rent_stabilized: Optional[bool] = None
    net_effective_rent: Optional[float] = None

    # Unit
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[float] = None
    floor: Optional[str] = None
    available_date: Optional[str] = None
    lease_term: Optional[str] = None
    furnished: Optional[bool] = None
    description: Optional[str] = None

    # Amenities
    laundry: Optional[str] = None
    in_unit_washer_dryer: Optional[bool] = None
    dishwasher: Optional[bool] = None
    elevator: Optional[bool] = None
    doorman: Optional[bool] = None
    virtual_doorman: Optional[bool] = None
    gym: Optional[bool] = None
    outdoor_space: Optional[bool] = None
    air_conditioning: Optional[bool] = None

    # Pets
    pet_policy: Optional[str] = None
    cat_allowed: Optional[bool] = None
    dog_allowed: Optional[bool] = None
    pet_fee: Optional[float] = None
    pet_deposit: Optional[float] = None
    monthly_pet_rent: Optional[float] = None
    pet_approval_requirements: Optional[str] = None
    pet_status: Optional[PetStatus] = None

    # Contacts
    listing_agent: Optional[str] = None
    brokerage_or_management_company: Optional[str] = None
    contact_info: Optional[str] = None

    # Status and assessment
    active_status: Optional[ActiveStatus] = None
    days_on_market: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    risk_notes: list[str] = Field(default_factory=list)
    application_flags: list[str] = Field(default_factory=list)
    score: Optional[int] = None
    score_reasons: list[str] = Field(default_factory=list)
    confidence_notes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class SourceResult(BaseModel):
    """What a source adapter returns: listings plus its own outcome status."""

    name: str
    status: SourceStatus
    listings: list[Listing] = Field(default_factory=list)
    note: Optional[str] = None
