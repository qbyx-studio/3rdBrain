---
name: promptos-skillsync
description: >
  Reconcile the skills catalogued in a PromptOS knowledge base against the skills actually
  installed on this machine — across every agent runtime present — then install, repair and
  verify whatever is missing or broken. Runtime-agnostic: it discovers which agent platforms
  exist rather than assuming any of them, so it works on Claude Code, Codex, Cursor, Windsurf,
  Copilot CLI and anything else that reads a skills directory. Use this skill whenever the user
  wants to audit installed skills, asks "are my skills actually installed / registered / loaded",
  reports that a skill or slash command does not appear, wants every skill in their knowledge
  base installed on a new or existing machine, wants two agent platforms brought to parity,
  or wants to verify a skill install actually worked rather than trusting an installer's output.
---

# PromptOS SkillSync; Catalogue → Installed, Verified, On Every Runtime

The PromptOS knowledge base records which skills are worth having. This skill makes the
machine match the record — on every agent runtime installed, not just the one you are
running inside — and then proves it.

Two failure modes drive the whole design:

1. **Installers lie.** They report success for work they did not do. A cross-agent installer
   can print `copy → Codex ✓` and write nothing. Never treat installer output as evidence.
2. **Installed ≠ loaded ≠ typeable.** A skill can be valid on disk, absent from the running
   agent's registry, and absent again from the slash menu. These are three separate states
   and each needs its own check. Conflating them is how a "316 skills installed" report ends
   with an empty slash menu.

So: every claim is grounded in a command run now, or in your own live registry. Nothing is
inferred from an install log.

Before any audit or repair, follow `../promptos-curator/references/framework-freshness.md` once.

## Run order

**Phase 0 — Discover.** Never assume a platform. Probe for skill roots and command roots and
carry forward only the ones that resolve. Absence is data, not an error.

**Phase 1 — Audit.** Validate what is on disk, diff it against your live registry, map the
slash surface, and invoke a live sample. Full protocol: `references/audit-protocol.md`.

**Phase 2 — Reconcile.** Read the knowledge base's skill inventory and diff it against what
Phase 1 found installed. Produce four sets:

| Set | Meaning | Action |
| --- | --- | --- |
| INSTALLED | catalogued and present and loading | none |
| MISSING | catalogued, not installed | install in Phase 3 |
| BROKEN | installed but invalid, unloaded, or uninvocable | repair in Phase 3 |
| NOT-A-SKILL | catalogued but not installable as a skill | record with the reason |

That last set is mandatory, not a rounding error. Knowledge bases catalogue CLIs, MCP servers,
libraries and gated downloads alongside real skills. A CLI is not a skill and must never be
reported as installed. Name each one and say what it actually is.

**Phase 3 — Install and repair.** Route each item by what its source actually contains, not by
what the catalogue page calls it. Full routing table, per-runtime mechanics and the known
installer traps: `references/install-playbook.md`.

**Phase 4 — Re-verify.** Re-run Phase 1 against the items just touched. An install is not done
because an installer exited zero; it is done when the skill validates on disk, appears in a
registry, and invokes. Report anything that needs a restart to become visible, and say which
surface the restart affects.

## Rules

- **Parity is explicit.** When more than one runtime exists, every skill lands on every one, or
  the report names the runtime it is missing from and why. Silent single-platform installs are
  the most common failure this skill exists to catch.
- **Count skills, not directory entries.** Count directories containing a `SKILL.md`. A raw
  listing counts internal folders and inflates every number downstream.
- **Third-party code is third-party code.** Installing a skill means running someone else's
  instructions with your agent's permissions. Surface any risk rating the installer reports,
  name anything flagged, and never bury it in a success summary.
- **Report gaps in full.** A partial install reported as complete is worse than a failed one,
  because it stops the user from looking. If something could not be installed, say so, say why,
  and give the exact command or manual step that would fix it.

## Output

A table with one row per discovered runtime — skills on disk, valid, loaded, typeable as
`/name` — then the four reconciliation sets with counts, then a verdict. PASS requires zero
invalid, zero failed-to-load, every MISSING item resolved or explained, and a passing live
invocation sample. Anything else is FAIL with the specific gap and the exact fix.
