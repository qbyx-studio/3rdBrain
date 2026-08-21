"""Verify that Cloudflare stored every published path with exact casing."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path


def expected_paths(site: Path) -> set[str]:
    return {
        "/" + path.relative_to(site).as_posix()
        for path in site.rglob("*")
        if path.is_file()
    }


def find_mismatches(site: Path, manifest: dict[str, str]) -> tuple[list[str], list[str]]:
    expected = expected_paths(site)
    actual = set(manifest)
    return sorted(expected - actual), sorted(actual - expected)


def api_json(url: str, token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if not payload.get("success"):
        raise RuntimeError(f"Cloudflare API rejected manifest request: {payload.get('errors')}")
    return payload


def latest_branch_manifest(account: str, project: str, branch: str, token: str) -> dict[str, str]:
    base = f"https://api.cloudflare.com/client/v4/accounts/{account}/pages/projects/{project}"
    deployments = api_json(f"{base}/deployments?per_page=25", token)["result"]
    for deployment in deployments:
        metadata = (deployment.get("deployment_trigger") or {}).get("metadata") or {}
        if metadata.get("branch") != branch:
            continue
        detail = api_json(f"{base}/deployments/{deployment['id']}", token)["result"]
        files = detail.get("files")
        if isinstance(files, dict):
            return files
    raise RuntimeError(f"No deployment manifest found for branch {branch!r}")


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: verify_deployment_manifest.py SITE_DIR PROJECT BRANCH", file=sys.stderr)
        return 2
    site, project, branch = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    if not token or not account:
        print("manifest verify: Cloudflare credentials are missing", file=sys.stderr)
        return 2

    last: tuple[list[str], list[str]] | None = None
    for attempt in range(10):
        manifest = latest_branch_manifest(account, project, branch, token)
        last = find_mismatches(site, manifest)
        if not last[0] and not last[1]:
            print(f"manifest verify: {len(manifest)} exact-case paths match Cloudflare")
            return 0
        if attempt < 9:
            time.sleep(2)

    missing, unexpected = last or ([], [])
    print(f"manifest verify: {len(missing)} missing, {len(unexpected)} unexpected", file=sys.stderr)
    for path in missing[:10]:
        print(f"  missing: {path}", file=sys.stderr)
    for path in unexpected[:10]:
        print(f"  unexpected: {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
