from __future__ import annotations

from pathlib import Path

from tools.summary_to_nav import find_missing_published_targets


def test_route_contract_ignores_labels_and_maps_markdown_to_published_html(tmp_path: Path):
    build = tmp_path / ".build"
    site = tmp_path / "site"
    (build / "agents" / "grok-bot").mkdir(parents=True)
    (site / "agents" / "grok-bot" / "nine-hacks").mkdir(parents=True)
    (build / "agents" / "grok-bot" / "nine-hacks.md").write_text(
        "# Nine hacks\n", encoding="utf-8"
    )
    (site / "agents" / "grok-bot" / "nine-hacks" / "index.html").write_text(
        "<h1>Nine hacks</h1>\n", encoding="utf-8"
    )
    nav = """* Grok Bot
    * [Nine hacks](agents/grok-bot/nine-hacks.md)
"""

    assert find_missing_published_targets(nav, build, site) == []


def test_route_contract_reports_missing_source_and_missing_output(tmp_path: Path):
    build = tmp_path / ".build"
    site = tmp_path / "site"
    build.mkdir()
    site.mkdir()
    (build / "exists.md").write_text("# Exists\n", encoding="utf-8")
    nav = """* [Missing source](missing.md)
* [Missing output](exists.md)
"""

    assert find_missing_published_targets(nav, build, site) == [
        "missing.md (source missing)",
        "exists.md -> exists/index.html",
    ]
