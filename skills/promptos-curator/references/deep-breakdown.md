# Deep Breakdown Protocol (Depth L2/L3)

Read this when a material earns the deep treatment: long/dense workflow content
(tutorial videos, multi-demo streams, long articles with many sub-procedures), or the
user explicitly asks to "break it down".

The goal: someone who never watched the source can execute any demoed element from your
pages — and someone who did watch can jump to any moment in seconds.

## Table of contents

1. Acquire the source
2. Mine the content
3. Design the page tree
4. Build the pages
5. Extract standalone tools (L3)
6. Honesty rules

---

## 1. Acquire the source

Work from the actual content — never from the title, thumbnail, or your memory.

**Video (YouTube etc.):**
- `yt-dlp` at modest resolution (480p is plenty for frames):
  `yt-dlp -f "bv*[height<=480]+ba/b[height<=480]" --write-auto-sub --sub-lang en --sub-format vtt -o "src.%(ext)s" <URL>`
  (Corporate AV/proxies can break TLS for Python — `--no-check-certificates` is an
  acceptable fallback for public video downloads.)
- Grab the **description** too — creators often put a chapter list there. If web fetch
  returns only page chrome, open the watch page in a browser tool and expand/read the
  description element; chapters there beat guessing structure from the transcript.
- Parse the VTT into a clean timed transcript: strip tags, dedupe rolling caption lines,
  merge into ~15-second blocks prefixed `[m:ss]`. Read the whole thing before structuring.

**Article/thread:** fetch full text; capture section anchors instead of timestamps.
**Repo:** README + docs; permalink to files/lines instead of timestamps.

## 2. Mine the content

From transcript + chapters, list every element: the major use cases AND the smaller
demonstrations nested inside them (a connector setup inside a use case, a sub-trick
inside a setup). Do not skip the small ones — "he demoed so many things, don't miss any"
is the standing requirement. For each element record: start time, what's demonstrated,
exact steps, any verbatim prompt/command shown or spoken, tools involved.

**Screenshots:** extract 1–3 frames per element at the most informative moments:
`ffmpeg -ss <seconds> -i src.ext -frames:v 1 -q:v 5 out.jpg`
Spot-check a couple visually (not black/transition frames). Commit into the base's asset
convention (e.g. `.gitbook/assets/<topic>/`). Frames showing a full prompt on screen are
gold — transcribe the prompt verbatim into a prompt block on the page.

## 3. Design the page tree

- **Hub page**: what the material is, "Use it when" table, and the **element map** — a
  table of every element: `[m:ss](deep link) | element | link to its page`. Deep links:
  YouTube `https://youtu.be/<id>?t=<seconds>`; articles `#anchor`; repos permalinks.
- **One child page per element.** Nest sub-elements under their use case. Elements whose
  true topic belongs elsewhere in the base get filed in their topical category
  (see the classification rules in SKILL.md) — the hub's map links across categories;
  a hub is a lens, not a silo.

## 4. Build the pages

Each element page (template in `page-templates.md`):
- Standard anatomy (type label, "Use it when", pairs).
- **Step-by-step exactly as demonstrated** — numbered, each step carrying its own
  `[▶ m:ss](…?t=…)` deep link where it happens.
- Screenshots inline at the relevant steps.
- Verbatim prompts/commands in fenced blocks, never paraphrased.
- Source embed at the bottom.

## 5. Extract standalone tools (L3)

Every distinct tool demoed inside a workflow gets its own tool page in its own topical
category — researched and verified like any other intake item (canonical link, what it is
independent of this video). Workflow page ↔ tool page link both ways
("**Tool page:** …" / "**See it used:** …"). Both appear in the master index —
tool row (⚙️/📦) and workflow row (ℹ️) are separate searchable entries.

Judgment calls: name-dropped examples with no demo (mentioned only as "you could connect
X or Y") don't need pages — a mention on the parent page suffices. An underlying
engine/model that a platform auto-selects gets a page only if useful — and its label must
state the relationship ("engine auto-selected by <platform>, not used directly").

## 6. Honesty rules

- Auto-captions garble names — cross-check spellings against on-screen frames or web
  search before writing them down (a caption's "seed dance" was on-screen "Seedance 2.0").
- A chapter title you couldn't mine content for gets a page with the timestamp and
  "watch for details" — not invented steps.
- Costs are real: download + transcript + frames is several times a normal page. When the
  user didn't ask for depth, surface the choice instead of deciding silently either way.
