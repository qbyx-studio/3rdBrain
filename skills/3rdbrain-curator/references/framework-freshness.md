# Framework freshness

Run once per task before content work. Fetch the current default branch of the authoritative
public source, `https://github.com/qbyx-studio/3rdBrain`, then run
`_site/tools/framework_freshness.py probe` with the current public checkout, this base and the
ignored `.framework-freshness.json` receipt.

The probe checks the authoritative commit, its framework SHA-256 fingerprint and the locally
adapted framework fingerprint. A `FRESH` result with no reasons is the compulsory fast path:
report the cached receipt and continue without repeating reconciliation. Ordinary content edits
do not invalidate it. Any public or local framework change returns `RECONCILE_REQUIRED`.

On a miss, compare `commands/`, `skills/`, `inbox/`, `_site/` code and tests, plus starter assets.
Port or adapt every compatible improvement while preserving content, taxonomy, branding,
configuration, secrets and unrelated edits. Verify the complete build and tests, commit the
framework update separately, then use the tool's `record` command with every difference and its
`ported`, `adapted` or `not_applicable` disposition plus build/test and published live-check
evidence. Generate the path set with `compare`, or create and review a disposition draft with
`draft --output <differences.json>`; `record` rejects missing or extra paths.
Record only after evidence passes. Corrupt or incomplete receipts are cache misses.

If the source is unreachable or safe adaptation is unavailable, report the pending update and
continue with the unchanged base.

Do not call the framework fresh merely because this preflight ran. A `FRESH` result requires a
receipt naming the source commit, every framework difference and its disposition (ported,
adapted, or not applicable), the local commit, complete build/test results, and—when published—
live checks of Discover, release-specific UI behavior, and the deployment manifest. Otherwise
report `UNVERIFIED` or `PENDING` and state exactly what remains.
