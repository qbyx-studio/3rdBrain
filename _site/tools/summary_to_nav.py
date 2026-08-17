"""Convert a GitBook SUMMARY.md into a literate-nav navigation file.

GitBook expresses sidebar sections as `## Headings` between top-level lists.
mkdocs-literate-nav only reads a single Markdown list and silently ignores
headings, which drops the entire navigation. The fix is mechanical: each
`## Heading` becomes a parent list item and the bullets under it become its
children, which is how MkDocs models sections anyway.

    ## General                  ->    * General
                                        * [PXPipe](general/pxpipe.md)
    * [PXPipe](general/pxpipe.md)

SUMMARY.md is left untouched so it stays valid for GitBook while both systems
run in parallel.

    python tools/summary_to_nav.py docs/SUMMARY.md docs/NAV.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")
TITLE_RE = re.compile(r"^#\s+")
BULLET_RE = re.compile(r"^(?P<indent>\s*)\*\s+(?P<rest>.*)$")

# GitBook writes 2-space indents; literate-nav's Markdown parser only treats a
# nested list as nested at 4 spaces. Depth is renormalized rather than copied.
GITBOOK_INDENT = 2
NAV_INDENT = "    "


def convert(text: str) -> tuple[str, int, int]:
    out: list[str] = []
    sections = pages = 0
    in_section = False

    for line in text.splitlines():
        if not line.strip():
            continue

        # Drop the document title ("# Table of contents").
        if TITLE_RE.match(line) and not line.startswith("##"):
            continue

        heading = HEADING_RE.match(line)
        if heading:
            out.append(f"* {heading.group('title')}")
            in_section = True
            sections += 1
            continue

        bullet = BULLET_RE.match(line)
        if bullet:
            pages += 1
            # Everything under a heading shifts one level deeper so it nests
            # beneath the synthesized section item.
            depth = len(bullet.group("indent")) // GITBOOK_INDENT
            if in_section:
                depth += 1
            out.append(f"{NAV_INDENT * depth}* {bullet.group('rest')}")
            continue

        # Anything else (stray prose) is not navigation; skip it.

    return "\n".join(out) + "\n", sections, pages


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    nav, sections, pages = convert(src.read_text(encoding="utf-8"))

    # Pages the site adds that GitBook's SUMMARY.md does not know about are
    # appended here, so they land at the end of the sidebar without the vault
    # ever being edited.
    extra = src.parent / "NAV-EXTRA.md"
    if extra.exists():
        tail = extra.read_text(encoding="utf-8").lstrip("\n")
        nav = nav.rstrip("\n") + "\n" + tail
        print(f"  + appended {extra.name}")

    dst.write_text(nav, encoding="utf-8")
    print(f"  {src.name} -> {dst.name}: {sections} sections, {pages} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

