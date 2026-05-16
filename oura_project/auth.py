"""OAuth helpers for local Oura API access."""

from __future__ import annotations

import json
import os
import secrets
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
CLIENT_ID_ENV = "OURA_CLIENT_ID"
CLIENT_SECRET_ENV = "OURA_CLIENT_SECRET"
REDIRECT_URI_ENV = "OURA_REDIRECT_URI"
SCOPES_ENV = "OURA_SCOPES"
TOKEN_FILE_ENV = "OURA_TOKEN_FILE"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/callback"
DEFAULT_SCOPES = "personal daily heartrate spo2Daily"
DEFAULT_TOKEN_FILE = ".oura-token.json"
EXPIRY_SKEW_SECONDS = 60


class OuraAuthError(RuntimeError):
    """Raised when the local OAuth flow cannot complete."""


@dataclass(frozen=True)
class OAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str = DEFAULT_REDIRECT_URI
    scopes: str = DEFAULT_SCOPES
    token_file: Path = Path(DEFAULT_TOKEN_FILE)

    @classmethod
    def from_env(cls) -> "OAuthConfig":
        client_id = os.getenv(CLIENT_ID_ENV, "").strip()
        client_secret = os.getenv(CLIENT_SECRET_ENV, "").strip()
        if not client_id or not client_secret:
            raise OuraAuthError(f"Set {CLIENT_ID_ENV} and {CLIENT_SECRET_ENV} before starting OAuth.")
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=os.getenv(REDIRECT_URI_ENV, DEFAULT_REDIRECT_URI).strip(),
            scopes=os.getenv(SCOPES_ENV, DEFAULT_SCOPES).strip(),
            token_file=Path(os.getenv(TOKEN_FILE_ENV, DEFAULT_TOKEN_FILE).strip()),
        )


@dataclass(frozen=True)
class AuthStatus:
    configured: bool
    source: str | None = None
    message: str = ""


def load_token(token_file: str | Path | None = None) -> dict[str, Any] | None:
    path = Path(token_file or os.getenv(TOKEN_FILE_ENV, DEFAULT_TOKEN_FILE))
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_token(token: dict[str, Any], token_file: str | Path | None = None) -> Path:
    path = Path(token_file or os.getenv(TOKEN_FILE_ENV, DEFAULT_TOKEN_FILE))
    token = dict(token)
    if "expires_in" in token:
        token["expires_at"] = int(time.time()) + int(token["expires_in"])
    path.write_text(json.dumps(token, indent=2, sort_keys=True))
    path.chmod(0o600)
    return path


def token_expired(token: dict[str, Any] | None) -> bool:
    if not token or not token.get("access_token"):
        return True
    expires_at = token.get("expires_at")
    if not expires_at:
        return False
    return int(expires_at) <= int(time.time()) + EXPIRY_SKEW_SECONDS


def auth_status(token_file: str | Path | None = None) -> AuthStatus:
    token = load_token(token_file)
    source = str(token_file or os.getenv(TOKEN_FILE_ENV, DEFAULT_TOKEN_FILE))
    if token and token.get("access_token"):
        if token_expired(token):
            return AuthStatus(False, source, "Oura token exists but is expired.")
        return AuthStatus(True, source, "Oura OAuth token is configured.")
    return AuthStatus(False, None, "Run the OAuth login harness to create an Oura token.")


def get_access_token(token_file: str | Path | None = None) -> str | None:
    token = load_token(token_file)
    if token_expired(token):
        return None
    return str(token.get("access_token")) if token else None


def authorization_url(config: OAuthConfig, state: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "scope": config.scopes,
            "state": state,
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


def post_token(payload: bytes) -> dict[str, Any]:
    request = Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def exchange_code(config: OAuthConfig, code: str) -> dict[str, Any]:
    payload = urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.redirect_uri,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        }
    ).encode()
    return post_token(payload)


def refresh_token(config: OAuthConfig, refresh_token_value: str) -> dict[str, Any]:
    payload = urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_value,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        }
    ).encode()
    return post_token(payload)


def run_local_callback(config: OAuthConfig, state: str) -> str:
    parsed = urlparse(config.redirect_uri)
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise OuraAuthError("Local OAuth harness requires a localhost redirect URI.")
    if parsed.scheme != "http":
        raise OuraAuthError("Local OAuth harness expects an http localhost redirect URI.")

    result: dict[str, str] = {}
    expected_path = parsed.path or "/"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            query = parse_qs(urlparse(self.path).query)
            if urlparse(self.path).path != expected_path:
                self.send_response(404)
                self.end_headers()
                return
            if query.get("state", [""])[0] != state:
                result["error"] = "state_mismatch"
            elif "error" in query:
                result["error"] = query["error"][0]
            elif "code" in query:
                result["code"] = query["code"][0]
            else:
                result["error"] = "missing_code"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Oura authorization received.</h1>You can close this tab.</body></html>")

        def log_message(self, format: str, *args: object) -> None:
            return

    server = HTTPServer((parsed.hostname or "127.0.0.1", parsed.port or 8765), Handler)
    server.handle_request()
    if result.get("error"):
        raise OuraAuthError(f"OAuth callback failed: {result['error']}")
    if not result.get("code"):
        raise OuraAuthError("OAuth callback did not include an authorization code.")
    return result["code"]


def login(open_browser: bool = True) -> Path:
    config = OAuthConfig.from_env()
    state = secrets.token_urlsafe(24)
    url = authorization_url(config, state)
    if open_browser:
        webbrowser.open(url)
    else:
        print(url)
    code = run_local_callback(config, state)
    token = exchange_code(config, code)
    return save_token(token, config.token_file)


def refresh_saved_token() -> Path:
    config = OAuthConfig.from_env()
    current = load_token(config.token_file)
    if not current or not current.get("refresh_token"):
        raise OuraAuthError("No refresh token found. Run OAuth login first.")
    token = refresh_token(config, str(current["refresh_token"]))
    return save_token(token, config.token_file)
