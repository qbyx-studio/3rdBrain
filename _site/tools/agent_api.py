"""Build the static, read-only 3rdBrain agent API from staged discovery data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "-", value).strip(".-")
    if not cleaned:
        raise ValueError("Discovery record has an invalid empty ID")
    return cleaned


def build_agent_api(root: Path, output: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    discovery = root / "assets" / "discovery"
    records_path = discovery / "records.json"
    taxonomy_path = discovery / "taxonomy.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))
    taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Discovery records must be a JSON list")

    api_root = (output or root / "api" / "v1").resolve()
    if api_root.exists():
        shutil.rmtree(api_root)
    pages_root = api_root / "pages"
    pages_root.mkdir(parents=True, exist_ok=True)

    api_records: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every discovery record must be an object")
        identifier = _safe_id(str(record.get("id", "")))
        relative = Path(str(record.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Discovery record {identifier} has an unsafe path")
        source = (root / relative).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise FileNotFoundError(f"Discovery record {identifier} points to missing page {relative}")
        markdown = source.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
        endpoint = f"/api/v1/pages/{identifier}.json"
        page = {
            "schema": 1,
            "id": identifier,
            "title": record.get("title"),
            "path": record.get("path"),
            "location": record.get("location"),
            "source_urls": record.get("source_urls") or [],
            "content_sha256": content_hash,
            "content_markdown": markdown,
        }
        _write_json(pages_root / f"{identifier}.json", page)
        api_records.append({**record, "content_endpoint": endpoint, "content_sha256": content_hash})

    _write_json(api_root / "records.json", api_records)
    _write_json(api_root / "taxonomy.json", taxonomy)
    manifest = {
        "schema": 1,
        "name": "3rdBrain read-only API",
        "read_only": True,
        "record_count": len(api_records),
        "endpoints": {
            "records": "/api/v1/records.json",
            "taxonomy": "/api/v1/taxonomy.json",
            "page_template": "/api/v1/pages/{id}.json",
        },
    }
    _write_json(api_root / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="staged 3rdBrain content root")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(json.dumps(build_agent_api(args.root, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
