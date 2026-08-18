# -*- coding: utf-8 -*-
"""Which links become players, and in what shape.

Host knowledge lives here as DATA, so adding a platform is one row rather than a
code change. The renderer walks the table, first match wins, and anything with no
row degrades to a link card.

This replaced a hardcoded YouTube branch. The base it was written against was
almost all YouTube, so every other platform silently took the fallback and
rendered as a tidy link card that looked deliberate. An Instagram recipe source
sat there for weeks looking correct.

A table still cannot know about a platform that launches next year, so the
content checks warn when a source link points at a host with no row here. The
gap announces itself instead of hiding.

Each row: (pattern, embed URL template, aspect ratio, display name)
  pattern   captures the id the embed URL needs
  template  {0} is the captured id
  aspect    portrait platforms are 9/16; a shared 16/9 box letterboxes them
  name      used in the fallback link under the player
"""

from __future__ import annotations

import re

EMBED_HOSTS: list[tuple[str, str, str, str]] = [
    (
        r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/|live/)|youtu\.be/)([A-Za-z0-9_-]{6,})",
        "https://www.youtube-nocookie.com/embed/{0}",
        "16/9",
        "YouTube",
    ),
    (
        r"instagram\.com/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)",
        "https://www.instagram.com/p/{0}/embed",
        "9/16",
        "Instagram",
    ),
    (
        r"tiktok\.com/(?:@[\w.-]+/video/|v/)(\d+)",
        "https://www.tiktok.com/embed/v2/{0}",
        "9/16",
        "TikTok",
    ),
    (
        r"vimeo\.com/(?:video/)?(\d+)",
        "https://player.vimeo.com/video/{0}",
        "16/9",
        "Vimeo",
    ),
    (
        r"loom\.com/share/([A-Za-z0-9]+)",
        "https://www.loom.com/embed/{0}",
        "16/9",
        "Loom",
    ),
    (
        r"(?:bilibili\.com/video/|b23\.tv/)([A-Za-z0-9]+)",
        "https://player.bilibili.com/player.html?bvid={0}",
        "16/9",
        "Bilibili",
    ),
]

_COMPILED = [(re.compile(p, re.I), tpl, ratio, name) for p, tpl, ratio, name in EMBED_HOSTS]

# Hosts that carry video but have no row above. Used by the content checks to say
# "add a row" rather than letting the link quietly become a card.
VIDEO_HOSTS = re.compile(
    r"https?://[^/\s)]*(?:"
    r"youtube\.com|youtu\.be|instagram\.com|tiktok\.com|vimeo\.com|loom\.com|"
    r"bilibili\.com|b23\.tv|facebook\.com/watch|fb\.watch|twitch\.tv|dailymotion\.com|"
    r"streamable\.com|wistia\.com|rumble\.com"
    r")",
    re.I,
)

# YouTube is the only host whose deep links carry a start time worth preserving.
_START_AT = re.compile(r"[?&](?:t|start)=(\d+)")


def resolve(url: str):
    """Return (src, aspect, name) for an embeddable URL, else None."""
    for pattern, template, ratio, name in _COMPILED:
        m = pattern.search(url)
        if not m:
            continue
        src = template.format(m.group(1))
        start = _START_AT.search(url)
        if start and name == "YouTube":
            src += ("&" if "?" in src else "?") + "start=" + start.group(1)
        return src, ratio, name
    return None


def is_embeddable(url: str) -> bool:
    return resolve(url) is not None


def looks_like_video(url: str) -> bool:
    return bool(VIDEO_HOSTS.match(url.strip()))
