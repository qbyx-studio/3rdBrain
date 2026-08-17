# Platform setup

Where the base lives, how materials reach it, and how to put it online later.

## Table of contents

1. Where the base lives
2. Local base, the reference implementation
3. Other places a base can live
4. Materials inbox, options and recommendation
5. Telegram bot inbox, the reference implementation
6. Other input channels
7. Publishing
8. Scheduled processing
9. Credential checklist

---

## 1. Where the base lives

**Default: a folder on the user's own computer, rendered by MkDocs.**

It wins on the thing that decides adoption. Setup finishes with zero accounts, zero tokens,
zero cost, and nothing leaving the machine. The user sees their own base in a browser
minutes after starting, and their notes stay private by construction.

A local git repository comes with it, giving history and an undo button with no remote and
no GitHub account.

Going online is its own decision, made later, with its own warning. Section 7 covers it.

## 2. Local base, the reference implementation

```
knowledge-base/
├── README.md            ← landing page
├── SUMMARY.md           ← the sidebar
├── general/  coding/ …  ← content, one folder per topic
├── .assets/             ← images
└── _site/               ← the build, the theme, the tests
```

Steps:

1. **Check Python 3.10+ and git.** Install what is missing, or hand the user one link and
   wait. One sentence on why it is needed.
2. **Create the folder and the starter files.** `SUMMARY.md` holds the sidebar as a Markdown
   list with `## Headings` for sections.
3. **Copy `_site/` from this repo.** Dependencies are pinned there.
4. **`git init` and commit.** History from day one.
5. **Build and open.** `cd _site && VAULT=.. bash build.sh`, then serve and open the browser.

The build never writes to the content. Every transform runs against a throwaway copy, and a
test enforces it. See `references/site-build.md`.

## 3. Other places a base can live

Offer these when the user asks for them. Each adds an account, so the local default stands
unless the user chooses otherwise.

| Option | What it adds | What it costs |
| --- | --- | --- |
| **GitBook + two way git sync** | A polished editor, a hosted reading UI, comments | A GitBook account and a GitHub account, two tokens, and a paid plan for private team access |
| **Notion** | Familiar editor, easy sharing | An account, a lossy import, and the loss of git as source of truth |
| **Obsidian** | Local files, strong editing, graph view | Desktop app per person, and sharing needs git or a paid sync |
| **Outline, BookStack, Wiki.js** | Team features, permissions | A server to run and maintain |

The page block syntax renders in both MkDocs and GitBook, so a base can move between them
without rewriting pages.

## 4. Materials inbox, options and recommendation

**Default: a Telegram bot.** Saving happens on a phone, in the moment, hours before any
processing. An inbox that lives on the phone is the difference between a base that grows and
a base that stalls.

| Option | Setup | Best for |
| --- | --- | --- |
| **Telegram bot** | About 60 seconds through @BotFather | Everyone who saves from a phone |
| **Plain chat paste** | None | Starting today, adding a bot later |
| Email inbox | Mailbox plus credentials | People who forward by mail |
| Notion or Sheet inbox page | An account | Teams already living there |
| WhatsApp bridge | Unofficial client | Last resort; re-pairing and ban risk |

Whatever the channel: capture into a durable local queue the moment a message arrives,
because Telegram keeps unfetched updates for about 24 hours. Restrict it to an allowlist of
the user's own accounts. Confirm each processed item back to whoever sent it.

## 5. Telegram bot inbox, the reference implementation

Working code ships in `inbox/`. Copy it, do not rewrite it. The hard parts are already
solved and each one was learned in production.

```
inbox/
├── bot.py                 ← the collector daemon
├── confirm.py             ← per account "done" replies after a run
├── config.example.json    ← copy to config.json, add the token
└── README.md              ← install and autostart, per platform
```

Setup:

1. The user creates the bot with **@BotFather → /newbot** and pastes the token.
2. Copy `bot.py`, `confirm.py` and `config.example.json` into the base folder.
3. Write `config.json` with the token and `enroll_remaining` set to the number of accounts
   to approve. Never commit this file.
4. Start the bot, and set it to run at login so capture never sleeps.
5. Each account sends one message during the enrolment window and is added to `owners`.
   Confirm the enrolled accounts with the user afterwards.
6. Have the user send a link from their phone and confirm it lands in `inbox.json`.

What the daemon already handles:

- **Durable capture.** Every message is written to `inbox.json` immediately.
- **Allowlist with an enrolment window.** Accounts outside the list are ignored silently.
- **A trigger phrase.** A message mentioning the base name flags the queue for processing.
- **`/cleanup`.** Deletes only items already marked processed, using each message's own chat
  ID so multiple accounts work. Telegram allows bots to delete messages under 48 hours old,
  so it reports the older remainder for manual deletion.
- **`/help`.**
- **Self healing.** An unhandled exception restarts the loop, so capture continues.

After each filing run, `confirm.py` sends every submitting account a summary of what was
filed. It is idempotent, so running it twice sends nothing twice. Silent failures destroy
trust in a pipeline, so failures message the user too.

## 6. Other input channels

Plain chat paste needs nothing: the user pastes links into the conversation and processing
begins. It is the right start for someone who wants to see value before creating anything.

Email, Notion pages and spreadsheets all work as queues. Keep the same contract: durable
capture, an allowlist, and a confirmation back to the sender.

## 7. Publishing

Local first, online by choice. `commands/publish.md` holds the full procedure. The shape:

1. **Consent.** State plainly that the notes are going onto the internet, and wait.
2. **Ask who gets in.** An email allowlist behind a sign in screen, or an open link.
3. **Deploy** to Cloudflare Pages, free, with one API token.
4. **Verify from outside** and report exactly what a stranger sees.

One structural detail decides the whole design: Cloudflare cannot put a login wall on a
Pages **production** address, and can on **preview** addresses. Setting the production branch
to one that never exists leaves the public address empty and makes every deploy protectable.

## 8. Scheduled processing

Offer it, keep it off by default. A daily run that fires while the user sleeps is useful
once the pipeline is trusted, and confusing before then.

The bot supports it: set `auto_hour` in the config and it spawns a headless processing run
after that hour, once a day, only when the queue has unprocessed items. It messages every
submitting account when a run starts, and messages them again if the run fails.

A publish hook can follow the same pattern, republishing after each filing run.

## 9. Credential checklist

Local setup asks for nothing. Everything below is optional, and every item is revokable.

| Item | Where to get it | How to revoke |
| --- | --- | --- |
| Telegram bot token | @BotFather → `/newbot` | @BotFather → `/revoke` |
| Cloudflare API token | dash.cloudflare.com → My Profile → API Tokens | Same page |
| GitBook API token | app.gitbook.com → Developer settings | Same page |
| GitHub PAT | github.com/settings/tokens | Same page |

State the revocation path at the moment you ask for the credential, and keep every secret
out of files that git tracks.
