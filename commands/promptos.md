---
description: Set up PromptOS — connect a knowledge base (GitBook) and a materials inbox (Telegram). Every credential is revokable.
---

# /promptos — first-run setup

You are setting up **PromptOS** for this user with whatever agent is running you. Load the
`promptos-curator` skill (`skills/promptos-curator/SKILL.md`) — it holds the full pipeline.
Your only job in THIS command is to establish the two connections, using **revokable**
credentials, then confirm the pipeline is ready. Do not process anything yet.

Never assume platforms or credentials. Check what already exists; ask only for what's missing,
in one message, with where to get each item and how to revoke it.

## 1. Knowledge base (where pages are filed)

Default and recommendation: **a Git repo as source of truth + GitBook two-way Git Sync**
(history, recoverability, safe concurrent human+AI editing). Notion / Obsidian / MkDocs are
supported alternatives — offer them if the user is undecided.

Request, with revocation stated up front:
- **GitBook API token** — app.gitbook.com → Developer settings. **Revoke anytime** there.
- **GitHub PAT** (`repo` scope) for the synced repo — github.com/settings/tokens.
  **Revoke anytime** there. Prefer a fine-grained, short-lived token scoped to the one repo.

Configure **two-way sync** (never one-way force-import over the user's manual edits). Verify a
test write renders on GitBook before moving on.

## 2. Materials inbox (how links reach the base)

Default and recommendation: **a Telegram bot** (official Bot API, token-only, multi-device,
replies with confirmations, supports owner-only `/cleanup`). Plain chat-paste works with zero
setup as a fallback.

Request, with revocation stated up front:
- **Telegram bot token** — create the bot in 60s via **@BotFather**. **Revoke anytime** with
  BotFather `/revoke` (it issues a fresh token and kills the old one).
- **Approved accounts allowlist** — each account the user will send from says "Hi" to the bot
  once; you record their chat IDs. Only allowlisted accounts are accepted. **Remove any account
  from the allowlist at any time.**

Stand up a durable local queue that captures messages the moment they arrive (Telegram only
retains unfetched updates ~24h), a watchdog that keeps the capture daemon alive and self-repairs
its config, and a `confirm` step that replies "done" to each submitting account after a run.

## 3. Confirm ready

Report back: knowledge base connected (repo + GitBook sync verified), inbox connected (bot live,
N approved accounts), and that the user can now forward links anytime and run **`/promptos:process`**
whenever they want them filed. Remind them: every token above is revokable, and nothing they
pasted is permanent.
