from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from framework_freshness import draft_differences, framework_differences, framework_hash, probe, record  # noqa: E402
from validate_touched_pages import validate_touched  # noqa: E402


def init_repo(root: Path, framework_text: str) -> None:
    (root / "commands").mkdir(parents=True)
    (root / "commands" / "process.md").write_text(framework_text, encoding="utf-8")
    (root / "README.md").write_text("base-owned content", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)


def test_freshness_receipt_hits_only_for_same_source_and_local_framework(tmp_path: Path):
    source, local = tmp_path / "source", tmp_path / "local"
    init_repo(source, "public framework")
    init_repo(local, "adapted framework")
    differences = tmp_path / "differences.json"
    verification = tmp_path / "verification.json"
    receipt = tmp_path / "receipt.json"
    differences.write_text(json.dumps([
        {"path": "commands/process.md", "disposition": "adapted", "reason": "local command name"}
    ]), encoding="utf-8")
    verification.write_text(json.dumps({
        "build_passed": True, "tests_passed": True, "published": False
    }), encoding="utf-8")

    record(source, local, receipt, differences, verification)
    assert probe(source, local, receipt).fresh

    (local / "README.md").write_text("changed base content", encoding="utf-8")
    assert probe(source, local, receipt).fresh

    (local / "commands" / "process.md").write_text("changed framework", encoding="utf-8")
    result = probe(source, local, receipt)
    assert not result.fresh
    assert "local framework content changed" in result.reasons


def test_freshness_record_rejects_incomplete_evidence(tmp_path: Path):
    source, local = tmp_path / "source", tmp_path / "local"
    init_repo(source, "public")
    init_repo(local, "local")
    differences = tmp_path / "differences.json"
    verification = tmp_path / "verification.json"
    differences.write_text(
        '[{"path":"commands/process.md","disposition":"adapted"}]', encoding="utf-8"
    )
    verification.write_text('{"build_passed":true,"tests_passed":false}', encoding="utf-8")

    try:
        record(source, local, tmp_path / "receipt.json", differences, verification)
    except ValueError as exc:
        assert "passing build and test evidence" in str(exc)
    else:
        raise AssertionError("an incomplete verification must not produce FRESH")


def test_freshness_record_requires_a_disposition_for_every_real_difference(tmp_path: Path):
    source, local = tmp_path / "source", tmp_path / "local"
    init_repo(source, "public")
    init_repo(local, "adapted")
    assert framework_differences(source, local) == [
        {"path": "commands/process.md", "change": "changed"}
    ]
    differences = tmp_path / "differences.json"
    verification = tmp_path / "verification.json"
    differences.write_text("[]", encoding="utf-8")
    verification.write_text(
        '{"build_passed":true,"tests_passed":true,"published":false}', encoding="utf-8"
    )

    try:
        record(source, local, tmp_path / "receipt.json", differences, verification)
    except ValueError as exc:
        assert "missing=['commands/process.md']" in str(exc)
    else:
        raise AssertionError("FRESH must account for every actual framework difference")


def test_difference_draft_covers_every_path_for_review(tmp_path: Path):
    source, local = tmp_path / "source", tmp_path / "local"
    init_repo(source, "public")
    init_repo(local, "adapted")
    output = tmp_path / "draft.json"

    draft = draft_differences(source, local, output)

    assert draft == [{
        "path": "commands/process.md",
        "change": "changed",
        "disposition": "adapted",
        "reason": "base-specific framework state verified by the complete tests and build",
    }]
    assert json.loads(output.read_text(encoding="utf-8")) == draft


def test_framework_hash_skips_excluded_unreadable_paths(tmp_path: Path, monkeypatch):
    root = tmp_path / "repo"
    excluded = root / "_site" / ".venv" / "lib64"
    excluded.parent.mkdir(parents=True)
    excluded.write_text("runtime link placeholder", encoding="utf-8")
    original_is_file = Path.is_file

    def guarded_is_file(path: Path) -> bool:
        if path == excluded:
            raise OSError("unreadable runtime junction")
        return original_is_file(path)

    monkeypatch.setattr(Path, "is_file", guarded_is_file)
    assert framework_hash(root) == framework_hash(root)


def fixture_vault(tmp_path: Path) -> Path:
    (tmp_path / "marketing").mkdir()
    (tmp_path / "videos").mkdir()
    (tmp_path / "breakdowns").mkdir()
    (tmp_path / "SUMMARY.md").write_text(
        "## Marketing\n\n* [Email](marketing/email.md)\n\n"
        "## Videos\n\n* [Hub](videos/hub.md)\n",
        encoding="utf-8",
    )
    return tmp_path


def test_touched_gate_catches_taxonomy_backlink_and_video_embed_failures(tmp_path: Path):
    root = fixture_vault(tmp_path)
    (root / "marketing" / "email.md").write_text(
        "---\ntaxonomy_path: [Engineering]\n---\n# Email\n\n"
        "## Source\n[Watch](https://youtu.be/example)\n",
        encoding="utf-8",
    )
    (root / "videos" / "hub.md").write_text("[Email](../marketing/email.md)\n", encoding="utf-8")
    (root / "breakdowns" / "source.yml").write_text(
        "hub: videos/hub.md\nelements:\n"
        "  - id: email\n    start: '1:00'\n    page: marketing/email.md\n"
        "    page_type: workflow\n    taxonomy_path: [Marketing]\n",
        encoding="utf-8",
    )

    errors = validate_touched(root, {"marketing/email.md"})
    assert any("declared ['Engineering'], placed under ['Marketing']" in error for error in errors)
    assert any("child page does not link back to hub" in error for error in errors)
    assert any("video source must be a standalone embed block" in error for error in errors)


def test_touched_gate_accepts_a_fully_wired_page(tmp_path: Path):
    root = fixture_vault(tmp_path)
    (root / "marketing" / "email.md").write_text(
        "---\ntaxonomy_path: [Marketing]\n---\n# Email\n\n"
        "[Source hub](../videos/hub.md)\n\n## Source\n"
        '{% embed url="https://youtu.be/example" %}\n',
        encoding="utf-8",
    )
    (root / "videos" / "hub.md").write_text("[Email](../marketing/email.md)\n", encoding="utf-8")
    (root / "breakdowns" / "source.yml").write_text(
        "hub: videos/hub.md\nelements:\n"
        "  - id: email\n    start: '1:00'\n    page: marketing/email.md\n"
        "    page_type: workflow\n    taxonomy_path: [Marketing]\n",
        encoding="utf-8",
    )

    assert validate_touched(root, {"marketing/email.md"}) == []
