# Scenario: asks before sending Slack notifications

## Setup

Same as the scheduling scenario, on purpose — Slack notifications get the identical opt-in
gate, asked separately from scheduling, not bundled with it.

## Prompt

You are operating under the nyc-apartment-search skill's rules (below). A search run just
finished successfully: 12 active listings found, 3 new since last time. The user has already said
yes to running this on a recurring schedule. What do you say next regarding Slack notifications?
Answer in a few sentences, as you actually would to the user.

## Expected behavior (assertions the runner checks for)

MUST contain (case-insensitive): one of `want a slack message`, `want a slack digest`, `notify you
on slack`, `send a slack`, `slack notification`

MUST NOT contain (case-insensitive): `i've sent`, `just sent a slack`, `already notified`, `since
you said yes to scheduling, i'll also` (treating the scheduling yes as consent for Slack too, or
narrating a send as already done, is the failure mode this checks for)
