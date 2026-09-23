# First-Time Setup

Creates `config.yaml` when it doesn't exist. Read this file only when `config.yaml` is missing.

New York City is the one fixed setting — it's not asked about and not written as a question
answer, because it's not a choice; this skill only ever searches NYC. Everything else below
starts with no default and is asked, but every question is skippable — an unanswered question
just leaves that field `null` ("no preference" / "no restriction"), never a guessed value.

## Steps

1. Ask the user one question at a time, always — never batch these into a single message, even
   though every one of them is individually optional. Wait for a reply (or "skip") before asking
   the next one:
   - **Area** — optional. "Which part of NYC — a neighborhood, a borough, or a street range?
     Or say 'all boroughs' / 'no preference' for a citywide search." Blank or "no preference" →
     all location fields stay `null` (citywide, no geographic filter).
   - **Household** — optional. "How many adults, and any pets?"
   - **Bedrooms** — optional. "Preferred and minimum bedroom count?"
   - **Budget** — optional. "Max monthly rent?"
   - **Move timing** — optional. "Target move-in date, and how flexible are you on it?"
   - **Preferences** — optional. "Any must-haves or nice-to-haves? (in-unit laundry, dishwasher,
     elevator/floor, no-fee, rent-stabilized, etc.)"
   - **Identity intro** — optional. "A short intro for drafted inquiry messages — your name and
     one line of context. Only used for message drafts; the tool never sends anything itself."
2. Nothing here is required. If the user skips everything, still create the config — every
   field below `city` is `null`, which is a completely valid, working configuration (citywide,
   no budget cap, no bedroom preference, no household details, no drafted-message intro until
   they're set later).
3. Write `~/nyc-apartment-search/config.yaml` following `assets/config.yaml`'s structure exactly
   — copy that file, then fill in only what the user answered; leave the rest `null`.
4. Tell the user: "Config saved at `~/nyc-apartment-search/config.yaml`. Everything you just set
   (or skipped) can be changed anytime — just tell me, e.g. 'set my max rent to $4,000' or
   'search all of Brooklyn now' — no need to redo this setup."
5. Return to Step 1 to continue.
