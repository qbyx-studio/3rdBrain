# Platform Setup; Output & Input Pipelines

Read this when establishing (or repairing) the pipeline. All steps are generic; substitute
the user's own accounts, repos and tokens. Never hardcode a specific user's IDs or paths
into pages; keep machine-specific ops notes on a dedicated ops page in their base.

## Table of contents

1. Output platforms; comparison & recommendation
2. GitBook + GitHub two-way sync (reference implementation)
3. Other output platforms (notes)
4. Input platforms; comparison & recommendation
5. Telegram bot inbox (reference implementation)
6. Other input channels (notes)
7. Scheduled auto-processing
8. Credential request checklist

---

## 1. Output platforms; comparison & recommendation

Recommend based on: does the user manually edit? need public sharing? like markdown?

| Platform | Best when | Watch out |
| --- | --- | --- |
| **GitBook + Git Sync** (recommended) | Wants polished docs UI + git history + AI edits and manual edits coexisting | MUST enable two-way Git Sync before mixing manual + automated edits |
| Notion | User lives in Notion already | API blocks are fiddlier than markdown; no git history |
| Obsidian (+ Git / Publish) | Local-first, markdown purist | Publishing costs extra; sync conflicts on mobile |
| Outline / BookStack (self-hosted) | Privacy, own infra | User maintains a server |
| Docusaurus / MkDocs + GitHub Pages | Developer user, public site | No WYSIWYG editing for the user |

The invariant that matters more than the brand: **a git repository as the source of truth**,
with the rendering platform syncing from it. That gives history, rollback, and safe
concurrent edits regardless of frontend.

## 2. GitBook + GitHub two-way sync (reference implementation)

Needs: GitHub personal access token (`repo` scope), GitBook API token
(app.gitbook.com → Developer settings), a GitBook organization.

1. **Create a private GitHub repo** for content (`POST /user/repos` or `gh repo create`).
2. Structure: markdown files in topical folders; `SUMMARY.md` = table of contents
   (nesting via indentation; group headers via `## Section`); `.gitbook.yaml`:
   ```yaml
   root: ./
   structure:
     readme: README.md
     summary: SUMMARY.md
   ```
   Images: commit under `.gitbook/assets/`, reference relatively; GitBook ingests them.
3. **Initial import** (only while the space is empty / one-way is safe):
   `POST https://api.gitbook.com/v1/spaces/{spaceId}/git/import` with
   `{url: "https://USER:TOKEN@github.com/user/repo.git", ref: "refs/heads/main"}`.
   Create the space first via `POST /v1/orgs/{orgId}/spaces` `{title}`.
4. **Enable two-way Git Sync** (user does this in GitBook UI: space → Configure → Git Sync →
   GitHub → pick repo/branch; initial-sync direction = whichever side currently holds the
   truth). From that moment: **never call the import API again**; it fights the sync and
   can destroy manual edits. The pipeline becomes plain git:
   `pull --rebase` → edit → commit → push; GitBook auto-syncs both directions
   (manual UI merges become `GITBOOK-*` commits you pull).
5. **Verify** pages after each push: `GET /v1/spaces/{id}/content` (page tree) or
   `/content/path/{path}` (rendered markdown). Note: GitBook builds URL slugs from group
   names; look pages up via the content tree, don't guess slugs.
6. GitBook markdown blocks that round-trip through git: `{% embed url="…" %}`,
   `{% hint style="info" %}…{% endhint %}`, code fences, HTML tables.

## 3. Other output platforms (notes)

Same pipeline shape everywhere: keep a git repo of markdown as truth; adapt only the
publish step (Notion API page upserts; Obsidian = the vault IS the repo; static-site =
CI deploy). If the platform has no two-way sync, then the git repo is the ONLY write path,
tell the user manual platform edits will be overwritten, and offer a "port my manual edit
back" command instead.

## 4. Input platforms; comparison & recommendation

| Channel | Best when | Watch out |
| --- | --- | --- |
| **Telegram bot** (recommended) | User saves from phone, multiple devices/accounts | Bot API keeps unfetched updates only ~24h → need an always-on collector |
| Plain chat paste | Zero setup, low volume | No queue; nothing persists between sessions |
| Email address | Everything can send email | Parsing noise; needs mailbox access |
| Notion/Sheet inbox page | User already lives there | Polling; no push |
| WhatsApp (whatsmeow bridge) | User insists on WhatsApp | Unofficial client: linked-device pairing, ~20-day session expiry, ToS/ban risk |

## 5. Telegram bot inbox (reference implementation)

1. User creates the bot: **@BotFather → /newbot** → they paste the token to you.
2. Build a small long-polling collector (any language; stdlib is enough) that:
   - long-polls `getUpdates` and **persists every message to a local queue file
     immediately** (survives the 24h server retention),
   - **binds to an allowlist** of the user's account IDs; first-sender binding plus an
     explicit enrollment window for additional accounts (confirm enrolled usernames with
     the user afterwards); ignore everyone else,
   - flags trigger phrases (e.g. any message mentioning the base's name) as "process now",
   - handles `/cleanup`: deletes messages **already marked processed**; using each
     message's own chat id (multi-account!); plus its own replies; Telegram only allows
     bots to delete messages <48h old, so report the too-old remainder for manual deletion,
   - handles `/help`,
   - runs persistently (autostart at login) so capture never sleeps.
3. Processing marks queue items `processed: true` and sends a confirmation to each
   submitting chat: what was filed where + cleanup reminder. Failures message the user too,
   silent scheduled failures destroy trust in the pipeline.

## 6. Other input channels (notes)

Whatever the channel: durable queue at capture time, allowlist, confirmations, and
user-triggered cleanup. Those four properties are the spec; the transport is detail.

## 7. Scheduled auto-processing

If the user wants hands-off processing (e.g. daily at a set hour):
- The collector daemon can spawn a headless agent run (`claude -p "<pointer to a
  PROCESS instructions file>"`) once per day when the queue is non-empty; skip when empty;
  catch up after the hour if the machine was asleep (guard with a last-run date).
- Requirements to state up front: the machine must be on; the CLI must be authenticated
  once (`claude` → `/login`); unattended runs need permission bypass; say so explicitly;
  tokens must persist locally, so agree on rotation policy with the user.
- Make every run observable: "run started (N items)" and "run failed (reason)" messages to
  the input channel. A PROCESS instructions file holds the full pipeline (this skill's
  rules + the user's platform specifics) so unattended runs behave identically to
  interactive ones.

## 8. Credential request checklist

When something's missing, ask once, precisely, with sources:

- GitHub PAT (`repo` scope); github.com/settings/tokens
- GitBook API token; app.gitbook.com → Developer settings (needs org admin/edit)
- Telegram bot token; @BotFather /newbot (then the user sends the bot one message)
- Platform-specific equivalents (Notion integration token + page share, etc.)

Also remind: tokens pasted into chat should be treated as exposed; rotate after setup,
or when the automation needs them long-term, store locally and agree that revocation now
breaks the pipeline.
