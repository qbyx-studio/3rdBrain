"""GitBook -> MkDocs compatibility layer.

Converts GitBook's proprietary block syntax to Material equivalents at build
time. Source markdown on disk is never modified, so the same files stay
editable in Obsidian and byte-identical to the promptos-2 repo.

Handled (counts measured across the full 319-page vault):
  {% embed %} block-level        297x  -> responsive YouTube iframe, or link card
  {% embed %} inline              35x  -> inline link (a <div> would break the line)
  {% prompt %}...{% endprompt %} 222x  -> collapsible admonition + copy button
  {% hint style="info|warning" %} 26x  -> Material admonition
  {% file src="..." %}             1x  -> download card
  .gitbook/assets/...            153   -> /gitbook-assets/... (copied post-build)

These five are the complete set; the vault uses no other GitBook constructs.
"""

from __future__ import annotations

import posixpath
import re
import shutil
from pathlib import Path
from urllib.parse import quote

from mkdocs.utils import get_relative_url

# --------------------------------------------------------------------------
# assets
# --------------------------------------------------------------------------

# MkDocs ignores dot-directories, so GitBook's .gitbook/assets tree is copied
# to a non-dot path after the build and references are rewritten to absolute
# URLs. Absolute means the depth of the page no longer matters.
ASSET_SRC = ".gitbook/assets"
ASSET_DST = "gitbook-assets"

# Three asset filenames contain spaces and parentheses ("_ARTICLE-TEMPLATE (1).docx",
# "image (1).png"). When the path sits inside quotes the closing quote is the only
# reliable terminator, so quoted references are rewritten first and the looser
# bare-path pattern only sees what is left.
_ASSET_QUOTED_RE = re.compile(r"(?<=\")((?:\.\./)*\.gitbook/assets/[^\"]+)(?=\")")
_ASSET_RE = re.compile(r"(?:\.\./)*\.gitbook/assets/([^\"')\s]+(?:\s[^\"')]+)*)")


def _asset_url(path: str) -> str:
    return f"/{ASSET_DST}/{quote(path.strip())}"


def _strip_prefix(path: str) -> str:
    return re.sub(r"^(?:\.\./)*\.gitbook/assets/", "", path.strip())


def _rewrite_assets(markdown: str) -> str:
    markdown = _ASSET_QUOTED_RE.sub(lambda m: _asset_url(_strip_prefix(m.group(1))), markdown)
    return _ASSET_RE.sub(lambda m: _asset_url(m.group(1)), markdown)


# --------------------------------------------------------------------------
# {% embed %}
# --------------------------------------------------------------------------

# Block-level: the embed sits alone on its line and becomes a player or card.
_EMBED_RE = re.compile(r"^\{%\s*embed\s+url=\"([^\"]+)\"\s*%\}\s*$", re.MULTILINE)

# Inline: 35 embeds in the vault sit mid-sentence ("**Get it:** {% embed %}"),
# several to a line, or inside list items. A block-level <div> there would
# break the surrounding paragraph, so these degrade to a plain link.
_EMBED_INLINE_RE = re.compile(r"\{%\s*embed\s+url=\"([^\"]+)\"\s*%\}")

_YT_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([A-Za-z0-9_-]{6,})"
)
_YT_T_RE = re.compile(r"[?&]t=(\d+)")


def _embed(m: re.Match[str]) -> str:
    url = m.group(1)
    yt = _YT_RE.search(url)
    if yt:
        src = f"https://www.youtube-nocookie.com/embed/{yt.group(1)}"
        t = _YT_T_RE.search(url)
        if t:
            src += f"?start={t.group(1)}"
        return (
            '<div class="gb-video">'
            f'<iframe src="{src}" loading="lazy" allowfullscreen '
            'allow="accelerometer; encrypted-media; picture-in-picture"></iframe>'
            "</div>"
            # Fallback: an embed can still fail (region blocks, owner settings,
            # or a localhost origin during preview), and a dead grey box with no
            # way out is worse than a link.
            f'<p class="gb-video-link" markdown="1">:material-youtube: '
            f'[Watch on YouTube]({url})</p>'
        )

    label = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    icon = ":material-github:" if "github.com" in url else ":material-link-variant:"
    return f'<div class="gb-card" markdown="1">{icon} [{label}]({url})</div>'


def _embed_inline(m: re.Match[str]) -> str:
    url = m.group(1)
    label = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    icon = ":material-play-circle:" if _YT_RE.search(url) else ":material-link-variant:"
    return f"{icon} [{label}]({url})"


# --------------------------------------------------------------------------
# {% prompt %} / {% hint %} / {% file %}
# --------------------------------------------------------------------------

_PROMPT_RE = re.compile(
    r"^\{%\s*prompt(?P<attrs>[^%]*)%\}\n(?P<body>.*?)\n\{%\s*endprompt\s*%\}",
    re.DOTALL | re.MULTILINE,
)

_HINT_RE = re.compile(
    r"^\{%\s*hint\s+style=\"(?P<style>\w+)\"\s*%\}\n(?P<body>.*?)\n\{%\s*endhint\s*%\}",
    re.DOTALL | re.MULTILINE,
)

_FILE_RE = re.compile(r"^\{%\s*file\s+src=\"([^\"]+)\"\s*%\}\s*$", re.MULTILINE)

_DESC_RE = re.compile(r'description="([^"]*)"')

# GitBook hint styles -> Material admonition types
_HINT_MAP = {
    "info": "info",
    "success": "success",
    "warning": "warning",
    "danger": "danger",
}


def _indent(body: str, spaces: int = 4) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else "" for line in body.split("\n"))


def _prompt(m: re.Match[str]) -> str:
    desc = _DESC_RE.search(m.group("attrs") or "")
    title = desc.group(1).replace('"', "'") if desc else "Prompt"
    # '???+' renders collapsible-but-open: the prompt stays visible, and long
    # ones can be folded away. Fenced code inside keeps Material's copy button.
    return f'???+ note "📝 {title}"\n\n{_indent(m.group("body"))}\n'


def _hint(m: re.Match[str]) -> str:
    kind = _HINT_MAP.get(m.group("style").lower(), "note")
    return f"!!! {kind}\n\n{_indent(m.group('body'))}\n"


def _file(m: re.Match[str]) -> str:
    src = m.group(1)
    name = Path(src.replace("\\", "/")).name
    href = _asset_url(_strip_prefix(src)) if ".gitbook/assets" in src else src
    return f'<div class="gb-card" markdown="1">:material-download: [{name}]({href})</div>'


# --------------------------------------------------------------------------
# fence awareness
# --------------------------------------------------------------------------

# Some pages document GitBook syntax by showing it inside a code fence -- the
# curator's page template is written that way. Converting those examples would
# corrupt the documentation, so every substitution below skips matches that
# begin inside a fenced block.

_FENCE_OPEN = re.compile(r"^(?P<marker>`{3,}|~{3,})")


def _fence_spans(text: str) -> list[tuple[int, int]]:
    """Character ranges covered by fenced code blocks.

    A fence closes only on a run of the same character at least as long as the
    one that opened it, so the inner ```markdown blocks of a four-backtick
    example count as content rather than as separate fences.
    """
    spans: list[tuple[int, int]] = []
    marker: str | None = None
    start = 0
    pos = 0
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        m = _FENCE_OPEN.match(stripped)
        if marker is None:
            if m:
                marker = m.group("marker")
                start = pos
        elif m and m.group("marker")[0] == marker[0] and len(m.group("marker")) >= len(marker):
            spans.append((start, pos + len(line)))
            marker = None
        pos += len(line)
    if marker is not None:
        spans.append((start, len(text)))
    return spans


def _sub_outside_fences(pattern: re.Pattern[str], repl, text: str) -> str:
    spans = _fence_spans(text)
    if not spans:
        return pattern.sub(repl, text)

    def guarded(m: re.Match[str]) -> str:
        if any(lo <= m.start() < hi for lo, hi in spans):
            return m.group(0)
        return repl(m)

    return pattern.sub(guarded, text)


# --------------------------------------------------------------------------
# raw HTML links to pages
# --------------------------------------------------------------------------

# MkDocs rewrites Markdown links to .md pages, but never links written as raw
# HTML. GitBook renders both, so pages authored there can contain
# <a href="other-page.md">, which would 404 here. Rewriting the content would
# fix this site and leave GitBook fine either way, so the renderer resolves them
# instead - the same choice made for heading anchors.
_HTML_MD_HREF = re.compile(r'(<a\s[^>]*href=")([^":#?]+\.md)((?:[#?][^"]*)?")', re.I)


def _rewrite_html_page_links(markdown: str, page, files) -> str:
    if page is None or files is None:
        return markdown

    here = posixpath.dirname(page.file.src_uri)

    def repl(m: re.Match[str]) -> str:
        target = posixpath.normpath(posixpath.join(here, m.group(2)))
        found = files.get_file_from_path(target)
        if found is None:
            return m.group(0)          # leave it alone; the link audit reports it
        return m.group(1) + get_relative_url(found.url, page.url) + m.group(3)

    return _HTML_MD_HREF.sub(repl, markdown)


# --------------------------------------------------------------------------
# MkDocs hooks
# --------------------------------------------------------------------------


def on_page_markdown(markdown: str, page, config, files) -> str:
    # Order matters: prompt blocks wrap fenced code, so they are converted
    # before the fence-aware guard would treat that inner fence as an example.
    for pattern, repl in (
        (_PROMPT_RE, _prompt),
        (_HINT_RE, _hint),
        (_FILE_RE, _file),
        (_EMBED_RE, _embed),
        # Anything left is mid-line and must stay inline.
        (_EMBED_INLINE_RE, _embed_inline),
    ):
        markdown = _sub_outside_fences(pattern, repl, markdown)
    markdown = _rewrite_html_page_links(markdown, page, files)
    return _rewrite_assets(markdown)


def on_post_build(config) -> None:
    src = Path(config["docs_dir"]) / ASSET_SRC
    if not src.is_dir():
        return
    dst = Path(config["site_dir"]) / ASSET_DST
    shutil.copytree(src, dst, dirs_exist_ok=True)
