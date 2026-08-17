# PromptOS Inbox

A Telegram bot that catches whatever you send it, from any device, and holds it until your
agent files it.

Standard library Python. No pip install, no dependencies, no build step.

## Why it runs all the time

The Telegram Bot API cannot read history, and it drops unfetched updates after roughly 24
hours. A collector that is asleep when you send something loses it permanently. So this runs
continuously and writes every message to disk the moment it arrives.

## Setup

**1. Create the bot.** Message **@BotFather** on Telegram, send `/newbot`, follow two
prompts, copy the token it gives you. About sixty seconds.

**2. Configure.**

```bash
cp config.example.json config.json
```

Open `config.json`, paste the token, and set `enroll_remaining` to how many accounts you
want to approve. Set it to `2` if you will send from a phone and a laptop.

**3. Start it.**

```bash
python bot.py
```

**4. Enrol your accounts.** From each device, send the bot any message while the enrolment
window is open. It replies `done ✅` and adds that account. The window closes itself once
the slots are used.

**5. Test.** Send a link from your phone and confirm it appears in `inbox.json`.

## Keep it running at login

**Windows.** Put a one line `.cmd` file in the Startup folder
(`Win+R` → `shell:startup`):

```bat
pythonw "C:\path\to\inbox\bot.py"
```

`pythonw` runs it without a console window.

**macOS.** Create `~/Library/LaunchAgents/com.promptos.inbox.plist` with a `ProgramArguments`
array of your python path and the script path, `RunAtLoad` set to true, then
`launchctl load` it.

**Linux.** A user systemd unit at `~/.config/systemd/user/promptos-inbox.service` with
`Restart=always`, then `systemctl --user enable --now promptos-inbox`.

## Commands in the chat

| Command | What it does |
| --- | --- |
| `/help` | What the bot is and how to use it |
| `/cleanup` | Deletes messages already filed, and only those |
| any message | Queued for the next run |
| a message naming your base | Queued, and flagged for processing |

`/cleanup` deletes only items marked processed, using each message's own chat ID so several
approved accounts work. Telegram allows bots to delete messages under 48 hours old, so
anything older is reported for you to remove by hand.

## Confirmations

After each filing run, your agent runs:

```bash
python confirm.py
```

Every account that submitted something gets a summary of what was filed. It is idempotent,
so running it twice sends nothing twice.

## Scheduled runs, optional

Off by default. Set `auto_hour` in the config to an hour of the day and the bot spawns a
headless processing run after that hour, once per day, only when the queue has unprocessed
items.

| Key | Meaning |
| --- | --- |
| `auto_hour` | Hour of day to run, `0` keeps it off |
| `base_dir` | Folder your knowledge base lives in |
| `agent_path` | Path to your agent CLI |
| `auto_prompt` | What to tell the agent |

It messages every submitting account when a run starts, and messages them again if the run
fails. A silent scheduled failure destroys trust in a pipeline.

## Files

| File | Purpose |
| --- | --- |
| `bot.py` | The collector daemon |
| `confirm.py` | Per account replies after a run |
| `config.json` | Your token and settings. **Never commit this.** |
| `inbox.json` | The queue |
| `bot.log` | What the daemon did |
| `auto_run.log` | Output from scheduled runs |

## Privacy

Everything stays on your machine. The bot talks to Telegram and to nothing else. Only
accounts you enrolled are accepted, and messages from anyone else are ignored in silence.

Revoke the token any time with @BotFather `/revoke`. It issues a fresh one and kills the old
one immediately.
