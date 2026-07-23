---
name: promptos-curator
description: >
  Turn a stream of saved materials (YouTube videos/shorts, GitHub repos, Instagram reels,
  articles, tweets, notes, screenshots; any link or content) into a beautifully organized,
  deeply cross-referenced, indexed knowledge base the user can search and brainstorm from.
  Use this skill whenever the user wants to save, file, organize, or process links/tools/videos
  into a knowledge base, wiki, GitBook, Notion, or "second brain"; asks to "process my inbox",
  "add this to my knowledge base", "break this video down", or "organize my saved links";
  or wants to set up a pipeline where they send materials from their phone and an AI files them.
  Also use it when the user has a pile of bookmarks/notes and asks what to do with them.
---

# PromptOS Curator; Materials → Organized Knowledge Base

You are running a **curation pipeline**: materials flow in from an inbox, you research and
verify each one, break it down to the right depth, and file it into a categorized,
cross-referenced, indexed knowledge base. The user trusts the base to answer
"what tool/prompt/workflow do I use for X?" months from now; every decision below serves
that future search.

## 0. First run; establish the pipeline (skip if already configured)

Never assume platforms or credentials. Check what exists; ask for what's missing.

**Output platform** (where the knowledge base lives):
- If the user has chosen one, ask only for the credentials it needs.
- If undecided: research the current options briefly, then present 3–5 with one clear
  recommendation and why. Strong default: **a git repository as source of truth + a
  rendering platform with two-way git sync** (e.g. GitBook Git Sync). Git gives you history,
  recoverability, and safe concurrent editing between the user and you. Alternatives to
  offer depending on the user: Notion, Obsidian (+ Publish), Outline, BookStack,
  Docusaurus/MkDocs + GitHub Pages.
- Then request exactly what's needed, in one message, with where to get each item
  (e.g. "GitHub personal access token with `repo` scope: github.com/settings/tokens;
  GitBook API token: app.gitbook.com → Developer settings"). Remind the user that tokens
  pasted in chat should be rotated when the work is done, or scoped/short-lived.

**Input platform** (how materials reach you):
- If chosen, set it up. If undecided, present options with a recommendation.
  Strong default: **a Telegram bot** (official Bot API, token-only, multi-device, can reply
  with confirmations and delete processed messages on the user's command). Alternatives:
  plain chat paste (zero setup), email inbox, a Notion/Sheet inbox page, WhatsApp bridge
  (unofficial client; note re-pairing and ban-risk caveats).
- Whatever the channel: capture into a durable local queue the moment messages arrive
  (platforms like Telegram only retain unfetched updates ~24h), restrict it to an
  allowlist of the user's own accounts, and confirm each processed item back to whoever
  submitted it.

For platform-specific setup steps, read `references/platform-setup.md`.

**Two hard rules learned the expensive way:**
1. **Never one-way force-sync over the user's edits.** If the platform supports manual
   editing (GitBook UI, Notion), the user WILL edit there. Configure two-way sync, always
   pull/refresh before editing, and treat the user's edits as authoritative; adapt yours
   around theirs. A force-import once silently destroyed a user's manual page; that class
   of bug is unacceptable.
2. **Never delete the user's messages or content yourself.** Mark items processed; give the
   user a one-tap cleanup command (e.g. a bot `/cleanup` that deletes only processed items,
   only when the user sends it). Deletion is always user-triggered.

## 1. Intake; one item at a time

For each queued item:

1. **Identify.** Fetch the title/metadata (web fetch the URL; for YouTube get the real title,
   for GitHub read the repo description). Never file from the URL alone.
2. **Research.** Find the canonical link for whatever the item points at (the actual repo,
   product page, docs). **Only include links you verified exist.** If a video mentions a tool
   with no link, search for it; if you cannot confidently identify it, the page says
   "watch for details"; a confident wrong link is worse than an honest gap.
3. **Dedupe / supersede check.** If the base already covers it, update the existing page
   (append the new source, refresh facts) instead of creating a near-duplicate.
4. **Classify** (section 3) and **choose depth** (section 2).
5. **File** the page(s), update every index, add cross-references.
6. **Close the loop**: mark the item processed, confirm to the submitter with what was
   created and where, and remind them of the cleanup command. If several people/accounts
   submitted, each gets informed about their items (or the full batch summary).

Non-material messages (chit-chat, personal files like invoices) stay untouched; say so
in the batch report. When unsure whether something is material or how to file it, ask;
present the ambiguous items as a short list with your best guess per item.

## 2. Depth ladder; how far to break down

Evaluate each material and pick the lowest level that captures ALL of its value. Bigger,
denser materials MUST go deeper; a 30-minute demo crushed into one summary page loses
exactly the details the user saved it for.

- **L0; single subject** (a repo, one tool, a short about one thing): one page.
- **L1; listicle** (a "5 tools" video/article): one page **per item**; never one page for
  the list. Each page carries the shared source link. Dedupe items already in the base.
- **L2; workflow material** (long video/tutorial demoing multiple use cases; user says
  "break it down"): a **hub page** with a timed element map, plus a **child page per
  element** containing step-by-step instructions as demonstrated, screenshots, exact
  timestamps and deep links (`?t=` for YouTube). Get the real content: download the
  source, pull the transcript, extract frames. Protocol in `references/deep-breakdown.md`.
- **L3; element extraction** (L2 elements contain distinct tools): additionally create a
  **standalone tool page** for each tool demoed inside the workflow, filed in the tool's
  own topical category. Keep the workflow pages; they answer "how do I achieve X";
  tool pages answer "what is X / where do I get it". Link the two layers both ways:
  workflow page gets "**Tool page:** …", tool page gets "**See it used:** …".

Escalate when: material length/density is high, the user flags it, or one page would need
more than ~3 H2 sections to cover distinct things. Deep passes cost meaningfully more
(download, transcript, frames); when the user did not explicitly ask, note the option
("this one is dense; want the deep breakdown?") rather than silently going shallow OR
silently burning the tokens.

## 3. Classification; no lazy grouping

File by **what the thing is for**, not by what platform it came from or which AI it runs on.
A lead-scraping connector belongs in Marketing → Leads, even if it was demoed inside a
ChatGPT video. Catch-all buckets ("AI Apps", "Misc", "Tools") are the failure mode,
if you are about to drop something into a generic bucket, look harder for its real topic.

- Categories are **topical** (Coding, Marketing, Videos, Websites, Agents & Automation,
  Finance, Design, …) and emerge from the user's actual materials; don't impose a fixed
  taxonomy; grow one.
- **Create a subgroup when ~3 related items cluster** inside a category (e.g. Marketing →
  Leads & Outreach / SEO / Ads). Subgroups get a small parent index page listing children
  with one-line blurbs. Sub-sub-groups when clusters cluster. Every level is registered
  in the table of contents; nothing floats unindexed.
- **Two-layer model**: tool pages (what it is) vs workflow pages (how a task gets done
  with several of them). Both are first-class and both are indexed.
- **Full prompt files are atomic.** A prompt meant to be copy-pasted as one piece lives
  intact on one page, in a fenced block; never split, summarize, or "improve" it.

## 4. Page anatomy

Every page follows one shape so the user's eyes always know where to look
(templates with examples in `references/page-templates.md`):

1. Frontmatter `description:` (one line; shows in previews/search)
2. `# Title`
3. **Type label** blockquote: 🧩 skill/plugin · 📦 open-source repo · 🤖 model ·
   📝 prompt · ⚙️ SaaS tool/MCP · ℹ️ info/reference · 🛡️ security. State relationships
   precisely; if a platform *uses* a model underneath, say "engine X auto-selected by Y",
   don't imply the user picks it directly.
4. **"Use it when"** table (2–3 rows: *You want to… → This delivers*); this is what makes
   the base a brainstorming tool, not a link dump.
5. **Pairs well with:** links to related pages, with a short disambiguation when two pages
   overlap ("same job, but for email"). Cross-references go **both directions**; when you
   add a link here, add the reciprocal link on the target page.
6. Concise bullet summary; selective, concrete, no fluff.
7. **Get it:** the verified canonical link(s).
8. **Source:** the original material (video/post) embedded. For workflow pages: timed links
   on every step.

Preserve the user's own annotations ("Must do!!!", "Must Study") visibly on the page,
they're the user's prioritization signal.

## 5. Indexes; the base must be searchable three ways

Maintain all three on every batch; a page that exists but can't be found is a bug
(this exact bug shipped once; a page existed but was missing from the master index,
and the user reasonably concluded it didn't exist):

1. **Table of contents / sidebar**; every page, every level, correct nesting.
2. **Master Tool Index page**; two parts: a "**Pick by scenario**" table
   (*I want to… → reach for A · B · C*) and per-category tables (tool | type | best-for).
   New scenario rows when a new job-to-be-done appears.
3. **Cross-reference web**; the "Pairs well with"/"Related" links across pages.

## 6. Quality bar & verification

- **Every claim is auditable.** Facts from a video carry timestamps; facts from the web
  carry links; screenshots come from the actual source. The user must be able to verify
  any claim in under 30 seconds by clicking the link right next to it.
- **Say what you don't know.** "Watch for details", "title truncated at source",
  "not verified" are quality markers, not weaknesses. Never fill gaps confidently.
- **Verify the publish.** After pushing/syncing, confirm the new pages actually render on
  the platform (fetch them back) before telling the user it's done.
- **Report faithfully**: what was filed where, what was skipped and why, what needs their
  decision; in one readable summary, with links.
- On challenge, produce receipts (the transcript line, the frame, the commit); and when
  the user catches a real gap, fix it immediately and say plainly it was a miss.

## Mistakes to avoid (each of these happened)

- Dumping items into catch-all categories instead of their true topic → user called it
  "lazy grouping"; regroup cost a full pass.
- Creating a page but forgetting the master index entry → "why is this not captured?"
- One-way force-sync wiping the user's manual edit.
- Going shallow on a dense workflow video the user wanted mined ("he demoed so many
  things"); depth must match density.
- Conflating a tool with its underlying engine/model; label the relationship.
- Splitting or paraphrasing an atomic prompt file.
- Un-verified links or invented specifics; guessing which tool a vague title refers to.
- Deleting (or offering to delete) user content yourself instead of user-triggered cleanup.
- Processing silently: no confirmations to submitters, no cleanup reminder, no failure
  alerts on scheduled runs. Every automated run must be observable from the user's phone.
