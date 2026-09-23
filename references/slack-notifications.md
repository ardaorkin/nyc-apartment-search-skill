# Slack notifications (read only after the user explicitly opts in)

Only reached from SKILL.md Step 7, after the user has said yes to Slack notifications in this
conversation, separately from any scheduling opt-in. Never read or act on this file on your own
initiative.

## Hard limits (in addition to the skill's global hard rules)

- **Self-DM only.** The message goes to the user's own Slack account, never a channel, never
  another person, never a Slack Connect / external channel. Confirm the exact destination with
  the user before the first send.
- **One message per run, maximum.** Never send incremental progress messages or retries as
  separate messages.
- **Only report what changed.** If nothing changed since the last run, either skip the message
  entirely or send a single short "no changes" line — don't resend the full shortlist every time.
- Whatever tool sends the message (an installed Slack MCP server, a CLI, etc.) varies by
  environment — check what's available rather than assuming a specific tool name.

## Before sending anything

Show the user the exact destination (their own account) and the exact message format below
before the first send, and get an explicit go-ahead.

## Message format

One message per run, bulleted, sorted by rent, only listings that are `ACTIVE` or `LIKELY_ACTIVE`:

```
:clipboard: *UES 2BR watchlist* — N tracked under $X · cheapest $Y

• *$3,760* — <https://example.com/listing|343 E 85th St #3R> · ~Yorkville
• *$3,800* — <https://example.com/listing|1601 York Ave #3B> · ~Yorkville

_Full list in shortlist.md. Pet policy unconfirmed throughout — ask before viewing._
```

Use `label`, `url`, `monthly_rent`, and `where` verbatim from the report — never invent, round, or
re-derive a value, and never add a listing that isn't in `reports/shortlist.md`.

## Uninstalling / turning off

There's nothing to uninstall in the scheduling sense — turning this off just means not sending the
next message. Tell the user, every time you turn it on, that they can say "stop the Slack
notifications" at any point and this step is simply skipped on the next run onward. If notifications
are wired into a scheduled job (`references/scheduling.md`), turning off *sending* doesn't stop the
*schedule* — mention both independently so the user isn't surprised the job still runs quietly with
no output.
