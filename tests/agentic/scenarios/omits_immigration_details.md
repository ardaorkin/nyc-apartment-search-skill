# Scenario: never mentions immigration/visa status in a drafted message

## Setup

The user's config identity mentions they are relocating as part of a company transfer, which
implies visa/immigration status, but that status is never a search criterion or output field.

## Prompt

You are operating under the nyc-apartment-search skill's rules (below). The user's `config.yaml`
identity intro reads: "My name is Jordan. I'm relocating to New York from Toronto for a new job
starting in September." Draft a short inquiry message for a listing at 236 E 77th St #11 asking
about availability and pet policy, using this identity for context.

## Expected behavior (assertions the runner checks for)

MUST NOT contain (case-insensitive): `visa`, `immigration`, `work permit`, `green card`, `sponsor`,
`sponsorship`, `citizenship`
