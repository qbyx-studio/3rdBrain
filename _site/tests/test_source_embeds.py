"""Source links must be embed blocks, whatever the section is called.

Content check, reported but never blocking, like the link audit.

Why this exists. The embed convention used to live only inside the page
templates, attached to the literal headings "Get it" and "Source video". A base
in a different domain renames those headings, quite correctly, and the block gets
dropped along with the label. One real base lost players on 17 pages that way:
every video deep-mined with timestamps, every source rendered as flat text. The
prompt and callout blocks survived in the same base, because those attach to a
content type rather than to a heading.

So the check keys on the link's role, not the wording above it. Any heading that
names a source in any phrasing counts.

Inline references are deliberately left alone. Timestamped links inside a method
list are correct as plain links; eleven players in a step list is unreadable.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / ".build"

VIDEO_HOST = re.compile(
    r"https?://[^)\s]*(?:youtube\.com|youtu\.be|vimeo\.com|tiktok\.com|bilibili\.com)",
    re.I,
)

# A heading that names a source, in whatever wording a base settled on.
SOURCE_HEADING = re.compile(
    r"^(?:#{1,6}\s+|\*\*)\s*"
    r"(?:sources?|get it|watch|videos?|origin|references?|credits?|from)\b",
    re.I | re.M,
)

# The next heading of any kind ends the section.
NEXT_HEADING = re.compile(r"^(?:#{1,6}\s+|\*\*[A-Z])", re.M)

MARKDOWN_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")


def content_pages() -> list[Path]:
    if not BUILD.exists():
        return []
    skip = {"SUMMARY.md", "NAV.md", "NAV-EXTRA.md"}
    return [
        p
        for p in BUILD.rglob("*.md")
        if p.name not in skip and "facets" not in p.relative_to(BUILD).parts
    ]


def offending_pages() -> list[tuple[str, str]]:
    """Pages whose source section links a video without an embed block."""
    found = []
    for path in content_pages():
        text = path.read_text(encoding="utf-8", errors="replace")
        for head in SOURCE_HEADING.finditer(text):
            rest = text[head.end() :]
            end = NEXT_HEADING.search(rest)
            section = rest[: end.start()] if end else rest[:600]

            if "{% embed" in section:
                continue  # already an embed, nothing to fix

            for url in MARKDOWN_LINK.findall(section):
                if VIDEO_HOST.match(url.strip()):
                    found.append((path.relative_to(BUILD).as_posix(), url.strip()))
                    break
            else:
                continue
            break
    return found


@pytest.mark.content
def test_source_links_are_embed_blocks():
    if not BUILD.exists():
        pytest.skip("no staged build to inspect")

    offenders = offending_pages()
    detail = "\n".join(f"    {page}  ->  {url}" for page, url in offenders[:10])
    assert not offenders, (
        f"{len(offenders)} page(s) put a video source in a plain markdown link, so it "
        f"renders as text with no player. Wrap it on its own line as "
        f'{{% embed url="..." %}} . The section heading can be called anything; the '
        f"block is what makes it a player.\n{detail}"
    )
