from __future__ import annotations

from pathlib import Path

from tools.verify_deployment_manifest import expected_paths, find_mismatches


def test_expected_paths_preserve_exact_case(tmp_path: Path):
    page = tmp_path / "agents" / "example" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text("ok", encoding="utf-8")
    assert expected_paths(tmp_path) == {"/agents/example/index.html"}


def test_manifest_comparison_reports_case_only_route_mismatches(tmp_path: Path):
    page = tmp_path / "agents" / "example" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text("ok", encoding="utf-8")

    missing, unexpected = find_mismatches(
        tmp_path, {"/AGENTS/example/index.html": "hash"}
    )

    assert missing == ["/agents/example/index.html"]
    assert unexpected == ["/AGENTS/example/index.html"]
