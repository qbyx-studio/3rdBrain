import json
from pathlib import Path

import pytest

from tools.agent_api import build_agent_api


def _base(tmp_path: Path) -> Path:
    root = tmp_path / "base"
    (root / "assets" / "discovery").mkdir(parents=True)
    (root / "guides").mkdir()
    (root / "guides" / "useful.md").write_text(
        "---\ndescription: Useful thing\n---\n\n# Useful\n\nFull private detail.\n",
        encoding="utf-8",
    )
    records = [{
        "id": "useful-123",
        "path": "guides/useful.md",
        "location": "/guides/useful/",
        "title": "Useful",
        "source_urls": ["https://example.com/source"],
        "search_text": "Useful private detail",
    }]
    (root / "assets" / "discovery" / "records.json").write_text(
        json.dumps(records), encoding="utf-8"
    )
    (root / "assets" / "discovery" / "taxonomy.json").write_text(
        json.dumps({"sections": ["Guides"]}), encoding="utf-8"
    )
    return root


def test_agent_api_contains_search_catalogue_and_full_page(tmp_path):
    root = _base(tmp_path)
    manifest = build_agent_api(root)

    assert manifest["read_only"] is True
    assert manifest["record_count"] == 1
    records = json.loads((root / "api" / "v1" / "records.json").read_text(encoding="utf-8"))
    assert records[0]["content_endpoint"] == "/api/v1/pages/useful-123.json"
    page = json.loads(
        (root / "api" / "v1" / "pages" / "useful-123.json").read_text(encoding="utf-8")
    )
    assert "Full private detail." in page["content_markdown"]
    assert page["content_sha256"] == records[0]["content_sha256"]


def test_agent_api_rejects_paths_outside_the_staged_base(tmp_path):
    root = _base(tmp_path)
    records_path = root / "assets" / "discovery" / "records.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))
    records[0]["path"] = "../secret.txt"
    records_path.write_text(json.dumps(records), encoding="utf-8")

    with pytest.raises(ValueError, match="unsafe path"):
        build_agent_api(root)


def test_main_build_always_generates_the_read_only_api():
    build = (Path(__file__).resolve().parents[1] / "build.sh").read_text(encoding="utf-8")
    assert 'tools/agent_api.py .build' in build
