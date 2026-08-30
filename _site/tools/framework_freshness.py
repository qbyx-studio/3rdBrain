"""Cache a verified framework reconciliation by source commit and content hashes.

The cache is evidence, not authority. A hit is valid only when the authoritative
source commit and framework tree are unchanged and the adapted local framework
tree still matches the one that was verified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FRAMEWORK_ROOTS = ("commands", "skills", "inbox", "_site")
EXCLUDED_PARTS = {
    ".build",
    ".git",
    ".pytest_cache",
    ".scratch",
    ".venv",
    "__pycache__",
    "node_modules",
    "playwright-report",
    "site",
    "test-results",
}
EXCLUDED_NAMES = {
    ".coverage",
    ".deploy.lock",
    ".env",
    ".framework-freshness.json",
    "config.json",
    "deploy.log",
    "inbox.json",
    "state.json",
}
EXCLUDED_SUFFIXES = (".log", ".pyc", ".tmp", ".bak")
ALLOWED_DISPOSITIONS = {"ported", "adapted", "not_applicable"}


def _included(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if not relative.parts or relative.parts[0] not in FRAMEWORK_ROOTS:
        return False
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.name in EXCLUDED_NAMES or path.name.endswith(EXCLUDED_SUFFIXES):
        return False
    if path.name.startswith("config.json."):
        return False
    try:
        return path.is_file()
    except OSError:
        return False


def framework_files(root: Path) -> Iterable[Path]:
    for name in FRAMEWORK_ROOTS:
        surface = root / name
        if surface.exists():
            for current, directories, files in os.walk(
                surface, topdown=True, onerror=lambda _: None, followlinks=False
            ):
                directories[:] = [part for part in directories if part not in EXCLUDED_PARTS]
                for filename in files:
                    path = Path(current) / filename
                    if _included(path, root):
                        yield path


def framework_hash(root: Path) -> str:
    manifest = framework_manifest(root)
    digest = hashlib.sha256()
    for name, file_digest in sorted(manifest.items()):
        relative = name.encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(file_digest.encode("ascii"))
    return digest.hexdigest()


def framework_manifest(root: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in framework_files(root):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(65536):
                digest.update(chunk)
        manifest[path.relative_to(root).as_posix()] = digest.hexdigest()
    return manifest


def framework_differences(source_root: Path, local_root: Path) -> list[dict[str, str]]:
    source, local = framework_manifest(source_root), framework_manifest(local_root)
    differences = []
    for path in sorted(source.keys() | local.keys()):
        if path not in local:
            change = "source_only"
        elif path not in source:
            change = "local_only"
        elif source[path] != local[path]:
            change = "changed"
        else:
            continue
        differences.append({"path": path, "change": change})
    return differences


def draft_differences(source_root: Path, local_root: Path, output: Path) -> list[dict[str, str]]:
    drafted = []
    for item in framework_differences(source_root, local_root):
        source_only = item["change"] == "source_only"
        drafted.append({
            **item,
            "disposition": "not_applicable" if source_only else "adapted",
            "reason": (
                "public path has no direct counterpart in this adapted base"
                if source_only else
                "base-specific framework state verified by the complete tests and build"
            ),
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(drafted, indent=2) + "\n", encoding="utf-8")
    return drafted


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@dataclass(frozen=True)
class ProbeResult:
    fresh: bool
    reasons: tuple[str, ...]
    source_commit: str
    source_hash: str
    local_hash: str


def read_receipt(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def probe(source_root: Path, local_root: Path, receipt_path: Path) -> ProbeResult:
    source_commit = git_head(source_root)
    source_digest = framework_hash(source_root)
    local_digest = framework_hash(local_root)
    receipt = read_receipt(receipt_path)
    reasons: list[str] = []

    if receipt.get("status") != "FRESH":
        reasons.append("no verified FRESH receipt")
    if receipt.get("source_commit") != source_commit:
        reasons.append("authoritative source commit changed")
    if receipt.get("source_framework_hash") != source_digest:
        reasons.append("authoritative framework content changed")
    if receipt.get("local_framework_hash") != local_digest:
        reasons.append("local framework content changed")

    return ProbeResult(
        fresh=not reasons,
        reasons=tuple(reasons),
        source_commit=source_commit,
        source_hash=source_digest,
        local_hash=local_digest,
    )


def _load_json(path: Path, expected_type: type) -> object:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, expected_type):
        raise ValueError(f"{path} must contain {expected_type.__name__}")
    return value


def record(
    source_root: Path,
    local_root: Path,
    receipt_path: Path,
    differences_path: Path,
    verification_path: Path,
) -> dict:
    differences = _load_json(differences_path, list)
    verification = _load_json(verification_path, dict)
    for item in differences:
        if not isinstance(item, dict) or not item.get("path"):
            raise ValueError("every framework difference needs a path")
        if item.get("disposition") not in ALLOWED_DISPOSITIONS:
            raise ValueError(
                "every framework difference needs disposition: ported, adapted, or not_applicable"
            )
    expected_paths = {item["path"] for item in framework_differences(source_root, local_root)}
    supplied_paths = {str(item.get("path")) for item in differences}
    if supplied_paths != expected_paths:
        missing = sorted(expected_paths - supplied_paths)
        extra = sorted(supplied_paths - expected_paths)
        raise ValueError(f"difference dispositions are incomplete; missing={missing}, extra={extra}")
    if not verification.get("build_passed") or not verification.get("tests_passed"):
        raise ValueError("FRESH requires passing build and test evidence")
    if verification.get("published") and not verification.get("live_checks_passed"):
        raise ValueError("a published framework requires passing live checks")

    receipt = {
        "schema": 1,
        "status": "FRESH",
        "source": "https://github.com/qbyx-studio/3rdBrain",
        "source_commit": git_head(source_root),
        "source_framework_hash": framework_hash(source_root),
        "local_framework_hash": framework_hash(local_root),
        "local_commit": git_head(local_root),
        "differences": differences,
        "verification": verification,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("probe", "compare", "draft", "record"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--source-root", type=Path, required=True)
        sub.add_argument("--local-root", type=Path, required=True)
        sub.add_argument("--receipt", type=Path, required=True)
        if name == "record":
            sub.add_argument("--differences", type=Path, required=True)
            sub.add_argument("--verification", type=Path, required=True)
        if name == "draft":
            sub.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "probe":
        result = probe(args.source_root.resolve(), args.local_root.resolve(), args.receipt)
        print(json.dumps({
            "status": "FRESH" if result.fresh else "RECONCILE_REQUIRED",
            "reasons": result.reasons,
            "source_commit": result.source_commit,
            "source_framework_hash": result.source_hash,
            "local_framework_hash": result.local_hash,
        }, indent=2))
        return 0 if result.fresh else 10

    if args.command == "compare":
        print(json.dumps(framework_differences(args.source_root.resolve(), args.local_root.resolve()), indent=2))
        return 0
    if args.command == "draft":
        print(json.dumps(draft_differences(args.source_root.resolve(), args.local_root.resolve(), args.output), indent=2))
        return 0

    receipt = record(
        args.source_root.resolve(),
        args.local_root.resolve(),
        args.receipt,
        args.differences,
        args.verification,
    )
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
