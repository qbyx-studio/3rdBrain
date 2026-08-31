---
name: 3rdbrain-curator
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

# 3rdBrain Curator; Materials → Organized Knowledge Base

You are running a **curation pipeline**: materials flow in from an inbox, you research and
verify each one, break it down to the right depth, and file it into a categorized,
cross-referenced, indexed knowledge base. The user trusts the base to answer
"what tool/prompt/workflow do I use for X?" months from now; every decision below serves
that future search.

Before any setup or curation work, follow `references/framework-freshness.md` once.

For any video source, read `references/video-analysis.md` before acquisition. It routes
ordinary transcript mining, enhanced visual analysis, and raw-footage editing to the right
workflow without making optional tools a requirement.

For any website or article source, read `references/web-analysis.md` before acquisition. It
routes clean public-page extraction, completeness checks and browser fallback without treating
social posts or comments as ordinary article text.

For any repository or source-code material, read `references/repository-analysis.md`. It maps
the project first, retrieves only evidence-bearing files, and verifies product claims against
implementation or tests without executing untrusted code.

For social posts, discussions or comments, read `references/social-analysis.md`. It preserves
the original post, author follow-ups, reply structure, edits and access gaps through compact
platform-specific acquisition.

For PDFs, EPUBs and Office documents, read `references/document-analysis.md`. It uses native
text and structure first, selective rendering for visual evidence, and OCR only where native
extraction is incomplete.

For screenshots, image posts, photographed slides, scans, diagrams or handwriting, read
`references/image-analysis.md`. It maps image sets first, combines OCR with selective
full-resolution visual inspection, and records uncertainty instead of guessing.

For podcasts, audio, voice notes, RSS or Atom feeds, read `references/audio-analysis.md`. It
prefers existing timed transcripts and compact feed maps, then transcribes or opens selected
entries only when needed.

For login-gated or interactive sources, read `references/interactive-analysis.md` after the
ordinary source route leaves a verified gap. It uses the smallest read-only interaction in an
existing user-controlled session and never handles raw credentials or bypasses access controls.

## 0. First run; establish the pipeline (skip if already configured)

Never assume platforms or credentials. Check what exists; ask for what's missing.

**Where the base lives.** Default: **a folder on the user's own computer, rendered by
MkDocs**, with a local git repository for history. Setup finishes with zero accounts, zero
tokens and zero cost, and nothing leaves the machine. Assume the user has never opened a
terminal: you run every command, and you translate every error into plain words.

Read `references/site-build.md` for the build, the transforms and the design system. The
same build serves the local preview and any later publish, so the two never drift.

Publishing is a separate, explicit choice. `commands/publish.md` hosts the base on
Cloudflare Pages, free, and asks whether the user wants a login wall or an open link. It
warns before anything uploads and verifies from outside afterwards. Never publish during
setup, and never treat silence as consent.

Offer alternatives only when the user asks for them: GitBook with two way git sync, Notion,
Obsidian, Outline. Each adds an account, so the local default stands unless they choose
otherwise. When they do choose one, request exactly what it needs in one message, with where
to get each item and how to revoke it.

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

For inbox and hosting specifics, read `references/platform-setup.md`.

**Three commands.** First-run setup is **`/3rdbrain`** (build the base locally, connect the
materials inbox). Routine runs are **`/3rdbrain:process`** (framework freshness → self-heal →
pull → deep-mine → file → wire → confirm; full contract in `commands/process.md`).
The freshness check ports newer compatible public framework improvements without overwriting
the base's content or configuration. Going online is
**`/3rdbrain:publish`**, opt in and reversible.

**Every credential is revokable, nothing you paste is permanent:** the Telegram bot token
via @BotFather `/revoke` (issues a fresh token and kills the old one); any Cloudflare API
token at dash.cloudflare.com → My Profile → API Tokens; and any account can be removed from
the inbox allowlist at any time. Local setup asks for none of these.

**Two hard rules learned the expensive way:**
1. **Never one-way force-sync over the user's edits.** If the platform supports manual
   editing (the GitBook UI, Notion, a text editor), the user WILL edit there. Configure two-way sync, always
   pull/refresh before editing, and treat the user's edits as authoritative; adapt yours
   around theirs. A force-import once silently destroyed a user's manual page; that class
   of bug is unacceptable.
2. **Never delete the user's messages or content yourself.** Mark items processed; give the
   user a one-tap cleanup command (e.g. a bot `/cleanup` that deletes only processed items,
   only when the user sends it). Deletion is always user-triggered.

## 1. Intake; one item at a time

### Every item gets an outcome

The queue holds three kinds of item, and all three are first class. A queue is not a list of
URLs.

| Item | What to do |
| --- | --- |
| **A command** (`process`, `/cleanup`, `/help`) | Trigger it. This is the only kind that files nothing. |
| **A link**, with or without remarks | Mine it and file it, per the steps below. |
| **Text only**, no link at all | **Read it and act.** It is a note, an idea, or an instruction. |

Text-only items are where pipelines quietly rot. Handle one of three ways:

- **A note or idea** becomes a page of its own, filed by topic like anything else.
- **An instruction about another item** applies to that item, and overrides its default shape.
- **Ambiguous** means ask the user. One question costs less than a lost thought.

**Never mark an item `processed` without a filing action.** A `processed: true` carrying an
empty `filed_as` is a silent skip: the item leaves the queue, no page exists, and no
confirmation is sent, so nobody learns it vanished. That is exactly the drift that dropped
notes when a pipeline drifted URL-only, and it is the same period in which the "done"
confirmations lapsed. If an item genuinely cannot be filed, record the reason in `filed_as`
and say so in the confirmation. Commands are the only exception.

For each queued item:

1. **Read the latest remarks before mining.** Read the current text or caption of every
   queued message, including edits made after initial capture. Telegram delivers an edit as
   `edited_message`, not `message`; the queue's latest version is authoritative. A queued
   link is often followed by a separate message carrying instructions for that item: how to
   break it down, what to emphasise, what to warn about. **Per-item remarks override the
   default page shape.** A remark such as
   "decompose by use case, one page each, categorised by what it is for, and disclaim what it
   was actually tested on" replaces your filing plan for that item; follow it.

   Look for the adjacent message in the queue, before and after the link, from the same
   account. Also watch for a **gap in `message_id`**: consecutive submissions from one account
   normally have near-consecutive ids, so a jump means a message was dropped and the remarks
   for that link may be gone. When remarks may have been lost, **ask the user** rather than
   guessing a shape. Filing a link the wrong way costs more than one question.

   An item with `needs_review: true` was edited after it had already been filed. Use
   `previous_filed_as` to update the existing page, then mark and confirm the refreshed item
   through the normal close-the-loop step. Never create a second page for the edit.

2. **Identify AND mine.** Fetch the title/metadata and route the source by format. For ANY
   video (shorts included), follow `references/video-analysis.md`, pull the transcript
   (auto-subtitles) and read it before filing. Repositories follow
   `references/repository-analysis.md`; social threads follow `references/social-analysis.md`;
   PDFs, EPUBs and Office files follow `references/document-analysis.md`; screenshots, image
   posts and photographed notes follow `references/image-analysis.md`; audio, podcasts and feeds
   follow `references/audio-analysis.md`; login-gated or interactive gaps follow
   `references/interactive-analysis.md`. A title is clickbait,
   never content; filing from a title alone produces link-dumps and wrong categories
   (a "money printer" short turned out to be a video-generation repo). The transcript of
   a short costs seconds and yields the tool names, steps and claims the page exists for.
3. **Research.** For websites and articles, follow `references/web-analysis.md`. Find the
   canonical link for whatever the item points at (the actual repo,
   product page, docs). **Only include links you verified exist.** The mined content
   (transcript/text) names the tools; search from those names, never from the title.
   "Watch for details" is a FAILURE STATE, permitted only after mining was attempted and
   the content itself was unobtainable; it is never a substitute for reading the source.
   A confident wrong link is worse than an honest gap; an honest gap is worse than
   doing the five-second transcript pull that removes it.
4. **Dedupe / supersede check.** If the base already covers it, update the existing page
   (append the new source, refresh facts) instead of creating a near-duplicate.
5. **Classify** (section 3) and **choose depth** (section 2).
6. **File** the page(s), update every index, add cross-references.
7. **Close the loop**: mark the item processed, confirm to the submitter with what was
   created and where, and remind them of the cleanup command. If several people/accounts
   submitted, each gets informed about their items (or the full batch summary).
8. **Housekeeping**: after the batch is pushed and confirmed, delete local scratch downloads
   (videos, extracted frames you did not commit, temp transcripts) to avoid disk bloat.
   Only committed assets stay; everything else is deleted.

Non-material messages (chit-chat, personal files like invoices) stay untouched; say so
in the batch report. When unsure whether something is material or how to file it, ask;
present the ambiguous items as a short list with your best guess per item.

## 2. Depth ladder; how far to break down

Evaluate each material and pick the lowest level that captures ALL of its value. Bigger,
denser materials MUST go deeper; a 30-minute demo crushed into one summary page loses
exactly the details the user saved it for.

**The gold standard (this is the bar; hit it every time).** A page is TRUE-mined only when
all four are on it:
1. **Every on-screen or spoken artifact, verbatim, in its own block.** Every prompt, command,
   config, or code snippet the creator shows or reads aloud gets transcribed word-for-word
   into a fenced/prompt block, each tagged with the timestamp it appears (`(3:26)`). A video
   that shows three example prompts yields three verbatim blocks, not one summarized "template".
   Transcribe from the on-screen frame when the caption garbles it.
2. **The reusable principle, distilled.** Name the transferable insight the creator is teaching,
   not just the examples ("the power isn't the wording, it's the 3-part structure"; "the bar is
   the whole trick"). Give the reader the shape they can reuse on their own goal.
3. **Screenshots at the moments that carry information** (a full prompt on screen, a result, a
   settings panel), extracted and embedded inline, not described.
4. **Timestamps on everything**, so a reader can jump to any claim in seconds.
The reference page for this bar is the Gauntlet Loop page: every demoed prompt pulled verbatim
at its timestamp (FPS 3:26, apartment 7:22, landing page 10:41), screenshots embedded, the
3-part structure distilled, plus a ready-to-reuse meta-prompt. Match that depth. A page that
gives a summary + a link + one guessed template is a FAILURE even if nothing on it is wrong.

**Standing depth preference.** If the user has said "always mine deep / do everything / don't
give me basics" (this user has), treat deep mining as the DEFAULT for their base: do the full
pass without asking, and never downgrade to a summary on cost grounds. The "surface the choice"
option below applies only to users who have NOT set a standing preference.

- **L0; single subject** (a repo, one tool, a short about one thing): one page,
  built from the mined content. Content mining (reading the transcript/text) is NOT the
  deep treatment; it is the floor at every level, L0 included.
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
more than ~3 H2 sections to cover distinct things. What costs real money is the FULL deep
pass (video download, frame extraction, per-element pages); when the user has NOT set a
standing deep-mine preference and did not explicitly ask, note the option ("this one is
dense; want the deep breakdown?") rather than silently going shallow OR silently burning
the tokens. When the user HAS set a standing preference, skip the question and mine deep.
Subtitle-only transcript mining costs seconds and is never skipped on cost grounds.

## 3. Classification; no lazy grouping

File by **what the thing is for**, not by what platform it came from or which AI it runs on.
A lead-scraping connector belongs in Marketing → Leads, even if it was demoed inside a
ChatGPT video. Catch-all buckets ("AI Apps", "Misc", "Tools") are the failure mode,
if you are about to drop something into a generic bucket, look harder for its real topic.

**A source, creator, product, or vendor hub is a lens and cross-linking page, never a
substitute for purpose-based filing.** Give the source one hub with an element map, then file
each extracted workflow or use case under the top-level section matching what that page helps
the reader do. Email, engineering, marketing, research, and local-compute workflows can all
come from one source and still belong in different primary sections. The source hub links
across those sections; it does not own the children in the sidebar.

- Categories are **topical** (Coding, Marketing, Videos, Websites, Agents & Automation,
  Finance, Design, …) and emerge from the user's actual materials; don't impose a fixed
  taxonomy; grow one.
- **Create a subgroup when ~3 related items cluster** inside a category (e.g. Marketing →
  Leads & Outreach / SEO / Ads). A subgroup is a **label-only expander by default**: write
  a plain `* Group name` item in `SUMMARY.md`, with its linked children nested below it.
  Link the group itself only when it has a deliberately authored, standalone index page
  that gives readers value beyond repeating the child list. Sub-sub-groups follow the same
  rule when clusters cluster. Every level is registered in the table of contents; nothing
  floats unindexed. Review the generated
  `assets/discovery/taxonomy-audit.json` after every batch: it proposes 3+ item clusters,
  flags groups above 12 direct pages, paths deeper than four levels, and catch-all names.
  The audit proposes; the curator creates and names meaningful groups in `SUMMARY.md`.
- **One primary location, many facets.** Every curated content page has exactly one primary
  topical location in the sidebar and may carry every cross-cutting facet that truly applies.
  Every page created by the curator declares its complete sidebar ancestry as a
  `primary_section` plus a complete `taxonomy_path` list in frontmatter. The build validates
  the declared top-level section and every navigation level.
- **Two-layer model**: tool pages (what it is) vs workflow pages (how a task gets done
  with several of them). Both are first-class and both are indexed.
- **Full prompt files are atomic.** A prompt meant to be copy-pasted as one piece lives
  intact on one page, in a fenced block; never split, summarize, or "improve" it.

## 4. Page anatomy

Every page follows one shape so the user's eyes always know where to look
(templates with examples in `references/page-templates.md`):

1. Frontmatter `description:` (one line; shows in previews/search), `primary_section:`,
   `page_type:`, useful `aliases:`, and `taxonomy_path:` (every sidebar level from section
   through subgroup)
2. `# Title`
3. **Type label** blockquote: 🧩 skill/plugin · 📦 open-source repo · 🤖 model ·
   📝 prompt · ⚙️ SaaS tool/MCP · ℹ️ info/reference · 🛡️ security. State relationships
   precisely; if a platform *uses* a model underneath, say "engine X auto-selected by Y",
   don't imply the user picks it directly.
4. **"Use it when"** table (2 to 3 rows: *You want to… → This delivers*); this is what makes
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

### Source links are embed blocks, whatever the section is called

Any link that **is** a source, a canonical destination, or a video gets its own line as an
embed block:

```markdown
{% embed url="https://the-link" %}
```

This is a rule about the link's role, never about the heading above it. Section labels are
expected to change from base to base; a recipe base has no "Get it" section and will call it
"## Source", a legal base may call it "## Authority". The heading adapts. The block does not.

A bare markdown link is correct for an **inline reference**: a timestamped step inside a
method list, a mention mid-sentence, a row in a table. Those should stay plain, because a
list of eleven players is unreadable.

The failure this prevents, seen in production: a base renamed the section for its own domain,
the embed convention was attached to the old label rather than to the link, and 17 pages of
deep-mined video work rendered as flat text links with no player. Prompts and callouts
survived in the same base, because those attach to a content type rather than a heading.

### Date stamp (every page, first body line)

Every content page carries a visible, subtle stamp as its **first body line**: immediately
after the frontmatter block, or line 1 when a page has no frontmatter.

```markdown
<sub>🗓️ Added YYYY-MM-DD</sub>
```

New pages get today's date. It is the age signal `/3rdbrain:stalecheck` reads, so a missing
stamp means the page ages by its first commit date instead, which is close but coarser.

To backfill a base that predates the convention, take each page's first-add date from git:

```bash
git log --diff-filter=A --reverse --format=%as --name-only
```

## 5. Indexes; the base must be searchable five ways

Maintain all three on every batch; a page that exists but can't be found is a bug
(this exact bug shipped once; a page existed but was missing from the master index,
and the user reasonably concluded it didn't exist):

1. **Table of contents / sidebar**; every page, every level, correct nesting.
2. **Master Tool Index page**; two parts: a "**Pick by scenario**" table
   (*I want to… → reach for A · B · C*) and per-category tables (tool | type | best-for).
   New scenario rows when a new job-to-be-done appears.
3. **Cross-reference web**; the "Pairs well with"/"Related" links across pages.
4. **Facet indexes**; the topical category is only ONE axis. The same page is often
   findable by a cross-cutting *facet*: **Workflow, 3D, Game, Website, Video, Image, Skill,
   Prompt, Agent/Automation, MCP**. A page belongs to exactly one topical category but to
   as many facets as apply (the Gauntlet Loop is category=Coding, facets=Workflow · 3D ·
   Game · Website). Maintain a **facet hub page per facet** (a curated table of every page
   carrying that facet, with its hook), and tag each page with a **`Facets:` line** listing
   its facets as links to those hubs. This is what lets the user browse "show me everything
   3D" or "show me every workflow" independent of where the page is filed. When you add or
   touch a page, add it to every facet hub it qualifies for, and register the hubs in the
   sidebar under a top-level **"Browse by facet"** group. Prefer facet hubs (one source of
   truth, listed under every facet) over physically duplicating page content, which diverges.
5. **Unified search**; the header quick search and full `Discover <project name>` page use
   the same generated catalog, aliases, controlled vocabulary and hybrid ranking. Exact
   results appear immediately. A zero-LLM browser model reranks by meaning when available,
   while the lexical safety channel preserves proven matches. Add ordinary phrases readers
   will type to `aliases`; add representative jobs to `search-cases.yml`. A batch is incomplete
   if the committed Recall@5/MRR floors regress.

### Backward-compatible adoption

Legacy pages without declarations remain valid. Every newly extracted page must declare
`primary_section` and the complete `taxonomy_path`. Backfill older pages incrementally when
touched: record their purpose-based top-level section and full ancestry, then move or confirm
the `SUMMARY.md` entry in the same change.

## 6. Quality bar & verification

- **The page must beat the click.** The test of every page: a reader learns what is
  inside the source (the tool names, the steps, the numbers, the verdict) WITHOUT
  opening it. A page that only restates the title plus a link is a link-dump, the
  exact thing this pipeline exists to kill. "No wrong claims" is necessary and
  insufficient; the bar is "the true claims are present".
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
- Filing videos from their titles: a batch of shorts once shipped as title-plus-link pages
  ("watch for details") when five-second transcript pulls would have named every tool;
  one page even landed in the wrong category because the title hid what the thing was.
- Treating the honesty fallback ("watch for details") as an acceptable terminal state
  instead of a signal to mine harder.
- Deleting (or offering to delete) user content yourself instead of user-triggered cleanup.
- Processing silently: no confirmations to submitters, no cleanup reminder, no failure
  alerts on scheduled runs. Every automated run must be observable from the user's phone.
