# 3rdBrain by Qbyx Studio

**Save anything. Find the right thing when work starts.**

[![3rdBrain launch video preview](docs/assets/preview.gif)](https://qbyx-studio.github.io/3rdBrain/)

> [Watch the launch video with sound](https://qbyx-studio.github.io/3rdBrain/). The video was recorded when 3rdBrain carried the former PromptOS name. The workflow remains current. Command names shown in the video reflect the former naming.

3rdBrain turns links, videos, repositories, social threads, documents, prompts, screenshots,
and notes into a searchable working library on your computer. Send material from your phone.
An AI reads the source, verifies it, creates useful pages, and files each page by purpose.

The result answers one practical question: **what can I use for this?**

## The home for saved knowledge

3rdBrain is built for people who save valuable material faster than they can study it. Each
item moves through a complete path:

1. Capture it in a durable inbox.
2. Read the latest message, including later edits.
3. Mine the full source, including video transcripts, screenshots, and timestamps.
4. Create one useful page per distinct tool, workflow, prompt, or idea.
5. File each page by what it helps the reader do.
6. Cross-link related pages and update every index.
7. Confirm what was filed.

Your files remain ordinary Markdown. Git records every change. Manual edits stay authoritative.

## Find knowledge in two ways

The header search gives fast results from every page. **Discover 3rdBrain** provides a full
search workspace with ranked results and facet filters.

Search covers:

- Page titles and headings
- Descriptions and aliases
- Jobs from each "Use it when" table
- Topical sections and complete taxonomy paths
- Facets such as workflow, video, agent, platform, and access model
- Searchable page content

Exact title and phrase matches receive the strongest weight. Related terms, aliases, taxonomy,
facets, and body matches broaden recall. A niche query such as `opportunities` returns pages
whose indexed fields contain or meaningfully map to that term. 3rdBrain searches the knowledge
base you built. Its reach grows with the material, descriptions, aliases, and search cases in
that base.

## What 3rdBrain does

| You do this | 3rdBrain delivers this |
| --- | --- |
| Forward a link from any device | A durable pending item in the local inbox |
| Edit the message or caption later | The latest edit becomes authoritative |
| Process a long tutorial | A source hub, timed element map, and focused child pages |
| Save several workflows from one vendor | Each workflow receives its own purpose-based location |
| Ask what to use for a job | Ranked search results and a scenario-based Tool Index |
| Edit a filed inbox message | The existing page reopens for refresh and receives a new confirmation |
| Edit a page by hand | The next agent run preserves and works around that edit |
| Run a framework workflow | A freshness check ports compatible public improvements with a verification receipt |
| Review aging knowledge | A report of overdue, upcoming, and potentially superseded pages |
| Publish the library | A Cloudflare Pages site with an email allowlist or an open link |

Telegram sends an edited item as `edited_message`. The collector handles both `message` and
`edited_message`, matches them by chat and message ID, and keeps repeated updates idempotent.

## Purpose owns the sidebar

A source, creator, product, or vendor hub acts as a lens and cross-linking page. Every extracted
page keeps its own topical location.

For example, one source can produce pages in Marketing, Engineering, Research, and Local AI.
The source hub links across those sections. Each new page declares `primary_section` and its
complete `taxonomy_path`. Build checks compare those declarations with the staged sidebar.

One page has one primary topical location and may carry many facets.

## Six skills, five direct actions

Claude Code and Codex share the same canonical skill files.

| Purpose | Claude Code | Codex |
| --- | --- | --- |
| First setup | `/3rdbrain` | `$3rdbrain-setup` |
| Process saved material | `/3rdbrain:process` | `$3rdbrain-process` |
| Audit machine skills | `/3rdbrain:skills` | `$3rdbrain-skillsync` |
| Review aging pages | `/3rdbrain:stalecheck` | `$3rdbrain-stalecheck` |
| Publish the site | `/3rdbrain:publish` | `$3rdbrain-publish` |

The sixth skill, `3rdbrain-curator`, is the shared curation engine. The five direct actions load
it automatically whenever they need classification, page templates, deep breakdowns, site
rules, or framework freshness.

### First setup

```text
/3rdbrain
```

Setup creates a local Markdown knowledge base, initializes Git history, builds the reading
site, and optionally connects a Telegram inbox.

### Process saved material

```text
/3rdbrain:process
```

Processing checks framework freshness, repairs inbox capture, reads every pending item, mines
the sources, files pages, updates navigation and search data, verifies the build, and confirms
the result to each submitter.

3rdBrain chooses a format-aware, token-efficient evidence route. It maps each source first,
retrieves the smallest complete evidence set, checks coverage, and expands only when a claim
or source region remains unresolved.

- Videos begin with the complete timed transcript. Visual inspection concentrates on moments
  where prompts, settings, demonstrations and results appear.
- Articles use clean text extraction with beginning, middle and ending checks, plus browser
  fallback for dynamic pages.
- Repositories begin with structure, manifests and documentation. Relevant implementation and
  tests verify claims before filing.
- Social material preserves the original post, author follow-ups, reply branches, edits and
  inaccessible gaps.
- PDFs, EPUBs and Office documents begin with native text and document structure. Rendering is
  selective, and OCR is reserved for scanned or incomplete pages.
- Screenshots, image posts, photographed lecture slides and scans begin with an ordered visual
  map. OCR targets text-bearing regions, while full-resolution inspection resolves diagrams,
  formulas, handwriting and uncertain text.
- Podcasts and audio begin with chapters, show notes and any existing timed transcript. Long
  recordings are mapped and retrieved in focused spans; RSS feeds are indexed before entries or
  enclosures are opened.
- Interactive or login-gated sources begin with structured page text. The agent uses the smallest
  authorized read-only interaction, works through an existing user-controlled session, and
  reports inaccessible states explicitly.

Optional internal helpers may improve acquisition speed or evidence quality. A fresh 3rdBrain
installation keeps portable baseline routes and does not require those helpers.

### Audit machine skills

```text
/3rdbrain:skills
```

SkillSync discovers agent runtimes on the machine. It checks whether each catalogued skill is
present, valid, loaded, and invocable. It then installs or repairs gaps and verifies the result.

### Review aging pages

```text
/3rdbrain:stalecheck
```

Stalecheck reads page dates and produces a review queue. It reports overdue pages, an upcoming
watchlist, and possible superseding versions. The report leaves content unchanged.

### Publish

```text
/3rdbrain:publish
```

Publishing deploys the built site to Cloudflare Pages after explicit consent. Choose an email
allowlist or an open link. The workflow checks the live site from outside and records what a
visitor can access.

## Local by default

The first setup runs on your computer with local files, local Git history, and a local browser
site. Telegram and Cloudflare are optional connections. Their credentials stay in ignored local
configuration files and can be revoked at their providers.

## Page quality

Every newly curated page includes:

- A one-line description
- `primary_section` and complete `taxonomy_path` declarations
- A visible added date
- A precise page type
- A short "Use it when" table
- Verified canonical links
- Reciprocal links to related pages
- Embedded source material
- Timestamps and screenshots when the source contains them

Long-form sources receive one source hub with a timed element map. Each distinct use case
receives its own page. Child pages can live in categories across the knowledge base.

## Framework freshness with receipts

Every direct workflow begins with the same freshness contract. The agent compares the installed
framework with the current public 3rdBrain source, adapts compatible improvements, preserves
base-owned content and configuration, runs relevant tests, and records a receipt.

A `FRESH` receipt names:

- The source commit
- Every detected framework difference
- Each difference's outcome
- The local update commit
- Build and test results
- Live Discover and interface checks when a site is published

Incomplete evidence produces `UNVERIFIED` or `PENDING` with the remaining work stated clearly.

## Install

### Claude Code plugin

```text
/plugin marketplace add qbyx-studio/3rdBrain
/plugin install 3rdbrain@3rdbrain
```

### Direct skill install

Codex uses one canonical shared root:

```bash
mkdir -p ~/.agents/skills
cp -R skills/3rdbrain-* ~/.agents/skills/
```

Claude Code:

```bash
mkdir -p ~/.claude/skills
cp -R skills/3rdbrain-* ~/.claude/skills/
```

Windows PowerShell for Codex:

```powershell
Get-ChildItem skills -Directory -Filter "3rdbrain-*" | ForEach-Object {
  Copy-Item -Recurse -Force $_.FullName "$env:USERPROFILE\.agents\skills\$($_.Name)"
}
```

For Claude Code, use `.claude\skills` as the destination. Restart the agent after copying.

## Repository map

```text
commands/
  3rdbrain.md
  process.md
  skills.md
  stalecheck.md
  publish.md

skills/
  3rdbrain-curator/
  3rdbrain-setup/
  3rdbrain-process/
  3rdbrain-skillsync/
  3rdbrain-stalecheck/
  3rdbrain-publish/

inbox/
  bot.py
  watchdog.ps1
  confirm.py

_site/
  starter/
  tools/
  tests/
  e2e/
```

## Licence

MIT. See [LICENSE](LICENSE). The Qbyx Studio name and Qbyx logo remain the property of Qbyx Studio.

Built by [Sean Cypher](https://github.com/sean-cypher) at
[Qbyx Studio](https://github.com/qbyx-studio). The launch video was created with
[`/gloat`](https://github.com/qbyx-studio/gloat).
