---
description: Audit every agent runtime on this machine against the skills catalogued in your PromptOS base, then install, repair and verify whatever is missing or broken. Runtime-agnostic.
---

# /promptos:skills — reconcile catalogue → machine

Load the `promptos-skillsync` skill (`skills/promptos-skillsync/SKILL.md`) and run its four
phases. It holds the routing table, the per-runtime mechanics and the installer traps.

Default scope is the whole catalogue against every agent runtime found on this machine. If
the user named a subset — one skill, one category, one runtime — honor exactly that scope and
say in the report what you did not touch.

## Non-negotiables

**Discover, never assume.** Probe for runtimes. Do not branch on platform identity; a runtime
you did not anticipate must still produce a complete row in the report.

**Installed, loaded and typeable are three states.** Check each separately. A skill valid on
disk can be absent from the running registry, and a skill in the registry can still be absent
from the slash menu. Never report one as evidence of another.

**Never trust an installer's output.** Confirm on disk, per runtime, after every install.
Installers report success for work they did not do.

**Parity or an explanation.** Where multiple runtimes exist, every skill lands on all of
them, or the report names the runtime it is missing from and why.

**NOT-A-SKILL is a real result.** Catalogues list CLIs, MCP servers, libraries and manual
downloads next to real skills. Name each one and say what it actually is. Never report a CLI
as an installed skill.

## Report

The table from the skill's Output section, the four reconciliation sets with counts, then a
verdict. Surface any risk ratings the installer returned, naming flagged items explicitly.
Close with what needs a restart, which surface each restart affects, and what the user will
see before and after.

If anything could not be installed, give the exact command or manual step that would fix it.
A partial run reported as complete is worse than a failed one — it stops the user looking.
