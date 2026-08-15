# Audit protocol

Runtime-agnostic. Discovers the surface instead of branching on platform identity, so a
runtime nobody anticipated still produces a complete report.

Paste as-is into a fresh session, or follow it directly.

---

SKILL REGISTRATION AUDIT — do not trust prior context, memory, or any earlier claim in this
session. Every conclusion must come from a command you run now or from your own live
capability registry. If you cannot verify something, write UNVERIFIED. Never infer, never
estimate.

## 0. Discover the surface

Do not assume which platform you are on. Probe these candidate roots and report which exist,
with absolute resolved paths:

- skill roots: `~/.claude/skills` `~/.codex/skills` `~/.agents/skills` `~/.cursor/skills`
  `./.claude/skills` `./.agents/skills`
- command roots: `~/.claude/commands` `~/.codex/prompts`, and any `commands/` directory
  inside an installed plugin

Add any other skill or command root this runtime is known to read. Every later section
operates only on roots that resolved. If a root is absent, say so once and move on.

## 1. Ground truth on disk

For each discovered skill root, count **directories containing a `SKILL.md`** — not raw
listing output, which counts unrelated entries. Show the command and its real output.

Validate every skill directory: `SKILL.md` exists, opens as UTF-8, has YAML frontmatter
delimited by `---`, and carries a non-empty `name:` and `description:`. Report per root:
total / valid / invalid. Name every invalid one with its exact failure. Separately flag any
entry that is a symlink whose target does not resolve.

## 2. Your live registry

Without running a command, report how many skills you can invoke right now from your own
registry as loaded at session start. Do not enumerate them all if the count is large.

Diff your registry against section 1:

- **A. on disk AND in registry** → LOADED
- **B. on disk but NOT in registry** → FAILED TO LOAD ← the real defect
- **C. in registry but NOT on disk** → supplied by a plugin or bundled elsewhere

Give counts for A / B / C and name every member of B in full. If B is non-empty, open one and
diagnose why: malformed frontmatter, duplicate name, unreadable path, unresolved symlink, or
nesting deeper than the runtime scans.

If your registry is too large to diff exactly, diff a random 40-skill sample and state
clearly that it was sampled.

> Models are unreliable at exact recall over long lists. Named misses in set B are the
> signal; raw counts are approximate. Sections 0, 1, 3 and 4 are command-grounded and exact.

## 3. Slash surface — registered ≠ typeable

Registration and menu visibility are different. Do not merge them.

**(a)** From the command roots in section 0, list every command that resolves to a `/name`
entry, and the total. Where a plugin registry exists (an `enabledPlugins` map or equivalent),
cross-check it — a plugin present on disk but absent or disabled there is
INSTALLED-BUT-INACTIVE; list those separately. If this runtime has no command layer, state
that in one line and skip to (b).

**(b)** Count skills that load correctly but ship no command entry. These are invocable by
name or description and will not appear in any menu.

State plainly which skills are typeable as `/name` and which must be invoked by description.

## 4. Live invocation test

Choose 3 skills at random from set A, favoring the most recently installed. Exclude any whose
description implies persistent side effects — output-style changes, memory or config writes,
network posts, destructive file ops — and name what you excluded and why. Invoke the 3 for
real. Report each as invoked / failed plus the first line returned. A skill that lists but
will not invoke is a FAIL.

## Output

One table, one row per discovered root:

| Root | Skills on disk | Valid | Loaded | Typeable as /name |

Then VERDICT — PASS only if invalid = 0, B = 0, and all 3 invocations succeeded. Otherwise
FAIL, naming the specific gap and the exact command that fixes it. Nothing beyond that.
