# Framework freshness

Run once per task before content work. Fetch the current default branch of the authoritative
public source, `https://github.com/qbyx-studio/3rdBrain`, then run the portable probe:

```text
python _site/tools/framework_freshness.py probe \
  --source-root <current public checkout> \
  --local-root <this base> \
  --receipt <this base>/.framework-freshness.json
```

The probe compares the authoritative commit, a SHA-256 fingerprint of every framework-owned
surface, and the fingerprint of the locally adapted framework against the last verified receipt.
Base content is outside that fingerprint. A content edit therefore keeps a valid cache hit, while
any public or local framework change invalidates it automatically.

- `FRESH` with no reasons is the fast path. Report the cached receipt and continue. Never repeat
  a full reconciliation against that exact verified source and local framework state.
- `RECONCILE_REQUIRED` means fetch and compare every framework-owned surface: `commands/`,
  `skills/`, `inbox/`, `_site/` code and tests, plus starter assets. Port or adapt each compatible
  improvement. Preserve base-owned content, taxonomy, branding, configuration, secrets and
  unrelated edits.

After reconciliation, verify the complete relevant build and tests and commit the framework
update separately. Record a new receipt only after those checks pass. Supply a JSON list of every
difference with `path`, `disposition` (`ported`, `adapted`, or `not_applicable`) and reason, plus
JSON verification evidence containing `build_passed`, `tests_passed`, `published`, and
`live_checks_passed` when published:

Generate the exact path set with `compare`, or create a reviewable disposition draft with
`draft --output <differences.json>`. Review that draft before recording it. The `record` command
refuses `FRESH` when any real source/local difference is missing or an extra path is claimed.

```text
python _site/tools/framework_freshness.py record \
  --source-root <current public checkout> \
  --local-root <this base> \
  --receipt <this base>/.framework-freshness.json \
  --differences <differences.json> \
  --verification <verification.json>
```

The receipt is machine-local and ignored by git. Corruption or missing evidence becomes a cache
miss. If the source is unreachable or a safe adaptation is unavailable, report the pending update
and continue with the unchanged base.

Do not call the framework fresh merely because this preflight ran. A `FRESH` result requires a
receipt naming the source commit, every framework difference and its disposition (ported,
adapted, or not applicable), the local commit, complete build/test results, and—when published—
live checks of Discover, release-specific UI behavior, and the deployment manifest. Otherwise
report `UNVERIFIED` or `PENDING` and state exactly what remains.
