# 3rdBrain by Qbyx Studio

**The inbox for everything you save.**

[![3rdBrain launch video preview](docs/assets/preview.gif)](https://qbyx-studio.github.io/3rdBrain/)

> [Watch the launch video with sound](https://qbyx-studio.github.io/3rdBrain/). It was recorded under the former PromptOS name, so the command names differ. The workflow is current.

You already have a pile of saved links. Videos you meant to watch, repos you meant to read,
threads you screenshotted at midnight. They sit there because reading them is work.

3rdBrain gives that pile an inbox. Send a link from your phone. An AI watches the video, reads
the repo, pulls the transcript and the timestamps, then writes a page about what the thing is
for and files it where you will look for it.

Weeks later you type what you are trying to do, and the page comes back.

## How it works

Send material to your inbox. Each item travels a fixed path:

1. Capture into a durable inbox.
2. Read the latest version of the message, including edits made after sending.
3. Mine the whole source: transcripts, screenshots, timestamps, code.
4. Write one page per distinct tool, workflow, prompt or idea.
5. File each page by the job it helps you do.
6. Cross-link related pages and update every index.
7. Confirm back to you what was filed.

Your library is ordinary Markdown on your own disk. Git records every change. Anything you
edit by hand stays exactly as you wrote it.

## Finding things again

Type the job. "Prepare email replies without auto-sending." "Cheap local worker under a hosted
agent."

Exact wording surfaces immediately. A small local embedding model then reranks by meaning, so
the page you half-remember arrives even when you use different words from the page. Every
result shows why it matched.

Filters narrow by capability, category, access model and platform. Search runs inside your
browser and makes zero LLM calls.

## What you get

- A page per tool, workflow, prompt or idea, written from the source.
- Verbatim prompts and commands, with timestamps back to the exact moment in a video.
- A sidebar organised by purpose, so related work sits together.
- Facets across every page, so one idea is reachable from several angles.
- Indexes and cross-links that update themselves as the library grows.

## Your library is a real site

Setup builds the site and opens it in your browser. It runs on MkDocs with a theme this
project owns, so the library looks like yours from the first page:

- Your logo, favicon and fonts, from `_site/overlay/assets/`.
- Your colour palette and typography, from `_site/overlay/stylesheets/brand.css`.
- A sidebar organised by purpose, plus the Discover search workspace.

`3rdbrain-publish` puts that site on Cloudflare Pages. You choose an email allowlist so only
named people get in, or an open link. Publishing asks for consent every time and verifies the
result from outside afterwards, file by file.

## What 3rdBrain does

| You do this | 3rdBrain delivers this |
| --- | --- |
| Forward a link from any device | A durable pending item in the local inbox |
| Edit the message or caption later | The latest edit becomes authoritative |
| Process a long tutorial | A source hub, a timed element map, and focused child pages |
| Save several workflows from one vendor | Each workflow gets its own purpose-based location |
| Ask what to use for a job | Ranked search results and a scenario-based Tool Index |
| Edit a filed inbox message | The existing page reopens for refresh and gets a new confirmation |
| Edit a page by hand | The next agent run preserves and works around that edit |
| Run a framework workflow | A freshness check ports compatible improvements with a receipt |
| Review aging knowledge | A report of overdue, upcoming and potentially superseded pages |
| Publish the library | A branded Cloudflare Pages site with an email allowlist or an open link |

## Seven skills

| Skill | What it does |
| --- | --- |
| `3rdbrain-setup` | Create a local base and connect the inbox. |
| `3rdbrain-process` | Process everything waiting in the inbox. |
| `3rdbrain-curator` | Turn one source into filed, cross-linked pages. |
| `3rdbrain-publish` | Publish to Cloudflare Pages with access control. |
| `3rdbrain-connect` | Give a person or an agent read-only search access. |
| `3rdbrain-skillsync` | Bring every agent runtime on the machine to parity, then prove it. |
| `3rdbrain-stalecheck` | Report aging pages. It reads, and leaves editing to you. |

## Local by default

Everything lives on your machine as Markdown under Git. Publishing is a separate, explicit
step with its own consent prompt. Access control is yours to set.

## Page quality

Every page carries the job it serves, reproducible steps, exact artifacts, limitations, and a
link back to the source. Timestamps point at the moment a claim was made. Where a source
contradicts itself, the page says so.

A curator can verify any claim in one click, which is what keeps a growing library worth
trusting.

## Framework freshness with receipts

Before content work, 3rdBrain checks itself against this repository. A fingerprint of every
framework-owned file is compared with the last verified receipt. A match is the fast path. A
change triggers a reconcile, and the receipt is written only after the build, the tests and the
live checks pass, with a disposition recorded for every differing file.

The receipt is evidence. It names the upstream commit, your commit, and what happened to each
difference.

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
commands/          slash commands
skills/            the seven skills and their references
inbox/             the capture bot
_site/             the private site build, tools and tests
_site/starter/     the template a new base starts from
```

## Licence

MIT. See [LICENSE](LICENSE). The Qbyx Studio name and Qbyx logo remain the property of Qbyx Studio.

Built by [Sean Cypher](https://github.com/sean-cypher) at
[Qbyx Studio](https://github.com/qbyx-studio). The launch video was created with
[`/gloat`](https://github.com/qbyx-studio/gloat).
