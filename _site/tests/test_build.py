"""Regression tests for the build pipeline.

Every assertion here corresponds to a bug that actually occurred while building
this site. Run against a completed build:

    cd _site && VAULT=.. bash build.sh

The build runs them for you. To run them alone, use the interpreter inside .venv
(.venv/bin/python, or .venv/Scripts/python.exe on Windows):

    .venv/bin/python -m pytest tests -q
"""

from __future__ import annotations

import json
import sys
import subprocess
import re
import urllib.parse
from pathlib import Path

import pytest

pytestmark: list = []

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / ".build"
SITE = ROOT / "site"


@pytest.fixture(scope="session", autouse=True)
def built():
    if not (SITE / "index.html").exists():
        pytest.skip("no build present; run build.sh first")


def source_files() -> list[Path]:
    return [p for p in BUILD.rglob("*.md")
            if p.name not in ("SUMMARY.md", "NAV.md", "NAV-EXTRA.md")]


def source_count(pattern: str) -> int:
    """How many times the source asks for a construct, outside code fences."""
    total = 0
    for p in source_files():
        text = read(p)
        # Drop fenced blocks: syntax shown as an example is not a request.
        text = re.sub(r"^(`{3,}|~{3,}).*?^", "", text, flags=re.S | re.M)
        total += len(re.findall(pattern, text, re.M))
    return total


def html_files() -> list[Path]:
    return list(SITE.rglob("*.html"))


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


# --- conversion ----------------------------------------------------------

def test_no_unconverted_gitbook_syntax_outside_code_blocks():
    """Inline embeds were missed at first: 35 sat mid-sentence, not on their
    own line, and shipped raw onto 23 pages."""
    offenders = []
    for f in html_files():
        text = read(f)
        # Strip code blocks; GitBook syntax inside them is deliberate.
        stripped = re.sub(r"<code[^>]*>.*?</code>", "", text, flags=re.S)
        if "{%" in stripped:
            offenders.append(f.relative_to(SITE).as_posix())
    assert offenders == [], f"raw GitBook syntax rendered on: {offenders}"


def test_syntax_template_page_is_not_converted():
    """mining-page-template.md documents the format by showing {% prompt %}
    inside a fence. Converting those examples corrupted the template."""
    page = SITE / "claude-setup" / "mining-page-template" / "index.html"
    if not page.exists():
        pytest.skip("this base has no syntax-template page")
    text = read(page)
    assert text.count("{% prompt") >= 3, "template examples were converted away"
    assert "???+ note" not in text, "admonition syntax leaked into the template"


def test_every_prompt_block_became_a_collapsible():
    want = source_count(r"^\{%\s*prompt")
    got = sum(read(f).count('<details class="note"') for f in html_files())
    assert got == want, f"source asks for {want} prompt blocks, rendered {got}"


def test_youtube_embeds_became_players():
    want = source_count(r"^\{%\s*embed\s+url=\"[^\"]*(?:youtube\.com|youtu\.be)")
    got = sum(read(f).count('class="gb-video"') for f in html_files())
    assert got == want, f"source asks for {want} video players, rendered {got}"


# --- assets --------------------------------------------------------------

def test_every_referenced_asset_exists():
    """GitBook keeps assets in a dot-directory that MkDocs ignores."""
    missing = set()
    for f in html_files():
        for m in re.finditer(r'src="/gitbook-assets/([^"]+)"', read(f)):
            rel = urllib.parse.unquote(m.group(1))
            if not (SITE / "gitbook-assets" / rel).exists():
                missing.add(rel)
    assert missing == set(), f"broken image references: {sorted(missing)[:5]}"


# --- navigation ----------------------------------------------------------

def test_nav_covers_every_summary_entry():
    """literate-nav silently ignores '## headings', which dropped the whole nav."""
    summary = read(BUILD / "SUMMARY.md")
    nav = read(BUILD / "NAV.md")
    targets = set(re.findall(r"\]\(([^)]+\.md)\)", summary))
    missing = {t for t in targets if t not in nav}
    assert missing == set(), f"nav lost entries: {sorted(missing)[:5]}"


def test_admin_page_is_last_in_nav():
    nav = read(BUILD / "NAV.md").rstrip().splitlines()
    assert "admin.md" in nav[-1], f"admin should be last, got: {nav[-1]!r}"


# --- search --------------------------------------------------------------

def index_docs() -> list[dict]:
    return json.loads(read(SITE / "search" / "search_index.json"))["docs"]


def test_redundant_facet_hubs_are_not_indexed():
    """The 30 hand-maintained hubs repeat every page title and buried results."""
    hubs = [d for d in index_docs() if re.match(r"^facets/[^/#]+/", d["location"])]
    assert hubs == [], f"{len(hubs)} facet-hub docs still indexed"


def test_tool_index_is_boosted():
    boosts = {d["location"]: d.get("boost") for d in index_docs()}
    assert boosts.get("tool-index/") == 4.0


def test_admin_page_is_not_indexed():
    """Its existence should not be discoverable through search."""
    assert not [d for d in index_docs() if d["location"].startswith("admin/")]


# --- tags ----------------------------------------------------------------

def test_tags_were_derived_from_facet_footers():
    tagged = sum(1 for p in BUILD.rglob("*.md") if re.search(r"^tags:", read(p), re.M))
    footers = source_count(r"^\*\*Facets:\*\*")
    assert tagged >= footers, f"{footers} pages carry a facet footer, only {tagged} tagged"


def test_facet_footers_were_removed_from_pages():
    """Tags replace the footer; leaving both duplicates the information and
    leaves links to hub pages that are no longer the source of truth."""
    # Anchored: prose that merely mentions the footer is not a footer.
    footer = re.compile(r"^\*\*Facets:\*\*", re.M)
    leftovers = [p.name for p in BUILD.rglob("*.md") if footer.search(read(p))]
    assert leftovers == [], f"footers remain on: {leftovers[:5]}"


# --- brand ---------------------------------------------------------------

def test_brand_assets_are_published():
    assert (SITE / "assets" / "qbyx-logo.png").exists()
    assert (SITE / "assets" / "favicon.png").exists()


def test_brand_stylesheet_is_loaded_and_dark_first():
    home = read(SITE / "index.html")
    assert "brand.css" in home
    css = read(SITE / "stylesheets" / "brand.css")
    assert "#04060c" in css.lower(), "Night 950 ground colour missing"
    assert "Space Grotesk" in css


# --- the vault is never modified ----------------------------------------

def test_build_never_writes_to_the_vault():
    """GitBook syncs the content bidirectionally; writing to it would fight that.

    Checks whichever layout is in use: a local vault/ mirror during development,
    or the parent repository when this project lives inside it as _site/.
    """
    vault = ROOT / "vault"
    if not vault.exists():
        vault = ROOT.parent          # same-repo layout
    if not (vault / "SUMMARY.md").exists():
        pytest.skip("no content directory to check")
    # This project's own folder sits inside the content repo in the same-repo
    # layout; its build artefacts are not writes into the content.
    strays = [p for p in vault.rglob("NAV.md") if not p.is_relative_to(ROOT)]
    assert not strays, f"build artefact written into content: {strays}"
    sample = vault / "general" / "pxpipe.md"
    if sample.exists():
        text = read(sample)
        assert "**Facets:**" in text, "vault page was stripped in place"
        assert not re.search(r"^tags:", text, re.M), "vault page was tagged in place"


# --- rendering of converted blocks --------------------------------------

def test_link_cards_render_real_anchors():
    """A block-level <div> swallows its contents unless it carries
    markdown="1", which left all 130 cards showing raw '[label](url)'."""
    total = broken = 0
    for f in html_files():
        for body in re.findall(r'<div class="gb-card"[^>]*>([\s\S]*?)</div>', read(f)):
            total += 1
            if "<a " not in body:
                broken += 1
    assert broken == 0, f"{broken} of {total} cards rendered without a working link"


def test_no_literal_icon_shortcodes_anywhere():
    offenders = [f.relative_to(SITE).as_posix() for f in html_files()
                 if ":material-" in read(f)]
    assert offenders == [], f"unrendered icon shortcodes on: {offenders[:5]}"


def test_video_players_send_a_referrer():
    """YouTube answers 'Error 153' when an embed sends no referrer."""
    offenders = [f.relative_to(SITE).as_posix() for f in html_files()
                 if "referrerpolicy" in read(f)]
    assert offenders == [], f"referrerpolicy would break playback on: {offenders[:5]}"


def test_every_video_has_a_fallback_link():
    players = sum(read(f).count('class="gb-video"') for f in html_files())
    fallbacks = sum(read(f).count('class="gb-video-link"') for f in html_files())
    assert fallbacks == players, f"{players} players but {fallbacks} fallback links"


def test_assets_with_spaces_and_parentheses_resolve():
    """'_ARTICLE-TEMPLATE (1).docx' was truncated at the first parenthesis."""
    page = SITE / "projects" / "yvechat" / "articles" / "index.html"
    if not page.exists():
        pytest.skip("page not in this build")
    hrefs = re.findall(r'href="(/gitbook-assets/[^"]+)"', read(page))
    assert hrefs, "no asset link on the page"
    for h in hrefs:
        rel = urllib.parse.unquote(h[len("/gitbook-assets/"):])
        assert (SITE / "gitbook-assets" / rel).exists(), f"unresolvable: {h}"


# --- links ---------------------------------------------------------------

# All source-vault link breaks have been fixed, so the allowance is empty and
# any new broken internal link fails the build.
KNOWN_CONTENT_BREAKS: set[str] = set()


@pytest.mark.content
def test_no_new_broken_internal_links():
    """Content check, not a build check.

    A link can be broken because the content pipeline is mid-run and has not
    written the target page yet. That must be reported, but it must never stop
    the site from publishing, so build.sh runs this separately.
    """
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_links.py"), str(SITE)],
        capture_output=True, text=True).stdout
    found = set(re.findall(r"->\s+(\S+)$", out, re.M))
    unexpected = found - KNOWN_CONTENT_BREAKS
    assert not unexpected, f"new broken links: {sorted(unexpected)[:5]}"


# --- heading anchors -----------------------------------------------------

def test_headings_use_gitbook_slug_rules():
    """GitBook maps each space to a separator; Python-Markdown collapses runs.

    Every in-page anchor in the base was authored against GitBook, so the
    renderer must follow GitBook's rule or those links break. Rewriting the
    content instead would fix this site and break the GitBook one.
    """
    import sys
    sys.path.insert(0, str(ROOT))
    from slugs import slugify

    assert slugify("Ops manager + Brock's cold-email fixes") == "ops-manager--brocks-cold-email-fixes"
    assert slugify("The launch: 10-15 targeted, not 5,000") == "the-launch-10-15-targeted-not-5000"
    # A single space stays a single separator.
    assert slugify("Step 1 Pick the niche") == "step-1-pick-the-niche"


@pytest.mark.content
def test_no_broken_in_page_anchors():
    """Anchors are content, so this reports rather than blocks a deploy."""
    import subprocess
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_links.py"), str(SITE)],
        capture_output=True, text=True).stdout
    m = re.search(r"BROKEN anchors\s*:\s*(\d+)", out)
    assert m, "link checker produced no anchor count"
    assert int(m.group(1)) == 0, f"{m.group(1)} broken anchors:\n{out}"


def test_raw_html_links_to_pages_are_resolved():
    """MkDocs rewrites Markdown links to .md pages but ignores raw HTML ones.

    GitBook renders both, so pages authored there can carry
    <a href="other-page.md">. Those must be resolved at render time, not left to
    404, and not fixed by editing content that is valid at the source.
    """
    offenders = []
    for f in html_files():
        for m in re.finditer(r'<a\s[^>]*href="([^":]+\.md)"', read(f)):
            offenders.append(f"{f.relative_to(SITE).as_posix()} -> {m.group(1)}")
    assert offenders == [], f"unresolved raw HTML page links: {offenders[:5]}"
