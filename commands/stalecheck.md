---
description: Run the PromptOS staleness check (report-only) and present the review queue. Never edits, banners or deletes anything.
---

# /promptos:stalecheck, surface pages that may be aging out

Run the staleness engine against the base and present the result. This is **report-only**: it
reads each page's `🗓️ Added` date, its facet class and version signals, then prints a review
queue. It must never edit, banner, delete or merge anything on its own.

## Steps

1. Run the engine from the base folder:

   ```bash
   python _site/tools/stalecheck.py --top 30
   ```

   Optional flags: `--top N` for list length, `--out FILE` to save the report. `--links` and
   `--flag` do not exist yet. If the user wants dead-link checking or banners, say so and
   offer to build them rather than pretending they are there.

2. Present the output in three parts, most actionable first:

   - **OVERDUE**, where age has passed the class threshold. Roundup and Model pages at 75
     days, medium tools around 180 to 210, durable techniques such as Prompt, Workflow, Skill
     and Agent at 300 to 330. On a young base this is usually empty; say so plainly.
   - **WATCHLIST**, the pages closest to their threshold, which is what ages next.
   - **SUPERSEDE?**, heuristic pairs where a higher version of the same product name exists
     elsewhere in the base. These are candidates to **verify by hand**, not facts. A base that
     updates versions in place will show none, and that is correct rather than a miss.

3. For anything flagged, recommend an action and wait for the user's say-so:

   | Signal | Recommended action |
   | --- | --- |
   | Stale ranking or benchmark | Refresh the one line verdict, keep the verbatim prompts. The recipe is the durable asset; the verdict is the perishable part. |
   | Dead tool, shut down | Archive candidate, the user confirms |
   | Superseded by a newer internal page | Merge, or add a `superseded by ->` line pointing at the newer page |

   Deletion and merging are always the user's decision. **Never remove a page on your own.**
   The base is a memory, and a stale ranking costs less than a lost recipe.

4. If the user approves changes, make them as ordinary edits and commit them. Where the base
   syncs with another platform, pull before editing so their manual edits stay authoritative.

## Notes

- The threshold comes from a page's **most volatile facet**, so a mis-tagged page ages at the
  wrong speed. If the report looks wrong for a page, check its facets before its date.
- Pages with no `🗓️ Added` line fall back to their first commit date from git history, so the
  report still works on a base that predates the convention.
- The engine writes nothing. Running it on a whim is free.
