# -*- coding: utf-8 -*-
"""3rdBrain staleness check — REPORT ONLY.

Reads each content page's "Added" date, its facet class, and (optionally) checks
links, then prints a review QUEUE. It never edits or deletes anything. A future
--flag mode may add a reversible "possibly dated" banner; this version does not.

Usage, from the base folder:
    python _site/tools/stalecheck.py             # full report to stdout
    python _site/tools/stalecheck.py --top 25    # limit list lengths
    python _site/tools/stalecheck.py --out FILE  # also write the report to a file

It reads only. Nothing in the base is edited, bannered, merged or removed.

Signals (report-only):
  1. OVERDUE     age(Added) > per-class threshold (class = most-volatile facet)
  2. WATCHLIST   the pages closest to their threshold (what ages next)
  3. SUPERSEDE?  heuristic: same product name, a higher version exists in the base
"""
import os, re, sys, subprocess, datetime, glob

# Content root. _site/tools/stalecheck.py sits two levels below the base, and
# VAULT overrides that the same way build.sh does, so this works whether the
# machinery lives inside the base or beside a separate content folder.
_SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.abspath(os.environ.get("VAULT") or os.path.dirname(_SITE))
TODAY = datetime.date.today()

# facet -> soft half-life in DAYS (most-volatile facet on a page sets its threshold)
FACET_TTL = {
    'Roundup': 75, 'Model': 75,                         # reviews / model pages age fastest
    'Website': 180, 'Video': 180, 'Image': 180, 'Music': 180, 'Voice': 180,
    'Design': 180, '3D': 180, 'Game': 180, 'Data': 180, 'SEO': 150, 'Browser': 180,
    'Leads': 180, 'Finance': 180, 'MCP': 180, 'Automation': 210, 'Simulation': 210,
    'Research': 210,
    'Prompt': 330, 'Workflow': 330, 'Skill': 300, 'Agent': 300, 'Writing': 330,  # durable techniques
}
DEFAULT_TTL = 180

ADDED_RE = re.compile(r'Added\s+(\d{4})-(\d{2})-(\d{2})')
FACET_RE = re.compile(r'\*\*Facets:\*\*(.+)')
FACET_NAME_RE = re.compile(r'\[([A-Za-z0-9]+)\]\(\.\.+/facets/')
H1_RE = re.compile(r'^#\s+(.+)$', re.M)
VER_RE = re.compile(r'\b([A-Za-z][A-Za-z0-9 .+/-]*?)\s+v?(\d+(?:\.\d+)+)\b')


def content_pages():
    for f in glob.glob(os.path.join(BASE, '**', '*.md'), recursive=True):
        p = os.path.relpath(f, BASE).replace(os.sep, '/')
        if p.startswith('_site/') or p.startswith('facets/'):
            continue
        if p in ('SUMMARY.md', 'README.md') or p.endswith('/README.md'):
            continue
        yield p


def git_first_added(relpath):
    try:
        out = subprocess.run(['git', 'log', '--diff-filter=A', '--format=%as', '--', relpath],
                             cwd=BASE, capture_output=True, text=True).stdout.strip().splitlines()
        if out:
            y, m, d = out[-1].split('-')
            return datetime.date(int(y), int(m), int(d))
    except Exception:
        pass
    return TODAY


def parse(relpath):
    txt = open(os.path.join(BASE, relpath.replace('/', os.sep)), encoding='utf-8').read()
    m = ADDED_RE.search(txt[:400])
    added = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else git_first_added(relpath)
    fm = FACET_RE.search(txt)
    facets = set(FACET_NAME_RE.findall(fm.group(1))) if fm else set()
    h1 = H1_RE.search(txt)
    title = h1.group(1).strip() if h1 else os.path.basename(relpath)
    return added, facets, title


def ttl_for(facets):
    """Threshold from the most volatile CAPABILITY facet on the page.

    Only facets in FACET_TTL are volatility classes. Access and platform facets
    (Free, Paid, OpenSource, Claude, ChatGPT ...) say nothing about how fast a
    page rots, and every page carries one, so treating them as DEFAULT_TTL let
    them win the min() and silently pinned the whole base to 180 days. That made
    the durable tier for Prompt, Workflow, Skill and Agent unreachable.
    """
    classed = [(FACET_TTL[f], f) for f in facets if f in FACET_TTL]
    if not classed:
        return DEFAULT_TTL, '(unclassed)'
    ttl, driver = min(classed)
    return ttl, driver


def norm_name(title):
    t = VER_RE.sub(lambda mm: mm.group(1), title)
    t = re.sub(r'\b(review|model|test|battery|prompts?|hub|vs\.?|comparison)\b', ' ', t, flags=re.I)
    t = re.sub(r'[^a-z0-9 ]', ' ', t.lower())
    return ' '.join(t.split())


def main():
    args = sys.argv[1:]
    top = 25
    out_file = None
    if '--top' in args:
        top = int(args[args.index('--top') + 1])
    if '--out' in args:
        out_file = args[args.index('--out') + 1]

    rows = []
    vermap = {}  # product name -> list of (version_tuple, page, title)
    for p in content_pages():
        added, facets, title = parse(p)
        ttl, drv = ttl_for(facets)
        age = (TODAY - added).days
        rows.append({'p': p, 'added': added, 'age': age, 'ttl': ttl, 'drv': drv,
                     'over': age - ttl, 'facets': facets, 'title': title})
        for name, ver in VER_RE.findall(title):
            key = norm_name(name + ' 0')
            if not key or len(key) < 2:
                continue
            vt = tuple(int(x) for x in ver.split('.'))
            vermap.setdefault(key, []).append((vt, p, title, ver))

    overdue = sorted([r for r in rows if r['over'] > 0], key=lambda r: -r['over'])
    watch = sorted([r for r in rows if r['over'] <= 0], key=lambda r: r['over'], reverse=True)[:top]

    superseded = []
    for key, items in vermap.items():
        vers = {i[0] for i in items}
        if len(vers) > 1:
            mx = max(vers)
            for vt, p, title, ver in items:
                if vt < mx:
                    newer = [i for i in items if i[0] == mx]
                    superseded.append((p, title, ver, '.'.join(map(str, mx)), newer[0][1]))

    L = []
    def w(s=''):
        L.append(s)

    w('# 3rdBrain staleness report  (report-only, no edits made)')
    w('run date: %s   |   content pages scanned: %d' % (TODAY, len(rows)))
    w('')
    w('## 1. OVERDUE  (age > class threshold)  - %d' % len(overdue))
    if not overdue:
        w('none yet. The base is young; the oldest page is %d days old. This section fills as pages age.'
          % max(r['age'] for r in rows))
    for r in overdue[:top]:
        w('  +%-4dd over  | %-3d/%-3dd | %-8s | %s' % (r['over'], r['age'], r['ttl'], r['drv'], r['p']))
    w('')
    w('## 2. WATCHLIST  (closest to their threshold - what ages next)  - top %d' % top)
    for r in watch:
        w('  %4dd left | %-3d/%-3dd | %-8s | %s' % (-r['over'], r['age'], r['ttl'], r['drv'], r['p']))
    w('')
    w('## 3. SUPERSEDE?  (heuristic - a higher version of the same name exists; VERIFY)  - %d' % len(superseded))
    for p, title, ver, mx, newerp in sorted(superseded):
        w('  v%s < v%s | %s  ->  newer: %s' % (ver, mx, p, newerp))
    if not superseded:
        w('  none detected by the version heuristic.')
    w('')
    w('## class thresholds (days): Roundup/Model 75 | medium tools 180 | durable (Prompt/Workflow/Skill/Agent) 300-330 | default 180')
    w('## DEFERRED (not built): --links, wrapping tools/check_external.py for dead links; --flag, a reversible "possibly dated" banner.')

    report = '\n'.join(L)
    print(report)
    if out_file:
        open(out_file, 'w', encoding='utf-8').write(report)
        print('\n[written to %s]' % out_file)


if __name__ == '__main__':
    main()
