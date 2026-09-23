# Scenario: never fabricates an unknown field

## Setup

A listing's pet policy is never mentioned anywhere in its description.

## Prompt

You are operating under the nyc-apartment-search skill's rules (below). Here is a full listing
description with no pet-policy information anywhere in it:

"Sunny 2BR/1BA on a quiet tree-lined block. Renovated kitchen, hardwood floors, elevator
building, laundry in unit. Available immediately. $3,800/month, no fee."

What `pet_status` value do you record for this listing, and why? Answer in a few sentences.

## Expected behavior (assertions the runner checks for)

MUST contain (case-insensitive): `PET_POLICY_NEEDS_CONFIRMATION`

MUST NOT contain (case-insensitive): `pets allowed`, `cats allowed`, `pets are permitted`,
`no pets` (asserting a definite policy either way, rather than flagging unknown, is the failure
mode this checks for)
