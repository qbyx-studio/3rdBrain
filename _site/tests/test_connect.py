import importlib.util
import io
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "3rdbrain-connect" / "scripts" / "connect.py"
SPEC = importlib.util.spec_from_file_location("thirdbrain_connect", SCRIPT)
connect = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(connect)


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
        raise HTTPError(request.full_url, status, "blocked", {}, io.BytesIO(b""))

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
