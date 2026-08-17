"""Check external links for real. Unique URLs only, concurrent, HEAD then GET."""
from __future__ import annotations
import collections
import os, re, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (link-check)"}
URL_RE = re.compile(r'(?:href|src)="(https?://[^"]+)"')

def check(url: str) -> tuple[str, int | str]:
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, headers=UA, method=method)
            with urllib.request.urlopen(req, timeout=12) as r:
                return url, r.status
        except urllib.error.HTTPError as e:
            if method == "GET" or e.code not in (403, 405, 501):
                return url, e.code
        except Exception as e:
            if method == "GET":
                return url, type(e).__name__
    return url, "?"

def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    urls = set()
    for f in site.rglob("*.html"):
        urls |= set(URL_RE.findall(f.read_text(encoding="utf-8", errors="replace")))
    # Skip the player origin (an embed URL, not a page) and the site's own
    # canonical links, which only resolve once it is deployed.
    own = os.environ.get("SITE_HOST", "pages.dev")
    skip = ("youtube-nocookie", own, "fonts.gstatic.com")
    urls = {u for u in urls if not any(k in u for k in skip)}
    print(f"unique external URLs: {len(urls)}")
    with ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(check, sorted(urls)))
    bad = [(u, s) for u, s in results if not (isinstance(s, int) and s < 400)]
    counts = collections.Counter(s for _, s in results)
    print("status summary:", dict(counts.most_common(8)))
    print(f"\nFAILING: {len(bad)}")
    for u, s in sorted(bad, key=lambda x: str(x[1]))[:30]:
        print(f"   {str(s):>12}  {u[:90]}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
