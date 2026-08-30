# Audio, podcasts and RSS

Use this route for podcasts, voice notes, interviews, recordings, audio enclosures and RSS or
Atom feeds. Treat show notes, transcripts and feed descriptions as separate evidence layers.

## Audio and podcast route

1. **Map first.** Capture the canonical source, title, speakers when supplied, duration,
   publication/update date, chapters, show notes and transcript availability.
2. **Prefer an existing timed transcript.** Keep speaker labels and timestamps. Clean repeated
   auto-caption fragments without changing meaning. Verify exact quotations against the audio
   or a trustworthy supplied transcript.
3. **Transcribe only when needed.** If no usable transcript exists, use an available local or
   user-authorized speech-to-text route. Chunk long audio by chapters or natural boundaries,
   keep timestamps, detect language, and label speakers conservatively. Do not silently send
   private audio to a cloud provider or trigger a paid service.
4. **Retrieve evidence selectively.** Build a chapter/topic map, search the transcript, and load
   only the relevant spans plus enough surrounding context. Expand when a claim, transition or
   source region remains unresolved. Retain the complete transcript outside model context when
   possible.
5. **Preserve meaningful non-speech evidence.** Note music, silence, demonstrations, audience
   reactions or sound cues only when they affect interpretation.

## RSS and Atom route

1. Parse feed-level metadata and a compact item index before opening entries. Preserve canonical
   item links, GUIDs, enclosure URLs, publication dates and update dates.
2. Distinguish a feed summary from the linked article or episode. Fetch the enclosure, transcript
   or article only when the item is selected for curation or the feed text is incomplete.
3. Follow pagination or archive links when the requested scope requires older items. Deduplicate
   redirected links, repeated GUIDs and the same item appearing in multiple feeds.
4. Treat the newest accessible revision as authoritative while retaining material corrections
   or update notes.

## Completeness gate

For audio, reconcile the transcript with duration, chapters, beginning and ending, and spot-check
representative segments against the recording. For feeds, reconcile visible item counts,
pagination, date range and selected enclosures. State missing transcripts, inaccessible audio,
truncated feeds and uncertain speaker attribution. A successful command or non-empty transcript
does not by itself prove complete extraction.
