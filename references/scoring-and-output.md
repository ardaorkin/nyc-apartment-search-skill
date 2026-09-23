# Ranking, risk checks, and output formats

## Ranking rubric (0–100)

Score only `ACTIVE` and `LIKELY_ACTIVE` listings.

| Dimension | Points |
| --- | --- |
| Location fit (matches the configured area if one is set, otherwise block quality/transit generally) | 20 |
| Value for rent | 20 |
| Layout / bedroom utility | 15 |
| Laundry, dishwasher, practical amenities | 15 |
| Pet friendliness | 10 |
| Fee structure (no-fee, low upfront cost) | 10 |
| Building quality / elevator / professional management | 5 |
| Listing freshness and confidence | 5 |

Preference order when comparing otherwise-similar units: 2-bedroom > unusually spacious or
compelling 1-bedroom; in-unit washer/dryer; dishwasher; elevator if above the 3rd floor; good
natural light; sane layout; no-fee or direct-management; clearly stated rent stabilization;
professionally managed building.

A single missing preference never disqualifies an otherwise good listing. While `max_rent` is
`null`, don't let the unknown budget dominate value scoring — score value relative to comparable
units in the same market (the configured area if one is set, otherwise the borough/neighborhood
the listing is actually in), and always record the top reasons behind a score in `score_reasons`.

## Risk checks

Flag and explain, don't accuse. Evidence-backed only.

Signals: below-market pricing with no explanation; money requested before a viewing or
application; wire-transfer or crypto request; landlord "overseas and unable to show the unit";
description copied from elsewhere; address mismatches; contact details inconsistent with the named
brokerage; passport / SSN / bank credentials / other sensitive data requested unusually early.

Levels: `LOW_RISK` (nothing notable), `REVIEW` (one soft signal — say which), `HIGH_RISK`
(multiple or severe signals). Each non-low level carries a one-line reason.

## Applicant-friendliness

This is an international relocation with continuing U.S.-company employment — that's the only
housing-relevant framing. Immigration status is never a search criterion and never appears in
output.

Flag requirements a transferee may need to plan around: U.S. credit score, SSN, U.S. tax returns,
U.S. landlord references, guarantor rules, income multiples, third-party guarantor acceptance
(e.g. Insurent/TheGuarantors), employer-letter acceptance, proof of employment. Where a listing
looks suitable but requirements might be an obstacle, add
`APPLICATION_REQUIREMENTS_NEED_CONFIRMATION`. Never assume the user lacks a given document.

## Outputs (every run)

### `reports/listings.csv`
One row per canonical apartment, rent prominent and sortable.

### `reports/listings.json`
Complete normalized records including `source_urls[]` and `observed_prices[]`.

### `reports/shortlist.md`

```markdown
# Best Current Matches

## [Address + Unit] — $X/month
- Bedrooms / bathrooms
- Active status
- Pet policy
- Laundry
- Dishwasher
- Elevator / floor
- Broker fee / no-fee
- Other mandatory fees
- Availability
- Why it is a good fit
- Concerns / missing information
- Questions to ask
- Direct clickable listing links

# Listings Requiring Follow-Up
# Stale / Off-Market Listings
# Rejected Listings
# Sources That Could Not Be Automatically Accessed
```

Rejected listings show the rejection reason. Follow-up covers anything carrying
`GEOGRAPHY_NEEDS_CONFIRMATION`, `PET POLICY NEEDS CONFIRMATION`,
`APPLICATION_REQUIREMENTS_NEED_CONFIRMATION`, or a `REVIEW`/`HIGH_RISK` level.

### `reports/changes.md`

Diff this run's snapshot against the previous one in `data/`. Tags: `NEW`, `PRICE_DROP`,
`PRICE_INCREASE`, `REMOVED`, `BACK_ON_MARKET`, `DETAIL_CHANGED` — each with previous and current
values. Watch rent, availability date, pet rules, broker fee, and listing status.

### Terminal summary

Sources searched · raw listings found · after geographic filtering · after pet filtering · after
dedupe · active or likely-active · top 10 ranked apartments. Name blocked sources explicitly.

## Message drafts (never sent)

Short, friendly, confident, natural, professional, not stiff. Open from `identity.intro` in
`config.yaml`. Include the cat only when the pet policy needs confirming, the listing asks about
pets, or it's otherwise relevant.

Never invent salary, credit score, savings, SSN, guarantor, rental history, lease length, or an
exact move-in date. Never mention visa or immigration details. Output the draft in chat for the
user to copy and send themselves.
