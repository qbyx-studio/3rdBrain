"""Source links must be embed blocks, and their host must have an embed rule.

Content checks, reported but never blocking, like the link audit.

Two failures live here, both of which shipped silently.

First, the embed convention used to be shown only under the literal headings
"Get it" and "Source video". A base in another domain renames those, quite
correctly, and the block gets dropped with the label. One base lost players on 17
pages that way. So the check keys on the link's role, not the wording above it.

Second, the renderer only knew YouTube. Every other platform took the fallback
and became a tidy link card that looked deliberate, so an Instagram source sat
wrong for weeks. Host knowledge is now a table, and this warns when a video
source points at a host with no row in it.

Inline references are deliberately left alone. Timestamped links inside a method
list are correct as plain links; eleven players in a step list is unreadable.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / ".build"

sys.path.insert(0, str(ROOT / "hooks"))
import embed_hosts  # noqa: E402

# A heading that names a source, in whatever wording a base settled on.
SOURCE_HEADING = re.compile(
    r"^(?:#{1,6}\s+|\*\*)\s*"
    r"(?:sources?|get it|watch|videos?|origin|references?|credits?|from)\b",
    re.I | re.M,
)

# The next heading of any kind ends the section.
NEXT_HEADING = re.compile(r"^(?:#{1,6}\s+|\*\*[A-Z])", re.M)

MARKDOWN_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")

EMBED_URL = re.compile(r'\{%\s*embed\s+url="([^"]+)"\s*%\}')


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
                if embed_hosts.looks_like_video(url):
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


@pytest.mark.content
def test_every_embedded_host_has_a_rule():
    """A video source with no row in the host table renders as a link card.

    The table cannot know about a platform that launches next year, so the gap
    has to announce itself. This is what turns "Instagram silently became a link
    card" into "add one row to EMBED_HOSTS".
    """
    if not BUILD.exists():
        pytest.skip("no staged build to inspect")

    unknown: dict[str, list[str]] = {}
    for path in content_pages():
        text = path.read_text(encoding="utf-8", errors="replace")
        for url in EMBED_URL.findall(text):
            if embed_hosts.looks_like_video(url) and not embed_hosts.is_embeddable(url):
                host = re.sub(r"^https?://(?:www\.)?([^/]+).*", r"\1", url.strip())
                unknown.setdefault(host, []).append(path.relative_to(BUILD).as_posix())

    detail = "\n".join(
        f"    {host}  ({len(pages)} page(s), e.g. {pages[0]})"
        for host, pages in sorted(unknown.items())
    )
    assert not unknown, (
        f"{len(unknown)} video host(s) have no embed rule, so their sources render as "
        f"link cards instead of players. Add a row to _site/hooks/embed_hosts.py:\n"
        f"{detail}"
    )
