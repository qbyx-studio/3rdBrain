# Install playbook

How to install a catalogued skill correctly, on every runtime present, and prove it landed.

## Route by what the source contains

Open the source before installing. The catalogue page's label is a hint, not a contract — a
page titled "Skill" routinely points at an MCP server, a CLI, or a library.

| Source contains | Route |
| --- | --- |
| `SKILL.md` at root, or under `skills/` | cross-agent skills CLI (below) |
| `.claude-plugin/marketplace.json` | plugin marketplace: add marketplace, then install by plugin name |
| Both | install the plugin; it carries its own skills |
| A docs site the installer accepts as a source | pass the URL to the skills CLI |
| Markdown prompts, no `SKILL.md` | package it yourself (below) |
| A CLI, MCP server, library, or gated/manual download | **NOT-A-SKILL** — record with the reason, never fake an install |

Verify the plugin's declared name from its `marketplace.json` rather than trusting the
catalogue. Names drift; a page can outlive a rename and send you to an id that no longer
exists.

## Cross-agent skills CLI

```bash
npx skills add <repo-or-url> -g -a <agent> -s '*' -y
```

Three traps, all of which fail quietly:

- **`-a` takes exactly one agent.** `-a claude-code,codex` is rejected outright.
  `-a "claude-code codex"` is rejected. Repeated `-a` flags silently honor only the first —
  no warning, and it reports success. **Run one pass per runtime.**
- **A pass can be a no-op while reporting success.** The Codex pass on Windows prints
  `copy → Codex ✓` and writes nothing to `~/.codex/skills`. Always confirm on disk after.
- **`-l` lists a repo's skills without installing.** Use it first — repos routinely carry far
  more skills than the catalogue page mentions.

## Bring every runtime to parity

Runtimes that were skipped, or whose installer pass no-opped, get the skills mirrored in by
hand from the shared store. Symlinks are enough; the target only needs a readable `SKILL.md`.

Two sources must be mirrored, and the second is the one people miss:

1. The shared skills store and each runtime's own skills directory.
2. **Skills that ship inside installed plugins.** These live under the plugin cache, not the
   skills directory, so a runtime without a plugin layer never sees them. Mirror from the
   *installed* plugin cache only — never from the marketplace listing, which contains every
   available plugin, not the installed ones.

On name collision, prefix with the plugin name rather than overwriting. Skip any runtime's
internal, non-skill directories.

## Packaging a source that ships no SKILL.md

Plenty of genuinely useful catalogue entries are prompt libraries. Do not skip them and do
not claim they installed. Package them:

- `SKILL.md` with `name` and a `description` written for retrieval — state the concrete
  situations that should trigger it, not just what it is.
- Move the original material to `references/`, unedited.
- Keep `SKILL.md` short and put the bulk in references; it is loaded on match, not up front.
- Attribute the upstream source and link it.

## GitHub rate limits masquerade as auth failures

Anonymous GitHub traffic is capped at 60 requests/hour, shared across plain `git clone` and
any installer that clones. On exhaustion, git reports:

```
could not read Username for 'https://github.com': terminal prompts disabled
Authentication failed for 'https://github.com/<owner>/<repo>.git'
```

This is indistinguishable from a genuine permissions error and will send you chasing a
credential problem that does not exist. Check the limit before diagnosing:

```bash
curl -s https://api.github.com/rate_limit
```

If exhausted: clone with a token, then add the local directory as a marketplace source
instead of the remote. Works identically and is not rate-limited.

## Verify, then report restarts honestly

An installer's exit code is not evidence. After installing, confirm on disk for **every**
runtime: the directory exists, `SKILL.md` parses, frontmatter carries `name` and
`description`. Then re-run the audit protocol against what you touched.

Restart requirements differ by surface, and saying "restart" without saying which surface is
how a user ends up thinking the work failed:

- Some runtimes hot-load new skills into a live session; the model can use them immediately.
- The **slash menu is built at session start** and does not rebuild on install. Newly added
  commands are invisible until restart even when the skill is fully loaded and working.
- Runtimes that scan their skills directory only at startup see nothing until restarted.

Report which of these applies to each runtime you touched, and what the user will observe
before and after restarting.

## Risk

Community skills execute with full agent permissions, and published scans have found
malicious payloads across a meaningful share of them. Where the installer reports a risk
rating, carry it into the report and name every flagged item explicitly. A flagged skill the
user chose to install is fine; a flagged skill buried inside a success summary is not.
