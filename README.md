# PromptOS by Qbyx

**Saved links, made findable.**

[![PromptOS launch video preview, click to watch with sound](docs/assets/preview.gif)](https://qbyxstudio.github.io/PromptOS/)

> **▶ [Watch the launch video (with sound)](https://qbyxstudio.github.io/PromptOS/)**, made with [`/gloat`](https://github.com/QbyxStudio/gloat), of course.

You save a link because it matters. Six weeks later you need it, and it sits buried under
four thousand other messages. The link still exists. Finding it costs more than
rediscovering the tool from scratch.

PromptOS closes that gap. You forward links from your phone. An AI researches each one,
writes it a proper page, and files it into a library built around one question:
**what do I use for this?**

Findable is the whole product. Everything below serves it.

## Built for the hoarders

This is for people who collect AI tools, prompts, repos, and long tutorial videos faster
than they can read them. If your bookmarks, your chat history, and three note apps each
hold pieces of the same mess, you are the user.

## Runs on your computer

Setup finishes on your own machine. No accounts. No tokens. No card. No cloud.

```bash
/promptos
```

That builds your knowledge base locally and opens it in your browser. Your notes stay on
your disk, private by construction.

When you want it on your phone, one more command publishes it. That step is opt in, it
warns you clearly, and it asks who is allowed in. See [Publishing](#publishing-optional).

## What actually happens

| You | PromptOS |
|---|---|
| Forward a link from any device | Captures it into a durable local queue |
| Say "process" | Researches each item, finds the verified canonical link, classifies it |
| Send a dense 30 minute tutorial | Mines transcript and screenshots, builds a hub plus one page per demoed element, each with a timestamped deep link |
| Ask "what do I use for X?" months later | The Tool Index answers in one table |
| Edit a page by hand | Your edit wins; the AI works around it |
| Want your chat tidy | `/cleanup` deletes only what has already been filed, only when you say so |
| Ask "is every skill in my base actually installed?" | `/promptos:skills` checks every agent on the machine, installs what is missing, and verifies it landed |
| Wonder which pages have gone stale | `/promptos:stalecheck` prints a review queue by age and class, and changes nothing |
| Send a link, then a note about how to file it | The note is read first, and it overrides the default page shape |

Every page opens with the date it was added, `🗓️ Added 2026-08-17`, which doubles as the age
signal `/promptos:stalecheck` reads. After that every page follows one shape: a type label (🧩 skill · 📦 repo · 🤖 model · ⚙️ SaaS ·
📝 prompt), a "Use it when" table, a short summary, the verified link, and the original
source embedded. Facts pulled from videos carry timestamps, so any claim is checkable in
seconds.

## The five commands

### `/promptos`

First run. Builds the base on your computer, sets up your inbox, opens the site. Ask it
questions in plain words; it does the terminal work for you.

### `/promptos:process`

The standing contract. Run it whenever you want your queue filed.

```text
you    → forward 5 links to your bot from your phone
you    → /promptos:process
skill  → self-heals the inbox, deep-mines each item, files, cross-links, indexes
bot    → "✅ Processed 5 items. Send /cleanup to tidy up."
```

Steer it in plain language:

```text
process my queue
this one is dense, break it down fully           ← forces the deep treatment
break down by timing so I can jump around        ← timestamped element pages
add this to the base: <link>                     ← single item, queue optional
what do I use for lead scraping?                 ← searches your own base
```

### `/promptos:skills`

Your base catalogues skills. This checks whether they are actually installed on the machine,
across every agent runtime it finds, then installs and repairs what is missing.

Installed, loaded and typeable are three separate states. It checks all three, because a
skill can be valid on disk and still be missing from the menu you type into.

### `/promptos:stalecheck`

Your base ages. A model ranking from six months ago is a liability, and you will not notice
on your own.

This reads the `🗓️ Added` date on every page and prints a review queue in three parts: what is
**overdue** against its class, a **watchlist** of what ages next, and heuristic
**supersede** pairs where a newer version of the same product exists elsewhere in your base.

Roundups and model pages age fastest at 75 days. Tool pages sit near 180. Prompts, workflows
and techniques last 300 or more, because a recipe stays useful long after a ranking rots.

It is **report only**. It never edits, banners, merges or deletes. It recommends, you decide.
A stale ranking costs less than a lost recipe.

### `/promptos:publish`

Puts the base online. Covered below.

## Your inbox

Default is a **Telegram bot**, created in about sixty seconds through @BotFather. Forward
anything to it from any device, at any hour, and it holds the item until you process it.
The token is revokable at any time with BotFather `/revoke`, and only accounts on your
allowlist are accepted.

Plain chat paste works too, with zero setup, if you want to start before making a bot.

## Publishing (optional)

`/promptos:publish` hosts your base on Cloudflare Pages, free. Before anything uploads it
states plainly that your notes are going onto the internet, then asks how you want it
guarded:

| Choice | Who gets in |
|---|---|
| **Email allowlist** | Only the addresses you name, through a sign in screen |
| **Open link** | Anyone who has the address |

After deploying it tests the site from outside and reports exactly what a stranger sees.
A published base that quietly leaks is a failure, so that check is part of the command.

## The look

Every base ships with the same design system, tuned over a real library of 330+ pages.

| | |
|---|---|
| Ground | Deep night, near black |
| Accent | One electric colour, used sparingly |
| Surfaces | Glass panels, hairline borders, soft glow on what matters |
| Display type | Space Grotesk, tight tracking |
| Body type | Glacial Indifference, self hosted |
| Technical type | JetBrains Mono for labels and code |
| Search | Instant, offline, section level results |

Prompts render as collapsible blocks with a copy button. Videos render as players. Tags
generate their own browse pages, with counts that stay correct on their own.

Swap the logo, the palette, or the fonts in one file whenever you want.

## What a filled base looks like

```
your-knowledge-base/
├── Tool Index            ← "I want to… → reach for A · B · C"
├── Browse by facet       ← generated: capability, price, platform
├── Coding/               ← subgroups: Workflow, Quality, Frontend…
├── Marketing/            ← Leads & Outreach, SEO, Ads…
├── Videos/               ← Generation, Editing, Code→Video…
├── Agents & Automation/  ← Inboxes, Scheduling, Multi-Agent…
└── …categories grow from YOUR materials
```

## Guardrails

Each one exists because it failed in production first.

- Every tool lands in its true topical category, never a catch all bucket.
- Every link is verified before it reaches a page.
- Full prompt files stay whole on one page.
- Your manual edits are authoritative, always.
- Deletion happens on your command alone.
- A page counts as done once it appears in every index.

## Install

```bash
/plugin marketplace add QbyxStudio/PromptOS
/plugin install promptos@promptos
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

## Layout

```
commands/
├── promptos.md                   ← /promptos, first run setup on your computer
├── process.md                    ← /promptos:process, the standing inbox contract
├── skills.md                     ← /promptos:skills, catalogue against machine
├── stalecheck.md                 ← /promptos:stalecheck, age review, report only
└── publish.md                    ← /promptos:publish, put the base online
skills/promptos-skillsync/
├── SKILL.md                      ← runtime discovery, install, verify
└── references/
    ├── audit-protocol.md         ← what counts as installed, loaded, typeable
    └── install-playbook.md       ← per runtime mechanics and installer traps
skills/promptos-curator/
├── SKILL.md                      ← the pipeline: intake → depth ladder → filing → indexes
└── references/
    ├── site-build.md             ← the MkDocs build, theme, and design system
    ├── platform-setup.md         ← inbox and hosting options, with exact steps
    ├── deep-breakdown.md         ← video mining: transcript, frames, timed deep links
    ├── mining-prompt.md          ← paste ready "true mine this" prompt
    └── page-templates.md         ← page anatomies, facet hubs, registration rule
```

## Why it exists

I FOMO-ed. Hard. Every AI influencer post felt too important to lose, so I flooded my own
WhatsApp and Telegram with forwarded links. Saved, then never seen again. So I built this
to solve my own problem.

My base runs 330+ pages today: every tool on its own page, fifteen topical sections,
generated facet hubs, and deep mined tutorials where every demoed element has its own
page with screenshots and jump links. When I ask "what do I use for lead scraping", the
answer is one search away with the verified link sitting right there.

Yours will look like whatever you feed it.

## Licence

MIT, see [LICENSE](LICENSE). The Qbyx name and logo stay the property of Qbyx Studio;
swap them for your own if you fork this.

---

Built by [Qbyx](https://github.com/QbyxStudio), sibling of
[`/gloat`](https://github.com/QbyxStudio/gloat). Skill-crafted with Claude.
