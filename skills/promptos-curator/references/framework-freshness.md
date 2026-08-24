# Framework freshness

Once per task, update the installed/public PromptOS source when reachable and port newer
compatible framework improvements into the base. Never replace base-owned content, taxonomy,
branding, configuration, secrets, or unrelated edits. Verify relevant build/tests and commit
the framework update separately. If the source is unavailable or a safe merge is not possible,
report the pending update and continue with the unchanged base.

Do not call the framework fresh merely because this preflight ran. A `FRESH` result requires a
receipt naming the source commit, every framework difference and its disposition (ported,
adapted, or not applicable), the local commit, complete build/test results, and—when published—
live checks of Discover, release-specific UI behavior, and the deployment manifest. Otherwise
report `UNVERIFIED` or `PENDING` and state exactly what remains.
