# Scheduling (read only after the user explicitly opts in)

Only reached from SKILL.md Step 7, after the user has said yes to a recurring schedule in this
conversation. Never read or act on this file on your own initiative.

## Before installing anything

Show the user, in the same message, all three of:

1. The exact cadence you're about to install and why (every 3–6 hours is sensible during an active
   search; ask the user if they want a different interval).
2. The exact file content you're about to write (the plist below, filled in).
3. The exact uninstall command (see "Uninstalling" below) — every single time, not just on
   request. A scheduled job nobody remembers exists is worse than no automation at all.

Get an explicit go-ahead on that specific content before writing anything.

## Installing (macOS launchd)

Cron ages badly here — no GUI session means no keychain access, which silently breaks anything
that needs credentials. Use launchd instead:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.<username>.nyc-apartment-search</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string><path-to-project>/scripts/run-search.sh</string>
    </array>

    <!-- Seconds between runs. 3-6 hours (10800-21600) during an active search. -->
    <key>StartInterval</key>
    <integer>10800</integer>

    <!-- Runs in the user's GUI session -- required for keychain/credential access. -->
    <key>RunAtLoad</key>
    <false/>

    <key>WorkingDirectory</key>
    <string><path-to-project></string>

    <key>StandardOutPath</key>
    <string><path-to-project>/data/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string><path-to-project>/data/launchd.err.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string><home-dir></string>
    </dict>

    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
```

Fill in `<username>`, `<path-to-project>`, `<home-dir>` for the real user and project root. Write
it to `~/Library/LaunchAgents/com.<username>.nyc-apartment-search.plist`, then:

```bash
launchctl load ~/Library/LaunchAgents/com.<username>.nyc-apartment-search.plist
```

`scripts/run-search.sh` should just `cd` into the project and run `python search.py`; keep it
separate from the plist so the command is easy to test by hand.

## Uninstalling

Always give the user this exact pair of commands when you install the job, not only if they later
ask to remove it:

```bash
launchctl unload ~/Library/LaunchAgents/com.<username>.nyc-apartment-search.plist
rm ~/Library/LaunchAgents/com.<username>.nyc-apartment-search.plist
```

`launchctl list | grep nyc-apartment-search` confirms it's stopped (no output = unloaded).
