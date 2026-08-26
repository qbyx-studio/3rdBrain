"""Migrate 3rdBrain 2 facet footers into frontmatter tags.

The vault already encodes its taxonomy on every page as a footer line:

    **Facets:** [Skill](../facets/skill.md) · [Free](../facets/free.md) · ...

That is exactly the data Material's tags plugin needs, so no page has to be
re-tagged by hand. This script lifts each footer into grouped frontmatter tags
and drops the footer, since the tags render at the top of the page instead:

    ---
    tags:
      - Capability/Skill
      - Access/Free
      - Platform/Claude
    ---

Run against a copy, never the live vault:
    python tools/facets_to_tags.py docs
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Group names mirror the three tables in facets/README.md. "Type" splits out
# the two page-type facets that the capability table carries but that are not
# capabilities.
GROUPS: dict[str, str] = {}
for _group, _names in {
    "Capability": (
        "Workflow Agent Skill Prompt MCP Automation Model Website Design Image "
        "Video Voice 3D Game Simulation Data Research Browser Writing SEO Leads "
        "Finance"
    ),
    "Type": "Roundup Bespoke",
    "Access": "Free Freemium Paid PasteReady APISpend SelfHosted OpenSource",
    "Platform": "Claude ChatGPT Gemini CrossPlatform",
}.items():
    for _name in _names.split():
        GROUPS[_name.lower()] = f"{_group}/{_name}"

FACETS_RE = re.compile(r"^\*\*Facets:\*\*(?P<body>.*)$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def tags_for(markdown: str) -> tuple[list[str], str]:
    """Return (grouped tags, markdown with the footer removed)."""
    m = FACETS_RE.search(markdown)
    if not m:
        return [], markdown

    tags, unknown = [], []
    for label in LINK_RE.findall(m.group("body")):
        key = label.strip().lower()
        if key in GROUPS:
            tags.append(GROUPS[key])
        else:
            unknown.append(label)
    if unknown:
        print(f"    ! unmapped facets: {', '.join(unknown)}")

    return tags, FACETS_RE.sub("", markdown, count=1).rstrip() + "\n"


def apply(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    tags, body = tags_for(text)
    if not tags:
        return False

    block = "tags:\n" + "".join(f"  - {t}\n" for t in tags)

    if body.startswith("---\n"):
        end = body.index("\n---", 4) + 1
        body = body[:end] + block + body[end:]
    else:
        body = f"---\n{block}---\n\n{body}"

    path.write_text(body, encoding="utf-8")
    print(f"    {len(tags)} tags -> {path.name}")
    return True


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "docs")
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 1

    tagged = 0
    for md in sorted(root.rglob("*.md")):
        if apply(md):
            tagged += 1
    total = len(list(root.rglob("*.md")))
    print(f"\n  tagged {tagged}/{total} pages ({total - tagged} index/hub pages have no facets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
