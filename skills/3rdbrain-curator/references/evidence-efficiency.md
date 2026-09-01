# Evidence efficiency

Acquisition tools often use no LLM tokens. Captions, HTML, repository files, native document text,
local OCR and local speech-to-text become expensive when the same evidence is repeatedly sent to an
LLM. This protocol reduces repetition while preserving complete mining.

## Use the local evidence runtime

The tool uses the Python standard library and needs no account, API key, server, model or package.

```text
python _site/tools/evidence_runtime.py prepare <extracted-text-file> \
  --source <canonical-source> --kind <kind> --mode full \
  --output <scratch>/evidence-pack.json --receipt <scratch>/efficiency-receipt.json
```

Supported kinds are `video`, `web`, `repository`, `social`, `document`, `image`, `audio`,
`interactive` and `note`.

Use `--mode full` for deep mining. It emits every locator-preserving chunk once in bounded batches.
Read every batch and record every reviewed chunk in the evidence ledger.

Use `--mode selective --query "<latest remarks>"` for a narrow enrichment or verification task. It
returns ranked evidence plus beginning, middle and ending coverage. Widen the query, increase
`--top`, or switch to full mode when a claim, contradiction or coverage check remains unresolved.

## Cache rules

The cache key contains the acquired content hash, material kind and extraction-pipeline version.
An identical source can reuse its evidence map after a file move. Edited content and a changed
pipeline version produce a miss. Missing or corrupt cache data also produces a miss.

For mutable remote sources, check a revision, edit timestamp, ETag or last-modified value when the
platform provides one. A cache hit saves LLM reprocessing. It does not prove that a remote source
has remained unchanged.

Cache only acquired evidence, chunks, maps and verified ledgers. Generate pages from current
evidence. Never cache a model response as authority.

## One mine, many pages

After reading the selected or full evidence pack, create a ledger that cites evidence chunk IDs.
Validate it before page writing:

```text
python _site/tools/evidence_runtime.py validate-ledger \
  <scratch>/ledger.json <scratch>/evidence-pack.json
```

For full mode, validation requires every source chunk to appear in `reviewed_chunk_ids`. Page
writing then uses the compact ledger. Return to raw material only for a named missing fact or
artifact.

## Receipt

The receipt records estimated raw and selected input, cache status, chunk coverage and pipeline
version. It stores no credentials or model output. Provider-reported usage may be added by the
calling product when available. Estimated tokens are evidence for comparison, not a billing claim.
