from __future__ import annotations

from pathlib import Path

from tools.summary_to_nav import find_missing_published_targets


def test_route_contract_ignores_labels_and_maps_markdown_to_published_html(tmp_path: Path):
    build = tmp_path / ".build"
    site = tmp_path / "site"
    (build / "agents" / "vendor-hub").mkdir(parents=True)
    (site / "agents" / "vendor-hub" / "setup-guide").mkdir(parents=True)
    (build / "agents" / "vendor-hub" / "setup-guide.md").write_text(
        "# Setup guide\n", encoding="utf-8"
    )
    (site / "agents" / "vendor-hub" / "setup-guide" / "index.html").write_text(
        "<h1>Setup guide</h1>\n", encoding="utf-8"
    )
    nav = """* Vendor Hub
    * [Setup guide](agents/vendor-hub/setup-guide.md)
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
