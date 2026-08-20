# PromptOS Inbox

A Telegram bot that catches whatever you send it, from any device, and holds it until your
agent files it.

Standard library Python. No pip install, no dependencies, no build step.

## Why it runs all the time

The Telegram Bot API cannot read history, and it drops unfetched updates after roughly 24
hours. A collector that is asleep when you send something loses it permanently. So this runs
continuously and writes every message to disk the moment it arrives. Telegram sends a later
edit as `edited_message`, not `message`; the collector requests both update types and treats
the latest edited text or media caption as authoritative.

Edits update the matching queue item by both chat ID and message ID, so they do not create
duplicates. Editing an item that was already filed reopens it for review: the curator updates
the existing page and sends a fresh confirmation. If the collector missed the original while
offline but receives its edit, it saves that edit as a new pending item.

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

## Only one instance ever runs

At startup the bot binds `127.0.0.1:47921` as a mutex. A second copy finds the port taken,
logs `already running`, and exits.

This matters more than it looks. Two pollers sharing one token make Telegram answer
409 Conflict, the update offset races, and updates fetched by the losing copy are discarded
before they reach `inbox.json`. Messages disappear with no error anywhere, which is how a
user's follow-up remarks on a link went missing. With the lock in place, a watchdog relaunch
or an accidental second start is harmless.

Change the port with `lock_port` in the config if 47921 is taken on your machine.

## Keep it running at login

**Windows Task Scheduler (recommended).** Create a task that runs at logon and repeats every
five minutes. Use `powershell.exe` as the program and these arguments, replacing the example
folder with your inbox folder:

```text
-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\path\to\inbox\watchdog.ps1"
```

Set **Start in** to that same inbox folder. The watchdog resolves `bot.py` and `bot.log`
relative to its own location, reads `lock_port` from `config.json`, and defaults to `47921`.
It exits successfully when the Python collector owns the port. If another program owns the
port, it records the conflict and refuses to start a competing collector. Otherwise it starts
`bot.py` through `pythonw.exe` with a hidden window.

For the simpler Startup-folder option, open `shell:startup` and place a `.cmd` file there:

```bat
powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\path\to\inbox\watchdog.ps1"
```

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

Text-only messages are queued exactly like links, because a note or an idea is worth as much
as a URL. The processing side reads them and files them; see the triage rules in the skill.

After each filing run, your agent runs:

```bash
python confirm.py
```

Every account that submitted something gets a summary of what was filed. It is idempotent,
so running it twice sends nothing twice.

It also reports **silent skips**: items marked processed with no `filed_as`. Those left the
queue with no page and no confirmation, so nobody would learn they vanished. Commands are
excluded, since triggering one files nothing by design. A warning here means something was
dropped, and it is the check that would have caught an earlier URL-only drift.

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
| `lock_port` | Single-instance mutex port, default 47921 |

It messages every submitting account when a run starts, and messages them again if the run
fails. A silent scheduled failure destroys trust in a pipeline.

## Files

| File | Purpose |
| --- | --- |
| `bot.py` | The collector daemon |
| `watchdog.ps1` | Windows single-instance health check and hidden relaunch |
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
