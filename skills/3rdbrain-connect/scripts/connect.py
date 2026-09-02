"""Manage individual read-only Cloudflare Access connections for 3rdBrain."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


API_ROOT = "https://api.cloudflare.com/client/v4"
TOKEN_PREFIX = "3rdBrain: "
APP_PREFIX = "3rdBrain read-only API: "
POLICY_PREFIX = "3rdBrain read-only: "


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


# Never forward a secret to a redirect destination or mistake a login page for the API.
urlopen = build_opener(NoRedirect()).open


class ConnectError(RuntimeError):
    """A safe, user-facing connection error."""


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        values[key] = value.strip().strip('"').strip("'")
    return values


def configuration(base: Path, env_file: Path | None = None) -> tuple[str, str]:
    values = _parse_env_file(env_file or base / "_site" / ".env")
    values.update({key: value for key, value in os.environ.items() if value})
    token = values.get("THIRDBRAIN_CONNECT_API_TOKEN") or values.get("CLOUDFLARE_API_TOKEN")
    account_id = values.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account_id:
        raise ConnectError(
            "Missing Cloudflare connection management credentials. Set "
            "THIRDBRAIN_CONNECT_API_TOKEN and CLOUDFLARE_ACCOUNT_ID in _site/.env."
        )
    return token, account_id


def site_url_from_base(base: Path) -> str:
    config = base / "_site" / "mkdocs.yml"
    if not config.exists():
        raise ConnectError(f"No _site/mkdocs.yml found under {base}")
    match = re.search(r"^site_url:\s*([^#\r\n]+)", config.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise ConnectError("The published site address is missing from _site/mkdocs.yml")
    return match.group(1).strip().strip('"').strip("'").rstrip("/")


def api_domain(site_url: str) -> str:
    parsed = urlparse(validate_site_url(site_url))
    return f"{parsed.hostname}/api/*"


def validate_site_url(site_url: str) -> str:
    parsed = urlparse(site_url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.port not in {None, 443} or parsed.path not in {"", "/"}
            or parsed.query or parsed.fragment or parsed.hostname in {"localhost", "127.0.0.1"}):
        raise ConnectError("Use the published HTTPS site root, without credentials, a path, or query.")
    return site_url.rstrip("/")


def site_hostname(site_url: str) -> str:
    parsed = urlparse(site_url if "://" in site_url else f"https://{site_url}")
    if not parsed.hostname:
        raise ConnectError(f"Invalid published site address: {site_url}")
    return parsed.hostname


def normalize_duration(value: str) -> str:
    cleaned = value.strip().lower().replace(" ", "")
    aliases = {
        "30d": "720h",
        "90d": "2160h",
        "1y": "8760h",
        "365d": "8760h",
        "none": "forever",
        "never": "forever",
        "noexpiry": "forever",
    }
    cleaned = aliases.get(cleaned, cleaned)
    if cleaned == "forever" or re.fullmatch(r"\d+(?:ns|us|µs|ms|s|m|h)", cleaned):
        return cleaned
    raise ConnectError("Expiry must be 30d, 90d, 1y, forever, or a Cloudflare duration such as 48h")


class CloudflareClient:
    def __init__(self, token: str, account_id: str):
        self.token = token
        self.account_id = account_id

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{API_ROOT}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "3rdBrain-Connect/1",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8") or "{}")
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(detail)
                messages = [item.get("message", "") for item in parsed.get("errors", [])]
                detail = "; ".join(filter(None, messages)) or f"HTTP {error.code}"
            except json.JSONDecodeError:
                detail = f"HTTP {error.code}"
            operation = path.split("/access/", 1)[-1].split("?", 1)[0]
            raise ConnectError(f"Cloudflare rejected {method} access/{operation}: {detail}") from error
        except URLError as error:
            raise ConnectError(f"Could not reach Cloudflare: {error.reason}") from error
        if not body.get("success", False):
            messages = [item.get("message", "") for item in body.get("errors", [])]
            raise ConnectError("Cloudflare rejected the request: " + "; ".join(filter(None, messages)))
        return body.get("result")

    def _list(self, path: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for page in range(1, 1001):
            result = self.request("GET", f"{path}?{urlencode({'page': page, 'per_page': 100})}")
            if not isinstance(result, list):
                raise ConnectError("Cloudflare returned an unexpected list response")
            items.extend(result)
            if len(result) < 100:
                return items
        raise ConnectError("Cloudflare pagination exceeded its safety limit")

    def list_tokens(self) -> list[dict[str, Any]]:
        return self._list(f"/accounts/{self.account_id}/access/service_tokens")

    def create_token(self, name: str, duration: str) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/accounts/{self.account_id}/access/service_tokens",
            {"name": name, "duration": duration, "enabled": True},
        )

    def delete_token(self, token_id: str) -> None:
        self.request("DELETE", f"/accounts/{self.account_id}/access/service_tokens/{token_id}")

    def list_apps(self) -> list[dict[str, Any]]:
        return self._list(f"/accounts/{self.account_id}/access/apps")

    def create_app(self, name: str, domain: str) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/accounts/{self.account_id}/access/apps",
            {
                "name": name,
                "domain": domain,
                "type": "self_hosted",
                "session_duration": "24h",
                "app_launcher_visible": False,
                "service_auth_401_redirect": True,
            },
        )

    def delete_app(self, app_id: str) -> None:
        self.request("DELETE", f"/accounts/{self.account_id}/access/apps/{app_id}")

    def list_policies(self, app_id: str) -> list[dict[str, Any]]:
        return self._list(f"/accounts/{self.account_id}/access/apps/{app_id}/policies")

    def create_policy(self, app_id: str, name: str, token_id: str) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/accounts/{self.account_id}/access/apps/{app_id}/policies",
            {
                "name": name,
                "decision": "non_identity",
                "include": [{"service_token": {"token_id": token_id}}],
            },
        )

    def delete_policy(self, app_id: str, policy_id: str) -> None:
        self.request("DELETE", f"/accounts/{self.account_id}/access/apps/{app_id}/policies/{policy_id}")


def _app_domain(app: dict[str, Any]) -> str:
    if isinstance(app.get("domain"), str):
        return app["domain"].rstrip("/")
    for destination in app.get("destinations") or []:
        if destination.get("type") == "public" and destination.get("uri"):
            return str(destination["uri"]).rstrip("/")
    return ""


def managed_connections(client: CloudflareClient) -> list[dict[str, Any]]:
    return sorted(
        [item for item in client.list_tokens() if str(item.get("name", "")).startswith(TOKEN_PREFIX)],
        key=lambda item: (str(item.get("name", "")).lower(), str(item.get("id", ""))),
    )


def create_connection(
    client: CloudflareClient,
    name: str,
    duration: str,
    site_url: str,
) -> dict[str, Any]:
    label = name.strip()
    if not label or len(label) > 96:
        raise ConnectError("Connection name must contain 1 to 96 characters")
    token_name = f"{TOKEN_PREFIX}{label}"
    if any(item.get("name") == token_name for item in managed_connections(client)):
        raise ConnectError(f"A 3rdBrain connection named {label!r} already exists")

    duration = normalize_duration(duration)
    domain = api_domain(site_url)
    app = next((item for item in client.list_apps() if _app_domain(item) == domain), None)
    created_app = False
    if app is None:
        app = client.create_app(f"{APP_PREFIX}{site_hostname(site_url)}", domain)
        created_app = True
    elif app.get("name") != f"{APP_PREFIX}{site_hostname(site_url)}":
        raise ConnectError("The API path already has an independently managed Access application. Review it before changing access.")

    token: dict[str, Any] | None = None
    try:
        token = client.create_token(token_name, duration)
        policy = client.create_policy(str(app["id"]), f"{POLICY_PREFIX}{label}", str(token["id"]))
    except Exception as error:
        cleanup_errors = []
        if token and token.get("id"):
            try:
                client.delete_token(str(token["id"]))
            except ConnectError:
                cleanup_errors.append(f"temporary token {token['id']} could not be removed")
        if created_app and app.get("id"):
            try:
                client.delete_app(str(app["id"]))
            except ConnectError:
                cleanup_errors.append(f"new API application {app['id']} could not be removed")
        if cleanup_errors:
            raise ConnectError(f"{error}. Cleanup required: {'; '.join(cleanup_errors)}") from error
        raise

    return {
        "status": "CREATED",
        "name": label,
        "token_id": token.get("id"),
        "expires_at": token.get("expires_at"),
        "duration": token.get("duration", duration),
        "site_url": site_url.rstrip("/"),
        "api_manifest": f"{site_url.rstrip('/')}/api/v1/manifest.json",
        "client_id": token.get("client_id"),
        "client_secret": token.get("client_secret"),
        "headers": {
            "CF-Access-Client-Id": token.get("client_id"),
            "CF-Access-Client-Secret": token.get("client_secret"),
        },
        "policy_id": policy.get("id"),
        "secret_notice": "Save this connection bundle now. Cloudflare will not show this secret again.",
    }


def _policy_uses_token(policy: dict[str, Any], token_id: str) -> bool:
    for rule in policy.get("include") or []:
        if (rule.get("service_token") or {}).get("token_id") == token_id:
            return True
    return False


def revoke_connection(client: CloudflareClient, token_id: str) -> dict[str, Any]:
    token = next((item for item in managed_connections(client) if str(item.get("id")) == token_id), None)
    if token is None:
        raise ConnectError("No managed 3rdBrain connection has that ID")

    warnings: list[str] = []
    for app in client.list_apps():
        app_id = str(app.get("id", ""))
        if not app_id:
            continue
        try:
            policies = client.list_policies(app_id)
        except ConnectError as error:
            warnings.append(str(error))
            continue
        for policy in policies:
            if not str(policy.get("name", "")).startswith(POLICY_PREFIX):
                continue
            if not _policy_uses_token(policy, token_id):
                continue
            try:
                client.delete_policy(app_id, str(policy["id"]))
            except ConnectError as error:
                warnings.append(str(error))

    client.delete_token(token_id)
    return {
        "status": "REVOKED",
        "name": str(token.get("name", "")).removeprefix(TOKEN_PREFIX),
        "token_id": token_id,
        "warnings": warnings,
    }


def probe_http(url: str, method: str = "GET", headers: dict[str, str] | None = None) -> tuple[int, bytes, str]:
    request = Request(url, method=method, headers=headers or {})
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read(), ""
    except HTTPError as error:
        return error.code, error.read(), (error.headers or {}).get("Location", "")
    except (URLError, TimeoutError) as error:
        raise ConnectError("Could not reach the published 3rdBrain. Retry when the network is available.") from error


def access_blocked(status: int, location: str) -> bool:
    if status in {401, 403}:
        return True
    target = urlparse(location)
    return (status in {301, 302, 303, 307, 308}
            and target.scheme == "https"
            and (target.hostname or "").endswith(".cloudflareaccess.com")
            and target.path.startswith("/cdn-cgi/access/"))


def inspect_site(site_url: str) -> dict[str, Any]:
    site_url = validate_site_url(site_url)
    manifest_url = f"{site_url}/api/v1/manifest.json"
    status, body, location = probe_http(manifest_url)
    try:
        manifest = json.loads(body) if status == 200 else {}
    except (ValueError, UnicodeDecodeError):
        manifest = {}
    if isinstance(manifest, dict) and manifest.get("read_only") is True and manifest.get("schema") == 1:
        return {"status": "PUBLIC", "api_manifest": manifest_url, "key_required": False,
                "instructions": "Read the manifest, then its records and page endpoints. No authentication headers are needed."}
    if access_blocked(status, location):
        return {"status": "PROTECTED", "api_manifest": manifest_url, "http_status": status}
    return {"status": "UNVERIFIED", "http_status": status,
            "reason": "No public 3rdBrain API or recognized access gate was found. Check publishing before creating a key."}


def doctor(base: Path, env_file: Path | None = None, site_url: str | None = None) -> dict[str, Any]:
    result = inspect_site(site_url or site_url_from_base(base))
    if result["status"] != "PROTECTED":
        return result
    try:
        client = _client(base, env_file)
        client.list_apps()
        client.list_tokens()
    except ConnectError as error:
        return {**result, "status": "SETUP_REQUIRED", "reason": str(error),
                "next_step": "Complete references/cloudflare-setup.md: authorize Access: Apps and Policies Edit and Access: Service Tokens Edit for this account, then retry. Never share the management token with an agent receiving read access."}
    return {**result, "status": "PREFLIGHT_OK", "write_permissions_verified": False,
            "next_step": "Read checks passed. The authorized temporary-key trial must pass before reporting Connect ready."}


def verify_connection(site_url: str, client_id: str, client_secret: str) -> dict[str, Any]:
    site_url = validate_site_url(site_url)
    manifest_url = f"{site_url.rstrip('/')}/api/v1/manifest.json"
    headers = {
        "CF-Access-Client-Id": client_id,
        "CF-Access-Client-Secret": client_secret,
        "User-Agent": "3rdBrain-Connect/1",
    }

    auth_status, body, _ = probe_http(manifest_url, headers=headers)
    try:
        manifest = json.loads(body.decode("utf-8")) if auth_status == 200 else {}
    except json.JSONDecodeError:
        manifest = {}
    anonymous_status, _, location = probe_http(manifest_url)
    writes = {method: probe_http(manifest_url, method, headers)[0]
              for method in ("POST", "PUT", "PATCH", "DELETE")}
    checks = {
        "authenticated_read": auth_status == 200 and isinstance(manifest, dict) and manifest.get("read_only") is True,
        "anonymous_blocked": access_blocked(anonymous_status, location),
        "write_blocked": all(status in {401, 403, 405} for status in writes.values()),
    }
    return {
        "status": "VERIFIED" if all(checks.values()) else "UNVERIFIED",
        "checks": checks,
        "http": {
            "authenticated_get": auth_status,
            "anonymous_get": anonymous_status,
            "authenticated_writes": writes,
        },
    }


def prepare_connection(client: CloudflareClient, site_url: str) -> dict[str, Any]:
    """An explicitly authorized, secret-free create/verify/revoke setup trial."""
    mode = inspect_site(site_url)
    if mode["status"] == "PUBLIC":
        return mode
    if mode["status"] != "PROTECTED":
        raise ConnectError(mode["reason"])
    bundle = create_connection(client, f"Setup trial {uuid.uuid4().hex[:12]}", "1h", site_url)
    try:
        verification = verify_connection(site_url, bundle["client_id"], bundle["client_secret"])
    finally:
        # Always remove the temporary key, including when a live probe fails.
        try:
            cleanup = revoke_connection(client, bundle["token_id"])
        except ConnectError as error:
            raise ConnectError(f"Trial cleanup required for token {bundle['token_id']}: {error}") from error
    status, _, location = probe_http(bundle["api_manifest"], headers=bundle["headers"])
    revoked = access_blocked(status, location)
    absent = all(item.get("id") != bundle["token_id"] for item in client.list_tokens())
    ready = verification["status"] == "VERIFIED" and revoked and absent and not cleanup["warnings"]
    return {"status": "READY" if ready else "UNVERIFIED", "verification": verification,
            "temporary_key_deleted": absent, "revoked_key_blocked": revoked,
            "api_manifest": bundle["api_manifest"], "cleanup_warnings": cleanup["warnings"]}


def _client(base: Path, env_file: Path | None) -> CloudflareClient:
    token, account_id = configuration(base, env_file)
    return CloudflareClient(token, account_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--base", type=Path, default=Path.cwd())
        subparser.add_argument("--env-file", type=Path)

    create = subparsers.add_parser("create")
    add_common(create)
    create.add_argument("--name", required=True)
    create.add_argument("--duration", default="90d")
    create.add_argument("--site-url")
    create.add_argument("--skip-verify", action="store_true")

    for command in ("doctor", "prepare"):
        subparser = subparsers.add_parser(command)
        add_common(subparser)
        subparser.add_argument("--site-url")
        if command == "prepare":
            subparser.add_argument("--confirm", action="store_true")

    listing = subparsers.add_parser("list")
    add_common(listing)

    revoke = subparsers.add_parser("revoke")
    add_common(revoke)
    revoke.add_argument("--token-id", required=True)
    revoke.add_argument("--confirm", action="store_true")

    args = parser.parse_args(argv)
    base = args.base.resolve()
    try:
        if args.command in {"doctor", "prepare", "create"}:
            site_url = args.site_url or site_url_from_base(base)
            preflight = doctor(base, args.env_file, site_url)
            if args.command == "doctor" or preflight["status"] != "PREFLIGHT_OK":
                print(json.dumps(preflight, indent=2))
                return 0 if preflight["status"] in {"PUBLIC", "PREFLIGHT_OK"} else 2
        client = _client(base, args.env_file)
        if args.command == "prepare":
            if not args.confirm:
                raise ConnectError("Setup trial requires --confirm after owner authorization")
            result = prepare_connection(client, site_url)
        elif args.command == "list":
            result: Any = managed_connections(client)
        elif args.command == "create":
            site_url = args.site_url or site_url_from_base(base)
            result = create_connection(client, args.name, args.duration, site_url)
            if not args.skip_verify:
                try:
                    result["verification"] = verify_connection(
                        site_url, str(result["client_id"]), str(result["client_secret"])
                    )
                except ConnectError as error:
                    result["verification"] = {"status": "UNVERIFIED", "error": str(error)}
                if result["verification"]["status"] != "VERIFIED":
                    result["status"] = "CREATED_UNVERIFIED"
        else:
            if not args.confirm:
                raise ConnectError("Revocation requires --confirm after the user confirms the exact connection")
            result = revoke_connection(client, args.token_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2 if isinstance(result, dict) and result.get("status") in {"UNVERIFIED", "CREATED_UNVERIFIED"} else 0
    except ConnectError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        if "403" in str(error) or "Cloudflare rejected" in str(error):
            print("Stop and follow references/cloudflare-setup.md to check the selected account and Access-management permissions. Do not retry mutations until authorized.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
