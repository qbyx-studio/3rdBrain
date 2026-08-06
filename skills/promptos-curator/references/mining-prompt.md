# The True-Mining Prompt

A paste-ready instruction that forces the full mining pass on a single material. Use it (or
send it verbatim to an agent) whenever a link must be TRUE-mined, not summarized. It encodes
the gold standard from `SKILL.md` §2 and `deep-breakdown.md`. The reference result this prompt
aims to reproduce is the Gauntlet Loop page.

```markdown
TRUE-MINE this material into my knowledge base. Do NOT summarize-and-link. Do NOT work from
the title or thumbnail. Work only from the actual content.

SOURCE: <paste link>

Do all of this:

1. ACQUIRE THE REAL CONTENT.
   - Video: download it (yt-dlp, ~480p is fine) and pull the auto-subtitles as a timed
     transcript. Also read the description/pinned comment for a chapter list and any links
     the creator shares. Read the whole transcript before writing anything.
   - Article/thread/repo: fetch the full text / README + docs, not the preview.

2. LIST EVERY ELEMENT, big and small. Every use case, and every sub-demo nested inside it
   (a connector setup, a one-off trick, a settings tweak). Miss nothing. For each: its
   timestamp, what is shown, the exact steps, the tools involved.

3. CAPTURE EVERY ARTIFACT VERBATIM. Every prompt, command, config, or code snippet the creator
   shows on screen or reads aloud gets transcribed WORD-FOR-WORD into its own block, tagged with
   its timestamp (e.g. 3:26). If the video shows three prompts, I want three verbatim blocks, not
   one merged "template". When the auto-caption garbles it, read it off the on-screen frame. Never
   substitute your own guess for what was shown.

4. SCREENSHOT THE MOMENTS THAT CARRY INFORMATION. Extract frames where a full prompt, a result,
   or a settings panel is visible (ffmpeg at the right seconds), spot-check they aren't black/
   transition frames, and embed them inline at the step they illustrate. Show, don't describe.

5. DISTILL THE REUSABLE PRINCIPLE. In plain words, name the transferable shape the creator is
   teaching (not just the examples) so I can reuse it on my own goal. Where useful, add a
   ready-to-reuse meta-prompt built from that principle, clearly marked as the distilled template,
   separate from (never a replacement for) the verbatim examples.

6. VERIFY EVERY LINK. Only include canonical links you confirmed exist (the real repo/product/
   docs), found by searching the tool NAMES from the content, never guessed from the title.

7. FILE IT to the right topical category (what it's FOR, never which app it came from), at the
   right depth (hub + one child page per element if it's a multi-demo workflow; standalone tool
   pages for each distinct tool demoed inside it, linked both ways). Tag every FACET it carries
   (Workflow / 3D / Game / Website / Video / Image / Skill / Prompt / Agent / MCP) and add it to
   each facet hub. Register it in the sidebar, the master index (scenario row + category table),
   and add reciprocal cross-links on related pages.

8. TIMESTAMP EVERY CLAIM and embed the original source at the bottom.

The test: someone who never opened the source can reproduce every demoed thing from my page,
and someone who did can jump to any moment in seconds. A summary + a link + one guessed template
is a FAILURE even if nothing on it is wrong. Match the depth of the Gauntlet Loop page.

When done, tell me exactly what you filed, where, and paste the timestamps of every verbatim
artifact you captured so I can spot-check.
```
