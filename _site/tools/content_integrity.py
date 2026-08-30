"""Reusable content checks shared by fast curation and the full build."""

from __future__ import annotations

import re
import sys
from pathlib import Path


HOOKS = Path(__file__).resolve().parents[1] / "hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))
import embed_hosts  # noqa: E402


SOURCE_HEADING = re.compile(
    r"^(?:#{1,6}\s+|\*\*)\s*"
    r"(?:sources?|get it|watch|videos?|origin|references?|credits?|from)\b",
    re.I | re.M,
)
NEXT_HEADING = re.compile(r"^(?:#{1,6}\s+|\*\*[A-Z])", re.M)
MARKDOWN_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")


def video_source_offenders(root: Path, pages: set[str] | None = None) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        if pages is not None and relative not in pages:
            continue
        if path.name in {"SUMMARY.md", "NAV.md", "NAV-EXTRA.md"} or "facets" in path.relative_to(root).parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for head in SOURCE_HEADING.finditer(text):
            rest = text[head.end():]
            end = NEXT_HEADING.search(rest)
            section = rest[:end.start()] if end else rest[:600]
            if "{% embed" in section:
                continue
            for url in MARKDOWN_LINK.findall(section):
                if embed_hosts.looks_like_video(url):
                    found.append((relative, url.strip()))
                    break
            else:
                continue
            break
    return found
