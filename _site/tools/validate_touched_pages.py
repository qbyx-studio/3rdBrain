"""Fast deterministic gate for pages written by the current curation batch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from content_integrity import video_source_offenders  # noqa: E402
from knowledge_index import (  # noqa: E402
    normalize_path,
    parse_summary,
    validate_breakdown_manifest,
    validate_declared_paths,
)


def _manifest_paths(manifest: dict) -> set[str]:
    paths = {normalize_path(str(manifest.get("hub") or ""))}
    paths.update(
        normalize_path(str(element.get("page") or ""))
        for element in manifest.get("elements") or []
        if isinstance(element, dict)
    )
    return {path for path in paths if path}


def validate_touched(root: Path, touched: set[str]) -> list[str]:
    touched = {normalize_path(path) for path in touched}
    errors: list[str] = []
    summary = root / "SUMMARY.md"
    if not summary.exists():
        return ["SUMMARY.md is missing"]
    navigation = parse_summary(summary.read_text(encoding="utf-8-sig"))

    taxonomy_errors = validate_declared_paths(root, navigation)
    if "SUMMARY.md" in touched:
        errors.extend(taxonomy_errors)
    else:
        errors.extend(
            error for error in taxonomy_errors
            if error.split(":", 1)[0] in touched
        )

    markdown_pages = {path for path in touched if path.endswith(".md")}
    for page, url in video_source_offenders(root, markdown_pages):
        errors.append(f"{page}: video source must be a standalone embed block ({url})")

    breakdown_root = root / "breakdowns"
    if breakdown_root.exists():
        for manifest_path in sorted(breakdown_root.glob("*.yml")):
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            relative_manifest = manifest_path.relative_to(root).as_posix()
            if relative_manifest not in touched and not (_manifest_paths(manifest) & touched):
                continue
            errors.extend(
                f"{relative_manifest}: {error}"
                for error in validate_breakdown_manifest(manifest, root)
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--paths", nargs="+", required=True)
    args = parser.parse_args()
    errors = validate_touched(args.root.resolve(), set(args.paths))
    if errors:
        print("touched-page validation failed:")
        for error in errors:
            print("  " + error)
        return 1
    print(f"touched-page validation: OK ({len(set(args.paths))} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
