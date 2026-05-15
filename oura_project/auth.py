"""Authentication helpers for local Oura API access."""

from __future__ import annotations

import os
from dataclasses import dataclass


TOKEN_ENV = "OURA_ACCESS_TOKEN"


@dataclass(frozen=True)
class AuthStatus:
    """Small status object for the dashboard and CLI checks."""

    configured: bool
    source: str | None = None
    message: str = ""


def get_access_token() -> str | None:
    """Return the configured Oura Personal Access Token, if present."""

    token = os.getenv(TOKEN_ENV, "").strip()
    return token or None


def auth_status() -> AuthStatus:
    """Return a non-secret auth status for UI and docs checks."""

    if get_access_token():
        return AuthStatus(
            configured=True,
            source=f"environment variable {TOKEN_ENV}",
            message="Oura access token is configured.",
        )
    return AuthStatus(
        configured=False,
        source=None,
        message=f"Set {TOKEN_ENV} to use live Oura API data.",
    )
