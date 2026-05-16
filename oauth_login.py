"""Run the local Oura OAuth callback harness."""

from __future__ import annotations

import argparse

from oura_project.auth import OuraAuthError, login, refresh_saved_token


def main() -> int:
    parser = argparse.ArgumentParser(description="Authenticate OuraProject with Oura OAuth.")
    parser.add_argument("--no-browser", action="store_true", help="Print the authorization URL instead of opening it.")
    parser.add_argument("--refresh", action="store_true", help="Refresh the saved token instead of starting login.")
    args = parser.parse_args()

    try:
        path = refresh_saved_token() if args.refresh else login(open_browser=not args.no_browser)
    except OuraAuthError as exc:
        print(f"OAuth failed: {exc}")
        return 1
    print(f"Oura token saved to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
