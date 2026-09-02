import importlib.util
import io
import json
import re
from pathlib import Path
from urllib.error import HTTPError

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "3rdbrain-connect" / "scripts" / "connect.py"
SPEC = importlib.util.spec_from_file_location("thirdbrain_connect", SCRIPT)
connect = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(connect)


def test_connect_freshness_reference_resolves_in_this_base():
    skill_dir = SCRIPT.parent.parent
    entry = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    reference = re.search(r"`(\.\./[^`]+framework-freshness\.md)`", entry)
    assert reference, "Connect must route to the base's freshness instructions"
    assert (skill_dir / reference.group(1)).is_file()


class FakeClient:
    def __init__(self):
        self.tokens = []
        self.apps = []
        self.policies = {}
        self.deleted_tokens = []
        self.deleted_policies = []
        self.deleted_apps = []
        self.fail_policy = False

    def list_tokens(self):
        return list(self.tokens)

    def create_token(self, name, duration):
        token = {
            "id": "token-1",
            "name": name,
            "duration": duration,
            "expires_at": None if duration == "forever" else "2027-01-01T00:00:00Z",
            "client_id": "client.access",
            "client_secret": "secret-once",
            "enabled": True,
        }
        self.tokens.append(token)
        return token

    def delete_token(self, token_id):
        self.deleted_tokens.append(token_id)
        self.tokens = [item for item in self.tokens if item["id"] != token_id]

    def list_apps(self):
        return list(self.apps)

    def create_app(self, name, domain):
        app = {"id": "app-1", "name": name, "domain": domain}
        self.apps.append(app)
        return app

    def delete_app(self, app_id):
        self.deleted_apps.append(app_id)
        self.apps = [item for item in self.apps if item["id"] != app_id]

    def list_policies(self, app_id):
        return list(self.policies.get(app_id, []))

    def create_policy(self, app_id, name, token_id):
        if self.fail_policy:
            raise connect.ConnectError("policy denied")
        policy = {
            "id": "policy-1",
            "name": name,
            "include": [{"service_token": {"token_id": token_id}}],
        }
        self.policies.setdefault(app_id, []).append(policy)
        return policy

    def delete_policy(self, app_id, policy_id):
        self.deleted_policies.append((app_id, policy_id))
        self.policies[app_id] = [
            item for item in self.policies.get(app_id, []) if item["id"] != policy_id
        ]


def test_create_connection_makes_one_token_and_path_specific_policy():
    client = FakeClient()
    result = connect.create_connection(client, "Recipe agent", "90d", "https://brain.example.com")

    assert result["status"] == "CREATED"
    assert result["duration"] == "2160h"
    assert result["client_secret"] == "secret-once"
    assert client.apps[0]["domain"] == "brain.example.com/api/*"
    assert client.tokens[0]["name"] == "3rdBrain: Recipe agent"
    assert client.policies["app-1"][0]["include"] == [
        {"service_token": {"token_id": "token-1"}}
    ]


def test_create_rolls_back_token_and_new_app_when_policy_fails():
    client = FakeClient()
    client.fail_policy = True

    with pytest.raises(connect.ConnectError, match="policy denied"):
        connect.create_connection(client, "Broken", "30d", "https://brain.example.com")

    assert client.deleted_tokens == ["token-1"]
    assert client.deleted_apps == ["app-1"]


def test_list_hides_unrelated_cloudflare_tokens_and_supports_forever():
    client = FakeClient()
    client.tokens = [
        {"id": "other", "name": "CI deployment"},
        {"id": "mine", "name": "3rdBrain: Research agent", "duration": "forever"},
    ]

    assert connect.managed_connections(client) == [client.tokens[1]]
    assert connect.normalize_duration("no expiry") == "forever"


def test_revoke_removes_matching_policy_and_token_only():
    client = FakeClient()
    client.tokens = [
        {"id": "mine", "name": "3rdBrain: Research agent"},
        {"id": "other", "name": "CI deployment"},
    ]
    client.apps = [{"id": "app-1", "domain": "brain.example.com/api/*"}]
    client.policies = {
        "app-1": [
            {
                "id": "mine-policy",
                "name": "3rdBrain read-only: Research agent",
                "include": [{"service_token": {"token_id": "mine"}}],
            },
            {"id": "human-policy", "name": "Email access", "include": []},
        ]
    }

    result = connect.revoke_connection(client, "mine")

    assert result["status"] == "REVOKED"
    assert client.deleted_policies == [("app-1", "mine-policy")]
    assert client.deleted_tokens == ["mine"]
    assert client.tokens == [{"id": "other", "name": "CI deployment"}]
    assert client.policies["app-1"] == [
        {"id": "human-policy", "name": "Email access", "include": []}
    ]


def test_duplicate_connection_name_is_idempotently_rejected():
    client = FakeClient()
    client.tokens = [{"id": "mine", "name": "3rdBrain: Research agent"}]

    with pytest.raises(connect.ConnectError, match="already exists"):
        connect.create_connection(client, "Research agent", "90d", "https://brain.example.com")

    assert len(client.tokens) == 1


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body


def test_live_verification_requires_read_auth_anonymous_block_and_write_block(monkeypatch):
    def fake_urlopen(request, timeout):
        authenticated = request.has_header("Cf-access-client-id")
        if request.method == "GET" and authenticated:
            return FakeResponse(200, json.dumps({"read_only": True}).encode())
        status = 302 if request.method == "GET" else 405
        raise HTTPError(request.full_url, status, "blocked", {
            "Location": "https://team.cloudflareaccess.com/cdn-cgi/access/login/test"
        }, io.BytesIO(b""))

    monkeypatch.setattr(connect, "urlopen", fake_urlopen)
    result = connect.verify_connection("https://brain.example.com", "client", "secret")

    assert result["status"] == "VERIFIED"
    assert result["checks"] == {
        "authenticated_read": True,
        "anonymous_blocked": True,
        "write_blocked": True,
    }


def test_live_verification_rejects_a_successful_write(monkeypatch):
    def fake_urlopen(request, timeout):
        if request.method == "GET" and request.has_header("Cf-access-client-id"):
            return FakeResponse(200, json.dumps({"read_only": True}).encode())
        if request.method == "GET":
            raise HTTPError(request.full_url, 403, "blocked", {}, io.BytesIO(b""))
        return FakeResponse(200, b"{}")

    monkeypatch.setattr(connect, "urlopen", fake_urlopen)
    result = connect.verify_connection("https://brain.example.com", "client", "secret")

    assert result["status"] == "UNVERIFIED"
    assert result["checks"]["write_blocked"] is False


def test_public_create_returns_address_without_credentials_or_cloudflare_calls(monkeypatch, capsys):
    monkeypatch.setattr(connect, "probe_http", lambda *a, **k: (
        200, b'{"schema":1,"read_only":true}', ""))
    def forbidden(*args):
        pytest.fail("Public sites must never load Cloudflare credentials")
    monkeypatch.setattr(connect, "_client", forbidden)
    assert connect.main(["create", "--name", "Agent", "--site-url", "https://brain.example.com"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PUBLIC"
    assert result["key_required"] is False


@pytest.mark.parametrize("status,body,location", [
    (200, b"<html>Login</html>", ""),
    (404, b"", ""), (500, b"", ""),
    (302, b"", "https://other.example.com/login"),
    (302, b"", "https://cloudflareaccess.com.evil.example/cdn-cgi/access/login"),
])
def test_uncertain_site_never_triggers_access_changes(monkeypatch, status, body, location):
    monkeypatch.setattr(connect, "probe_http", lambda *a, **k: (status, body, location))
    assert connect.inspect_site("https://brain.example.com")["status"] == "UNVERIFIED"


def test_doctor_explains_missing_access_permissions_without_mutation(monkeypatch, tmp_path):
    monkeypatch.setattr(connect, "inspect_site", lambda *a: {"status": "PROTECTED"})
    class Denied(FakeClient):
        def list_apps(self):
            raise connect.ConnectError("HTTP 403")
    client = Denied()
    monkeypatch.setattr(connect, "_client", lambda *a: client)
    result = connect.doctor(tmp_path, site_url="https://brain.example.com")
    assert result["status"] == "SETUP_REQUIRED"
    assert "cloudflare-setup.md" in result["next_step"]
    assert not client.tokens and not client.apps


def test_read_permissions_do_not_claim_setup_ready(monkeypatch, tmp_path):
    monkeypatch.setattr(connect, "inspect_site", lambda *a: {"status": "PROTECTED"})
    monkeypatch.setattr(connect, "_client", lambda *a: FakeClient())
    result = connect.doctor(tmp_path, site_url="https://brain.example.com")
    assert result["status"] == "PREFLIGHT_OK"
    assert result["write_permissions_verified"] is False


def test_prepare_creates_verifies_revokes_and_never_returns_secret(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(connect, "inspect_site", lambda *a: {"status": "PROTECTED"})
    monkeypatch.setattr(connect, "verify_connection", lambda *a: {"status": "VERIFIED"})
    monkeypatch.setattr(connect, "probe_http", lambda *a, **k: (403, b"", ""))
    result = connect.prepare_connection(client, "https://brain.example.com")
    assert result["status"] == "READY"
    assert result["temporary_key_deleted"] and result["revoked_key_blocked"]
    assert not client.tokens and not client.policies["app-1"]
    assert "secret-once" not in json.dumps(result)
    assert len(client.apps) == 1  # protected application retained for future keys


def test_prepare_cleans_temporary_key_after_failed_network_test(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(connect, "inspect_site", lambda *a: {"status": "PROTECTED"})
    def failed(*args):
        raise connect.ConnectError("Network unavailable")
    monkeypatch.setattr(connect, "verify_connection", failed)
    with pytest.raises(connect.ConnectError, match="Network unavailable"):
        connect.prepare_connection(client, "https://brain.example.com")
    assert not client.tokens and not client.policies["app-1"]


def test_prepare_fails_if_revoked_key_still_reads(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(connect, "inspect_site", lambda *a: {"status": "PROTECTED"})
    monkeypatch.setattr(connect, "verify_connection", lambda *a: {"status": "VERIFIED"})
    monkeypatch.setattr(connect, "probe_http", lambda *a, **k: (200, b"{}", ""))
    result = connect.prepare_connection(client, "https://brain.example.com")
    assert result["status"] == "UNVERIFIED"
    assert result["revoked_key_blocked"] is False


def test_prepare_public_api_is_read_only_no_changes(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(connect, "inspect_site", lambda *a: {"status": "PUBLIC"})
    assert connect.prepare_connection(client, "https://brain.example.com")["status"] == "PUBLIC"
    assert not client.apps and not client.tokens


def test_prepare_requires_owner_authorization(monkeypatch, capsys):
    client = FakeClient()
    monkeypatch.setattr(connect, "doctor", lambda *a: {"status": "PREFLIGHT_OK"})
    monkeypatch.setattr(connect, "_client", lambda *a: client)
    assert connect.main(["prepare", "--site-url", "https://brain.example.com"]) == 2
    assert not client.apps and not client.tokens


def test_unrelated_api_application_is_preserved():
    client = FakeClient()
    client.apps = [{"id": "other", "domain": "brain.example.com/api/*", "name": "Other service"}]
    with pytest.raises(connect.ConnectError, match="independently managed"):
        connect.create_connection(client, "Agent", "90d", "https://brain.example.com")
    assert len(client.apps) == 1 and not client.tokens


@pytest.mark.parametrize("write_status", [200, 302, 404, 500, 503])
def test_errors_and_redirects_do_not_prove_writes_are_blocked(monkeypatch, write_status):
    def probe(url, method="GET", headers=None):
        if method != "GET":
            return write_status, b"", ""
        if headers:
            return 200, b'{"read_only":true}', ""
        return 403, b"", ""
    monkeypatch.setattr(connect, "probe_http", probe)
    assert connect.verify_connection("https://brain.example.com", "id", "secret")["status"] == "UNVERIFIED"


def test_redirect_handler_never_forwards_credentials():
    assert connect.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example.com") is None


@pytest.mark.parametrize("url", ["http://brain.example.com", "https://user:secret@brain.example.com", "https://brain.example.com/subpath"])
def test_credentials_require_supported_https_site_root(url):
    with pytest.raises(connect.ConnectError):
        connect.validate_site_url(url)


def test_cloudflare_lists_all_pages(monkeypatch):
    client = connect.CloudflareClient("unused", "account")
    calls = []
    def request(method, path):
        calls.append(path)
        return [{"id": str(i)} for i in range(100)] if "page=1&" in path else [{"id": "last"}]
    monkeypatch.setattr(client, "request", request)
    assert len(client.list_tokens()) == 101
    assert len(calls) == 2
