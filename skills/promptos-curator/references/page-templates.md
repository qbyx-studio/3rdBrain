# Page Templates

Copy these shapes. Syntax shown is GitBook-flavored markdown (`{% embed %}`, `{% hint %}`);
substitute the target platform's equivalents (plain links / callouts) when elsewhere.

## Table of contents

1. Tool page
2. Workflow / element page (deep breakdown child)
3. Hub page (deep breakdown parent)
4. Prompt page (atomic)
5. Subgroup index page
6. Master Tool Index page
7. Type labels
8. Facet hub page

---

## 1. Tool page

```markdown
---
description: One line; what it is + its edge
---

# Tool Name

> 📦 **Open-Source Repo**   ← correct type label; add "(dormant)" / "(official)" etc. as true

**Use it when:**

| You want to… | This delivers |
| --- | --- |
| Concrete job-to-be-done | What the tool concretely gives |
| Second job (max 3 rows) | … |

**Pairs well with:** [Sibling](sibling.md) (short disambiguation; "same job, but for X")

**Concise summary:**

* 2–4 selective bullets; capabilities, numbers, the hook
* Keep the user's own annotation if they made one: ⭐ flagged **"Must do!!!"**

**Get it:**

{% embed url="https://verified-canonical-link" %}

**See it used (our workflow page):** [Workflow](../topic/workflow.md)   ← only if one exists

**Source video:**

{% embed url="https://original-material-link" %}
```

## 2. Workflow / element page

```markdown
---
description: "Use Case N: outcome in plain words"
---

# UC-N; Outcome Name

> ℹ️ Part of [Hub Name](../path/hub.md) · [▶ 4:13](https://youtu.be/ID?t=253)

**Use it when:**  (2-row table as above)

**Tool page:** [Tool](../topic/tool.md)   ← the standalone tool(s) this workflow uses

## Step-by-step

1. First action exactly as demonstrated ([▶ 4:56](https://youtu.be/ID?t=296))
2. Next step; include verbatim quotes of prompts spoken/typed ([▶ 6:41](…?t=401))
3. …every step timestamped…

{% prompt description="His exact prompt (7:12)" %}
```markdown
The verbatim prompt, untouched.
```
{% endprompt %}

![](../.gitbook/assets/topic/step-screenshot.jpg)

**Pairs well with:** [Our equivalent](…) (platform disambiguation)
```

## 3. Hub page

```markdown
---
description: Source name; every demoed element, timed & broken down
---

# Source; Full Breakdown

> ℹ️ **Info / Reference** (by Creator); every element has its own subpage with steps,
> screenshots and timed links

**Use it when:**  (table)

## 🗺 Element map

| Time | Element | Page |
| --- | --- | --- |
| [0:00](…?t=0) | Concept / setup | [Basics](basics.md) |
| [4:13](…?t=253) | **Use Case 1**; outcome | [UC1](../topic/uc1.md) |
| [4:56](…?t=296) | ↳ sub-element inside UC1 | [Sub-element](../topic/sub.md) |
| …every element, including cross-category ones… |

**Source video:**

{% embed url="https://source" %}
```

## 4. Prompt page (atomic)

```markdown
---
description: What this prompt achieves
---

# Prompt Name

{% hint style="info" %}
This is a **full prompt file**; use it as one piece.
{% endhint %}

{% prompt description="Usage note / variables to edit" %}
```markdown
ENTIRE prompt, byte-for-byte. Never split, trim, or "improve".
```
{% endprompt %}
```

## 5. Subgroup index page

```markdown
---
description: One line for the cluster
---

# Subgroup Name

* [Child A](child-a.md) - one-line blurb
* [Child B](child-b.md) - one-line blurb
```

Register in the table of contents as the parent with children nested beneath it.

## 6. Master Tool Index page

```markdown
---
description: Every tool in this space; one searchable table for brainstorming
---

# Tool Index

> Legend: 🧩 skill · 📦 repo · 🤖 model · 📝 prompt · ⚙️ SaaS/MCP · ℹ️ reference · 🛡️ security

## Pick by scenario

| I want to… | Reach for |
| --- | --- |
| Job-to-be-done | [A](…) · [B](…) · [C](…) |
| …one row per scenario; add a row when a new job appears… |

## <Category name>   (one such table per category)

| Tool | Type | Best for |
| --- | --- | --- |
| [Name](path.md) | 📦 | ≤8-word hook |
```

**Registration rule:** a new page isn't done until it appears in (a) the table of
contents at the right nesting, (b) its category table here, (c) a scenario row if it
serves a new job, and (d) reciprocal cross-links on related pages.

## 7. Type labels

🧩 skill/plugin for an AI assistant · 📦 open-source repo · 🤖 model/LLM ·
📝 prompt/technique · ⚙️ SaaS tool, MCP or connector · ℹ️ info/reference ·
🛡️ security tool. One per page, first thing after the H1, relationships stated
("engine auto-selected by X", "ChatGPT-side equivalent of Y").

## 8. Facet hub page

A facet is a cross-cutting way to browse, independent of topical category. One hub per facet;
it lists every page carrying that facet. On each member page, add a `**Facets:**` line (near
"Pairs well with") linking to each hub the page belongs to.

```markdown
---
description: Every <facet> page in the base — browse by capability, not category
---

# <Facet> · Browse

> 🧭 **Facet hub** — every page that involves <facet>, wherever it's filed. One row per page.

| Page | Type | Category | What it gives you |
| --- | --- | --- | --- |
| [Gauntlet Loop](../coding/gauntlet-loop.md) | 📝 | Coding | One-shot 3D worlds & games via sub-agent critics |
| [3D prompts](../websites/3d.md) | 📝 | Websites | Prompt patterns for Three.js scenes |
| …every page with this facet… |
```

On each member page, near the bottom:

```markdown
**Facets:** [Workflow](../facets/workflow.md) · [3D](../facets/3d.md) · [Game](../facets/game.md) · [Website](../facets/website.md)
```

**Facet vocabulary** (extend as the base grows): Workflow · 3D · Game · Website · Video ·
Image · Skill · Prompt · Agent/Automation · MCP · Voice/Audio. A page has ONE topical category
but as many facets as truly apply. Register all facet hubs under a top-level **"Browse by facet"**
group in the table of contents.
