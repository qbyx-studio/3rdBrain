"""Tune search relevance without touching the vault.

Runs against the staging copy, so all of this is derived at build time.

Two problems in a 317-page corpus:

1. Hub pages lose to the pages they link to. Searching "token savings" should
   surface the Tool Index near the top, not on page two.
2. The 30 hand-maintained facets/*.md hubs are pure link tables that repeat
   every page title in the vault. They match almost any query and bury the real
   page. They are also now redundant with the generated tag listings, so they
   are dropped from the index (they stay in the nav and stay browsable).

    python tools/search_tuning.py .build
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Page -> search boost. Higher wins ties against ordinary pages.
BOOST = {
    "tool-index.md": 4.0,   # the intended front door
    "README.md": 2.0,
    "facets.md": 2.0,
    "facets-capability.md": 1.5,
    "facets-access.md": 1.5,
    "facets-platform.md": 1.5,
}

# Directory whose pages are excluded from the index entirely.
EXCLUDE_DIR = "facets"

FM_RE = re.compile(r"^---\r?\n(?P<body>[\s\S]*?)\r?\n---\r?\n")


def patch(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if m:
        text = text[: m.end() - 4] + block + text[m.end() - 4 :]
    else:
        text = f"---\n{block}---\n\n{text}"
    path.write_text(text, encoding="utf-8")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".build")
    boosted = excluded = 0

    for name, weight in BOOST.items():
        p = root / name
        if p.exists():
            patch(p, f"search:\n  boost: {weight}\n")
            boosted += 1

    facets = root / EXCLUDE_DIR
    if facets.is_dir():
        for p in sorted(facets.rglob("*.md")):
            patch(p, "search:\n  exclude: true\n")
            excluded += 1

    print(f"  search: boosted {boosted} hub pages, excluded {excluded} facet hubs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
