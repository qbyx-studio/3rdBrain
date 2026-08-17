"""Audit every link in the built site.

Internal links must resolve to a real file. External links are counted and
grouped, not fetched. Anchors are checked against the target page's ids.

    python tools/check_links.py site
"""

from __future__ import annotations

import collections
import re
import sys
import urllib.parse
from pathlib import Path

HREF_RE = re.compile(r'<a\s[^>]*href="([^"]+)"', re.I)
SRC_RE = re.compile(r'<(?:img|iframe)\s[^>]*src="([^"]+)"', re.I)
ID_RE = re.compile(r'\sid="([^"]+)"')


def target_for(site: Path, page: Path, url: str) -> Path | None:
    """Map a URL to the file that should serve it."""
    path = urllib.parse.urlparse(url).path
    if not path:
        return None
    rel = urllib.parse.unquote(path)
    base = site if rel.startswith("/") else page.parent
    p = (base / rel.lstrip("/")).resolve()
    if p.is_dir():
        p = p / "index.html"
    elif p.suffix == "":
        p = p.with_suffix(".html")
    return p


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    pages = list(site.rglob("*.html"))

    internal = external = mailto = 0
    broken: list[tuple[str, str]] = []
    bad_anchor: list[tuple[str, str]] = []
    hosts: collections.Counter[str] = collections.Counter()
    ids_cache: dict[Path, set[str]] = {}

    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        for url in HREF_RE.findall(text) + SRC_RE.findall(text):
            if url.startswith(("http://", "https://", "//")):
                external += 1
                hosts[urllib.parse.urlparse(url).netloc.lower()] += 1
                continue
            if url.startswith(("mailto:", "tel:", "data:", "javascript:")):
                mailto += 1
                continue
            if url.startswith("#"):
                ids = ids_cache.setdefault(page, set(ID_RE.findall(text)))
                if urllib.parse.unquote(url[1:]) not in ids:
                    bad_anchor.append((page.relative_to(site).as_posix(), url))
                continue

            internal += 1
            tgt = target_for(site, page, url)
            if tgt is None or not tgt.exists():
                broken.append((page.relative_to(site).as_posix(), url))

    print(f"pages scanned      : {len(pages)}")
    print(f"internal links     : {internal}")
    print(f"external links     : {external}")
    print(f"mailto/tel/data    : {mailto}")
    print(f"\nBROKEN internal    : {len(broken)}")
    for src, url in broken[:25]:
        print(f"   {src}  ->  {url}")
    print(f"\nBROKEN anchors     : {len(bad_anchor)}")
    for src, url in bad_anchor[:15]:
        print(f"   {src}  ->  {url}")

    print("\ntop external hosts:")
    for host, n in hosts.most_common(12):
        print(f"   {n:5}  {host}")

    return 1 if broken or bad_anchor else 0


if __name__ == "__main__":
    raise SystemExit(main())
