from __future__ import annotations

from pathlib import Path

from tools.verify_deployment_manifest import deployment_credentials, expected_paths, find_mismatches


def test_credentials_can_be_read_from_a_windows_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"CLOUDFLARE_API_TOKEN=test-token\r\nCLOUDFLARE_ACCOUNT_ID=test-account\r\n")

    assert deployment_credentials(env_file) == ("test-token", "test-account")


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
