# PromptOS by Qbyx

**Own every link you save.**

[![PromptOS launch video preview, click to watch with sound](docs/assets/preview.gif)](https://qbyxstudio.github.io/PromptOS/)

> **▶ [Watch the full launch video (with sound)](https://qbyxstudio.github.io/PromptOS/)**, made with [`/gloat`](https://github.com/QbyxStudio/gloat), of course.

`/promptos-curator` is a Claude/ChatGPT skill that turns the stream of links you save,
YouTube videos, shorts, GitHub repos, reels, articles, notes, into a
**beautifully organized, deeply cross-referenced, searchable knowledge base**.
Send links from your phone, say "process", and every tool gets its own page with
verified links, use-case tables, and its place in a living index. Dense tutorial
videos get mined fully: transcripts, screenshots, step-by-steps, and timestamped
deep links for every single demoed element.

Your saved links become your personal tool library and knowledge base. It answers
one question extremely well: **"what do I use for this?"**

## Why I built this

I FOMO-ed. Hard. Every AI influencer post felt too important to lose, so I flooded
my own WhatsApp and Telegram with forwarded link. "Saved" and never seen again. So
I built this to solve my own problem. Easy to reference, and far less chance of
missing out on good tools because it drowned in my chat history.

The knowledge base this skill maintains for me is the reason it exists. Yours will
look like whatever you feed it.

## What it actually does

| You | The skill |
|---|---|
| Forward a link from any device | Captures it into a durable queue (Telegram bot, or any inbox you pick) |
| Say "process to promptos" | Researches each item, finds the **verified** canonical link, classifies it |
| Send a dense 30-min tutorial | Downloads it, mines transcript + screenshots, builds a hub + one page per demoed element with `?t=` deep links |
| Ask "what tool do I use for X?" months later | The **Pick-by-scenario index** answers in one table |
| Edit pages by hand | Two-way git sync keeps your edits and the AI's edits living side by side |
| Want things gone from chat | `/cleanup`; the bot deletes exactly what has been filed, exactly when *you* say so |
| Ask "is every skill in my base actually installed?" | `/promptos:skills` audits every agent runtime on the machine, installs what's missing, and verifies it landed |

Every page follows one anatomy: type label (🧩 skill · 📦 repo · 🤖 model · ⚙️ SaaS ·
📝 prompt), a "Use it when" table, a concise summary, the verified link, and the
original source embedded. Every claim is auditable; facts from videos carry
timestamps you can check in seconds.

Built-in guardrails, each learned from a real production failure: every tool lives
in its true topical category, every link is verified before it lands on a page,
full prompt files stay whole on a single page, your manual edits stay authoritative
through two-way sync, deletion happens on your command alone, and a page counts as
done once it appears in every index.

## The end product

A living library. Mine currently holds 150+ pages: every tool on its own page,
14 topical sections with subgroups, a master index searchable by scenario, and
deep-mined tutorial videos where every demoed element has its own step-by-step
page with screenshots and timestamped jump links. When I ask "what do I use for
lead scraping" or "which skill fixes my thumbnails", the answer is one search away,
with the verified link sitting right there.

## Example pipelines

The skill is input-agnostic and output-agnostic. Pick any inbox, pick any base:

| Inbox (where you save) | Base (where it's filed) | Who this fits |
|---|---|---|
| **Telegram bot ← YouTube + GitHub links** | **GitBook (two-way GitHub sync)** | **My own setup, the original PromptOS** |
| Instagram reels & saves | Notion | Creators living in IG and Notion |
| Facebook / LinkedIn saves | Google Docs / Drive | Teams that standardize on Google Workspace |
| X bookmarks | Obsidian vault | Local-first markdown people |
| Reddit saves + newsletters | MkDocs / GitHub Pages site | Developers who want a public tool wiki |
| Plain chat paste | Any of the above | Zero-setup start, upgrade later |

Same pipeline every time: capture, research, verify, break down, file, index,
cross-link, confirm.

## Install

```bash
/plugin marketplace add QbyxStudio/PromptOS
/plugin install promptos@promptos
```

Then three commands run the whole thing:

```bash
/promptos            # first-run setup: connect GitBook + Telegram (both revokable)
/promptos:process    # process the inbox: self-heal → deep-mine → file → confirm
/promptos:skills     # reconcile your catalogue against every agent runtime, install what's missing
```

<details>
<summary>Plugin system unavailable? Install the skill directly.</summary>

macOS / Linux:
```bash
rsync -a skills/promptos-curator/ ~/.claude/skills/promptos-curator/
```

Windows (PowerShell):
```powershell
Copy-Item -Recurse -Force skills\promptos-curator "$env:USERPROFILE\.claude\skills\promptos-curator"
```

Restart Claude Code after copying.
</details>

## Use it

### `/promptos` — first-run setup (revokable, works with any agent)

`/promptos` connects two things and requests exactly the credentials each needs,
with a link to get each token **and how to revoke it**. Nothing you paste is permanent.

1. **Knowledge base** — where pages are filed. Default: **GitBook + two-way GitHub
   sync** (git history, a polished reading UI, your manual edits kept safe). Needs a
   **GitBook API token** (revoke at app.gitbook.com → Developer settings) and a
   **GitHub PAT** (revoke at github.com/settings/tokens). Notion / Obsidian / MkDocs
   are supported alternatives.
2. **Materials inbox** — how links reach it. Default: a **Telegram bot** you create
   in 60s via **@BotFather** (revoke the token anytime with BotFather `/revoke`),
   plus an **approved-accounts allowlist** you can edit at any time. Plain chat paste
   works with zero setup.

### `/promptos:process` — run it

```text
you    → forward links to your bot from your phone, anytime
you    → /promptos:process
skill  → self-heals the inbox, deep-mines each item (transcript + timestamps +
         screenshots + verbatim prompts), files + cross-links + indexes, pushes
bot    → "✅ done: … Send /cleanup to tidy up."
```

### `/promptos:skills` — make your machine match your catalogue

Your base records which skills are worth having. `/promptos:skills` makes the machine match
the record, on **every agent runtime installed**, and then proves it.

It is **runtime-agnostic by construction**: it discovers which agent platforms exist rather
than branching on platform identity, so Claude Code, Codex, Cursor, Windsurf, Copilot CLI and
anything else that reads a skills directory all produce a complete report, including runtimes
that did not exist when this was written.

It audits **and repairs**. Anything catalogued but missing gets installed; anything installed
but broken gets fixed; and both get re-verified afterwards.

```text
you    → /promptos:skills
skill  → discovers every agent runtime on the machine
       → audits three separate states: valid on disk / loaded in the live registry /
         typeable as a slash command — these are not the same thing
       → diffs your catalogue against what's installed
       → installs what's missing, routing by what each source actually contains
       → brings every runtime to parity, mirroring in what an installer skipped
       → re-verifies, then reports what needs a restart and which surface it affects
```

It is built around two things that silently ruin skill installs:

- **Installers lie.** They report success for work they did not do — a cross-agent installer
  can print `copy → Codex ✓` and write nothing. Nothing here trusts an install log; every
  claim is grounded in a command run after the fact.
- **Installed ≠ loaded ≠ typeable.** A skill can be valid on disk, missing from the running
  agent's registry, and missing again from the slash menu. Each state is checked separately,
  which is what stops "everything installed ✅" from ending in an empty slash menu.

Catalogues also list CLIs, MCP servers, libraries and manual downloads next to real skills.
Those are reported as **NOT-A-SKILL** with what they actually are — never counted as
installed.

### Daily flow

```text
you    → forward 5 links to your bot from your phone
you    → "process to promptos"
skill  → researches, classifies, files, indexes, cross-links
bot    → "✅ Processed 5 items: … Send /cleanup to tidy up."
```

Steer it:

```text
process my queue
this one is dense, break it down fully           ← forces the deep treatment
break down by timing so I can jump around        ← timestamped element pages
add this to the base: <link>                     ← single item, queue optional
what do I use for lead scraping?                 ← searches your own base
```

### What a filled base looks like

```
your-knowledge-base/
├── Tool Index            ← "I want to… → reach for A · B · C"
├── Coding/               ← subgroups: Workflow, Quality, Frontend…
├── Marketing/            ← Leads & Outreach, SEO, Ads…
├── Videos/               ← Generation, Editing, Code→Video…
├── Agents & Automation/  ← Inboxes, Scheduling, Multi-Agent…
└── …categories grow from YOUR materials
```

## Layout

```
commands/
├── promptos.md                   ← /promptos — first-run setup (connect GitBook + Telegram)
├── process.md                    ← /promptos:process — the standing "process the inbox" contract
└── skills.md                     ← /promptos:skills — catalogue → machine: audit, install, verify
skills/promptos-curator/
├── SKILL.md                      ← the pipeline: intake → depth ladder → filing → indexes
└── references/
    ├── platform-setup.md         ← output/input platform options + exact setup steps
    ├── deep-breakdown.md         ← video mining: transcript, frames, timed deep links
    ├── mining-prompt.md          ← paste-ready "true-mine this" prompt (the gold standard)
    └── page-templates.md         ← copy-paste page anatomies + facet hubs + registration rule
skills/promptos-skillsync/
├── SKILL.md                      ← the four phases: discover → audit → reconcile → install → re-verify
└── references/
    ├── audit-protocol.md         ← runtime-agnostic audit, paste-ready into any fresh session
    └── install-playbook.md       ← source routing table, per-runtime mechanics, installer traps
```

---

Built by [Qbyx](https://github.com/QbyxStudio), sibling of
[`/gloat`](https://github.com/QbyxStudio/gloat). Skill-crafted with Claude.
