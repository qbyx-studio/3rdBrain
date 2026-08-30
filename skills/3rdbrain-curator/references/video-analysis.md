# Video analysis routing

Use this for every video material. The goal is evidence-efficient understanding: transcript
first, broad visual orientation second, dense visual inspection only where the content needs it.

## Choose the route

| Material and depth | Route |
| --- | --- |
| Published video, L0/L1, captions carry the useful content | Pull metadata, description and timed platform captions. Read the complete transcript. Inspect frames where captions name a demonstration, prompt, slide, result or unclear term. |
| Screen-heavy video or L2/L3 breakdown | Use the enhanced analysis route when `watch-video` is installed and its smoke test passes. Otherwise use the portable fallback below. |
| Local video with a caption sidecar | Use the same enhanced or portable route against the local file. Treat the sidecar as spoken evidence. |
| Raw footage that the user wants edited into a new video | Route to [Video Use](https://github.com/browser-use/video-use). This is an editing workflow with transcription, cut planning and rendering. It is outside ordinary 3rdBrain curation. |

Video Use's transcript-plus-selective-visuals principle is useful here. Its editing machinery
and paid ElevenLabs transcription solve a separate job, so they are never required for inbox
curation.

## Enhanced analysis with `watch-video`

[`watch-video`](https://github.com/TomGranot/watch-video) retrieves platform captions, builds
timestamped visual indexes and supports dense inspection windows. It uses Python, FFmpeg,
Pillow and yt-dlp. It requires no transcription API key.

1. Download one modest analysis copy with the existing 3rdBrain command, around 480p. Keep the
   caption sidecar beside it with the same filename stem. Do not let another tool download a
   second high-resolution copy.
2. Locate the installed `watch-video` skill and run its `scripts/run.py` commands through that
   skill's private runtime.
3. Acquire the local analysis copy so metadata and sidecar captions are normalized.
4. Run one `overview` pass across the complete runtime. Open every generated contact sheet.
5. Use transcript chapters, scene changes and the overview to identify information-bearing
   windows. Run `dense` passes only for demonstrations, on-screen text, prompts, settings,
   results, contradictions and ambiguous moments.
6. Keep evidence types separate:
   - `spoken`: present in captions or a supplied transcript;
   - `observed`: visible in an inspected frame;
   - `inferred`: reasoned from spoken or observed evidence.
7. Transcribe important on-screen artifacts from full-resolution individual frames. Contact
   sheets locate the moment; they are not the final legibility source.
8. Commit only the few decisive frames used by the pages. Delete downloaded media, contact
   sheets and unused frames after the batch closes.

The enhanced analyzer is an optional adapter. If it is missing, unhealthy or cannot retrieve a
public URL directly, continue through the portable fallback and report the limitation. Never
load cookies, bypass access controls or claim that a transcript proves something was visible.

## Portable fallback

1. Pull metadata, description and timed captions with yt-dlp.
2. Read the full cleaned transcript and map its elements.
3. Download a modest local copy, around 480p.
4. Use FFmpeg to extract frames around every demonstrated artifact and claim that depends on
   visual evidence. Increase sampling density only inside uncertain windows.
5. Label conclusions as spoken, observed or inferred, and preserve timestamps.

## Token and speed expectations

The savings come from avoiding blind frame dumps. Published-video transcripts were already the
3rdBrain default, so an enhanced analyzer does not inherently reduce transcript tokens. Its main
gain is faster, more systematic discovery of relevant visual moments. Coarse contact sheets can
increase image usage when the source is mostly talking-head footage, so use transcript-only
mining for simple sources and dense visual passes only when they can change the page.
