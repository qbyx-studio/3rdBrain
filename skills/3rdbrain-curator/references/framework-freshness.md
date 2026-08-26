# Framework freshness

Once per task, fetch the current default branch of the authoritative public source,
`https://github.com/qbyx-studio/3rdBrain`, and compare every framework-owned surface: `commands/`,
`skills/`, `inbox/`, `_site/` code and tests, plus starter assets. Port each newer compatible
improvement into the base. Preserve base-owned content, taxonomy, branding, configuration,
secrets, and unrelated edits. Verify the complete relevant build and tests, then commit the
framework update separately. If the source is unreachable or a safe adaptation is unavailable,
report the pending update and continue with the unchanged base.

Do not call the framework fresh merely because this preflight ran. A `FRESH` result requires a
receipt naming the source commit, every framework difference and its disposition (ported,
adapted, or not applicable), the local commit, complete build/test results, and—when published—
live checks of Discover, release-specific UI behavior, and the deployment manifest. Otherwise
report `UNVERIFIED` or `PENDING` and state exactly what remains.
