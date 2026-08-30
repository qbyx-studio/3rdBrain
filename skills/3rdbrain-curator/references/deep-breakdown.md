# Deep Breakdown Protocol (Depth L2/L3)

Scope note: transcript mining alone (subtitles, seconds of work) is NOT this protocol;
it is mandatory intake for every video at every depth level. This file is the FULL
treatment: downloads, frames, per-element pages.

Read this when a material earns the deep treatment: long/dense workflow content
(tutorial videos, multi-demo streams, long articles with many sub-procedures), or the
user explicitly asks to "break it down".

The goal: someone who never watched the source can execute any demoed element from your
pages; and someone who did watch can jump to any moment in seconds.

**The bar (the Gauntlet Loop page is the reference).** A breakdown is done only when it has:
every prompt/command/config the creator shows or says, transcribed **verbatim** into its own
block at its timestamp (three demoed prompts → three blocks, never one merged "template");
the **reusable principle** named in plain words (what shape the viewer can reuse, not just the
specific examples); screenshots of the information-carrying moments extracted and **embedded**;
and a timestamp on every claim. A hub-plus-summary with a link is NOT a breakdown, it is the
failure this protocol exists to prevent, even when nothing on it is factually wrong.

## Table of contents

1. Acquire the source
2. Mine the content
3. Design the page tree
4. Build the pages
5. Extract standalone tools (L3)
6. Honesty rules

---

## 1. Acquire the source

Work from the actual content; never from the title, thumbnail, or your memory.

**Video (YouTube etc.):**
- Follow `video-analysis.md`. Use its transcript-first, coarse-to-fine visual route when the
  optional enhanced analyzer is available, and its portable fallback when it is not.
- `yt-dlp` at modest resolution (480p is plenty for frames):
  `yt-dlp -f "bv*[height<=480]+ba/b[height<=480]" --write-auto-sub --sub-lang en --sub-format vtt -o "src.%(ext)s" <URL>`
  (Corporate AV/proxies can break TLS for Python; `--no-check-certificates` is an
  acceptable fallback for public video downloads.)
- Grab the **description** too; creators often put a chapter list there. If web fetch
  returns only page chrome, open the watch page in a browser tool and expand/read the
  description element; chapters there beat guessing structure from the transcript.
- Parse the VTT into a clean timed transcript: strip tags, dedupe rolling caption lines,
  merge into ~15-second blocks prefixed `[m:ss]`. Read the whole thing before structuring.

**Article:** follow `web-analysis.md`, fetch the complete text and capture section anchors
instead of timestamps. Route social posts and comment threads separately.
**Social thread:** follow `social-analysis.md`; preserve post, replies and branch locators.
**Repo:** follow `repository-analysis.md`; use immutable file/line permalinks instead of timestamps.
**Document:** follow `document-analysis.md`; use page, chapter, slide or sheet locators.

## 2. Mine the content

From transcript + chapters, list every element: the major use cases AND the smaller
demonstrations nested inside them (a connector setup inside a use case, a sub-trick
inside a setup). Do not skip the small ones; "he demoed so many things, don't miss any"
is the standing requirement. For each element record: start time, what's demonstrated,
exact steps, any verbatim prompt/command shown or spoken, tools involved.

**Capture every artifact verbatim.** Every prompt, command, config, or code block that appears
on screen or is read aloud is a first-class asset: transcribe it word-for-word (from the frame
when the auto-caption garbles it) into its own fenced/prompt block on the relevant page, tagged
with its timestamp. Never merge several distinct demoed prompts into one paraphrased template,
and never replace a shown prompt with your own guess of what it "probably" said. If the creator
also shares the artifact in a linked article/description, reconcile the two and keep the exact text.

**Distill the reusable principle.** Alongside the verbatim examples, state the transferable shape
in plain words, the thing the viewer is meant to reuse on their own goal (e.g. Gauntlet Loop's
"task → build-method → bar-to-hit" structure and "a bar must be named, inspectable, decisive").
The examples prove it; the principle is what makes the page useful beyond this one video. Where it
helps, add a ready-to-reuse meta-prompt built from the principle, clearly marked as the distilled
template (separate from the verbatim examples, never a substitute for them).

**Screenshots:** use the visual index from `video-analysis.md` to locate the informative
windows, then keep 1–3 decisive frames per element. With the portable fallback, extract them
directly:
`ffmpeg -ss <seconds> -i src.ext -frames:v 1 -q:v 5 out.jpg`
Spot-check a couple visually (not black/transition frames). Commit into the base's asset
convention (`.assets/<topic>/`, or `.gitbook/assets/<topic>/` on a GitBook base). Frames showing a full prompt on screen are
gold; transcribe the prompt verbatim into a prompt block on the page.

## 3. Design the page tree

- **Hub page**: one page for the source video or article, with what the material is, a
  "Use it when" table, and the **timed element map**; a
  table of every element: `[m:ss](deep link) | element | link to its page`. Deep links:
  YouTube `https://youtu.be/<id>?t=<seconds>`; articles `#anchor`; repos permalinks.
- **One child page per distinct use case.** Nest true sub-elements within that use case's
  page. Every child declares its own full `taxonomy_path` and is filed in the topical category
  matching what it is for, even when that differs from the source hub's category. The hub's
  map links across categories; a source, creator, product, or vendor hub is a lens and
  cross-linking page, not a sidebar silo.

## 4. Build the pages

Each element page (template in `page-templates.md`):
- `taxonomy_path` matching every level of its actual `SUMMARY.md` ancestry.
- Standard anatomy (type label, "Use it when", pairs).
- **Step-by-step exactly as demonstrated**; numbered, each step carrying its own
  `[▶ m:ss](…?t=…)` deep link where it happens.
- Screenshots inline at the relevant steps.
- Verbatim prompts/commands in fenced blocks, never paraphrased.
- Source embed at the bottom.

Create `breakdowns/<source-id>.yml` with one uniquely identified/timestamped element per child,
including its `page`, `page_type`, and `taxonomy_path`. The build verifies every child exists
and that hub and child link to each other.

As soon as each child is written, run the touched-page gate with the child, hub and manifest.
Do not continue to the next child until its declared taxonomy, both hub directions and video
source embed pass. This keeps a large breakdown from accumulating the same structural mistake
across every child. The final full build remains mandatory.

## 5. Extract standalone tools (L3)

Every distinct tool demoed inside a workflow gets its own tool page in its own topical
category; researched and verified like any other intake item (canonical link, what it is
independent of this video). Workflow page ↔ tool page link both ways
("**Tool page:** …" / "**See it used:** …"). Both appear in the master index,
tool row (⚙️/📦) and workflow row (ℹ️) are separate searchable entries.

Judgment calls: name-dropped examples with no demo (mentioned only as "you could connect
X or Y") don't need pages; a mention on the parent page suffices. An underlying
engine/model that a platform auto-selects gets a page only if useful; and its label must
state the relationship ("engine auto-selected by <platform>, not used directly").

## 6. Honesty rules

- Auto-captions garble names; cross-check spellings against on-screen frames or web
  search before writing them down (a caption's "seed dance" was on-screen "Seedance 2.0").
- A chapter title you couldn't mine content for gets a page with the timestamp and
  "watch for details"; not invented steps.
- Costs are real: download + transcript + frames is several times a normal page. When the
  user didn't ask for depth, surface the choice instead of deciding silently either way.
