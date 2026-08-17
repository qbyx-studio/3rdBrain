---
description: Set up PromptOS on this computer. Builds your knowledge base locally, connects a materials inbox, opens it in your browser. No accounts needed.
---

# /promptos, first run setup

You are setting up **PromptOS** for this user. Load the `promptos-curator` skill
(`skills/promptos-curator/SKILL.md`); it holds the pipeline. This command builds the base
and connects the inbox. Process nothing yet.

**Assume the user has never opened a terminal.** You run every command. They answer
questions, paste a token when asked, and click a link at the end. Explain what you are doing
in plain words, and translate any error into plain words too.

## 1. The base lives on this computer

Default and recommendation: **a folder on their disk, rendered by MkDocs**. Setup finishes
with zero accounts, zero tokens, zero cost, and nothing leaving the machine. Publishing is a
separate, later choice covered by `/promptos:publish`.

Ask one question: **where should the base live?** Offer a sensible default such as
`~/PromptOS` or `C:\PromptOS`. Then do the work:

1. **Check the tools.** Python 3.10 or newer, and git. If either is missing, install it, or
   give the user the one link they need and wait. Say why it is needed in one sentence.
2. **Copy the starter and the machinery.** `_site/starter/` holds a working base:
   `README.md`, `SUMMARY.md`, `tool-index.md` and one example page. Copy its contents to the
   base folder, add an `.assets/` folder, then copy `_site/` itself alongside them and delete
   the nested `_site/starter`. Copy these files, do not improvise them; the starter's
   `SUMMARY.md` already wires up the generated facet hubs.
3. **Create a local git repository** and make the first commit. This gives history and an
   undo button. No remote, no GitHub account.
4. **Build it.** `cd _site && VAULT=.. bash build.sh`. The first run creates the virtual
   environment and installs the pinned dependencies.
5. **Serve and open it.** Start `mkdocs serve` and open the browser at the address. If the
   port is refused with a permissions error, Windows has reserved it; try another port
   rather than reporting a failure. They should be looking at their own base before this
   command ends.

Read `references/site-build.md` for the build, the transforms and the design system.

Offer alternatives only if the user asks: GitBook with two way git sync, Notion, Obsidian.
Each of those adds an account, so let the local default stand unless they want otherwise.

## 2. Materials inbox

Default and recommendation: **a Telegram bot**. It is the piece that makes the whole thing
worth using, because saving happens on a phone, hours before any processing.

Ask whether they want it now or later. Plain chat paste works immediately and needs nothing,
so a user in a hurry can start filing today and add the bot afterwards.

If they want it now, request, with revocation stated up front:

- **Telegram bot token**, created in about sixty seconds through **@BotFather** with
  `/newbot`. Revoke at any time with BotFather `/revoke`, which issues a fresh token and
  kills the old one.
- **Approved accounts.** Each account they will send from messages the bot once during a
  short enrolment window. Record the chat IDs. Accounts not on the list are ignored, and any
  account can be removed later.

Then install the collector from `inbox/`:

1. Copy `inbox/bot.py` and `inbox/config.example.json` into the base folder.
2. Write `config.json` with the token, and open an enrolment window.
3. Start the bot, and set it to start again at login so capture never sleeps.
4. Have the user send one message from their phone, and confirm it arrived in the queue.

Never write the token into any file that git tracks.

## 3. Confirm ready

Report back in plain words:

- Where the base lives, and the address to read it.
- Whether the inbox is connected, and how many accounts are approved.
- That they can forward links any time and run **`/promptos:process`** to file them.
- That **`/promptos:publish`** puts it online later, whenever they want it on a phone.

Say plainly: everything is on their computer, nothing is shared, and every token they pasted
can be revoked.

## Hard rules

1. **Never one way force-sync over the user's edits.** If they can edit by hand, they will.
   Pull before editing, treat their version as authoritative, and adapt around it. A force
   import once destroyed a user's manual page. That class of bug is unacceptable.
2. **Never delete the user's messages or content yourself.** Mark items processed and give
   them a one tap `/cleanup`. Deletion is user triggered, always.
3. **Never publish without explicit consent.** Setup ends on the local machine. Going online
   is its own command, with its own warning.
