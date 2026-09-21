# Listing data model

One `Listing` record per **canonical apartment** (post-dedupe). Every field below must exist on the
record; anything not confirmed from the source is `null`, never a guess, never an inferred default.
Explain each `null` that matters in `confidence_notes`.

## Fields

### Provenance
| Field | Notes |
| --- | --- |
| `source` | Site/company the record came from |
| `source_listing_id` | Native ID on that site |
| `listing_url` | Direct link to the listing page |
| `source_urls[]` | Every URL this apartment was seen at, across all sources |
| `first_seen` | First run that saw it |
| `last_seen` | Most recent run that saw it |
| `source_last_updated` | If the site exposes it |
| `checked_at` | Timestamp of this fetch |

### Location
`address`, `unit`, `neighborhood`, `street_number`, `street_name`, `cross_streets`,
`latitude`, `longitude`, `geo_status`

`geo_status` ∈ `IN_RANGE` | `GEOGRAPHY_NEEDS_CONFIRMATION` | `OUT_OF_RANGE`

### Price and fees
`monthly_rent`, `observed_prices[]` (value + source + timestamp), `broker_fee_status`,
`broker_fee_amount`, `application_fee`, `security_deposit`, `amenity_fees`, `rent_stabilized`,
`net_effective_rent` (only if the source says so explicitly — otherwise `null`)

### Unit
`bedrooms`, `bathrooms`, `square_feet`, `floor`, `available_date`, `lease_term`, `furnished`,
`description`

### Amenities
`laundry`, `in_unit_washer_dryer`, `dishwasher`, `elevator`, `doorman`, `virtual_doorman`, `gym`,
`outdoor_space`, `air_conditioning`

### Pets
`pet_policy` (raw text), `cat_allowed`, `pet_fee`, `pet_deposit`, `monthly_pet_rent`,
`pet_approval_requirements`, `pet_status`

`pet_status` ∈ `CATS_ALLOWED` | `PETS_ALLOWED` | `CASE_BY_CASE` | `PET_POLICY_NEEDS_CONFIRMATION` | `PROHIBITED`

### Contacts
`listing_agent`, `brokerage_or_management_company`, `contact_info` (only if publicly listed)

### Status and assessment
| Field | Values |
| --- | --- |
| `active_status` | `ACTIVE` \| `LIKELY_ACTIVE` \| `UNCERTAIN` \| `STALE` \| `OFF_MARKET` |
| `days_on_market` | integer or `null` |
| `risk_level` | `LOW_RISK` \| `REVIEW` \| `HIGH_RISK` |
| `risk_notes` | one line of evidence per flag |
| `application_flags[]` | e.g. `APPLICATION_REQUIREMENTS_NEED_CONFIRMATION` |
| `score` | 0–100, active / likely-active only |
| `score_reasons[]` | top drivers of the score |
| `confidence_notes` | free text: what's unverified and why |

## Parsing rules

- Rent: strip currency/commas, reject values that aren't plausibly monthly rent, and never
  substitute a Zestimate, "rent estimate", historical price, or search-snippet number.
- If a source shows net-effective rent, store gross where available and note the concession
  rather than silently recording the lower figure.
- Address normalization: expand/standardize `E`/`East`, `St`/`Street`, `Ave`/`Avenue`, ordinal
  suffixes, and unit designators before comparing addresses.
- Booleans are three-state: `true`, `false`, `null` (unknown). Never coerce unknown to `false`.
