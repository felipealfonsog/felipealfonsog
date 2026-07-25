#!/usr/bin/env python3

import json
import os
import re
from pathlib import Path


CALLBACK_FILE = Path("spotify-callback.html")
CLIENT_ID = os.environ.get("SPOTIFY_PUBLIC_CLIENT_ID", "").strip()

CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
ASSIGNMENT_PATTERN = re.compile(
    r'const SPOTIFY_CLIENT_ID = ".*?"; '
    r"// managed-by-update-spotify-callback"
)


def main():
    if not CLIENT_ID:
        raise RuntimeError("The workflow input spotify_client_id is required.")
    if not CLIENT_ID_PATTERN.fullmatch(CLIENT_ID):
        raise RuntimeError(
            "Invalid Spotify Client ID format. "
            "Expected 16-128 letters, numbers, underscores, or hyphens."
        )
    if not CALLBACK_FILE.is_file():
        raise RuntimeError(f"File not found: {CALLBACK_FILE}")

    html = CALLBACK_FILE.read_text(encoding="utf-8")
    replacement = (
        f"const SPOTIFY_CLIENT_ID = {json.dumps(CLIENT_ID)}; "
        "// managed-by-update-spotify-callback"
    )
    updated, replacements = ASSIGNMENT_PATTERN.subn(
        replacement,
        html,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError(
            "Managed SPOTIFY_CLIENT_ID assignment was not found exactly once."
        )

    if updated == html:
        print("Spotify callback Client ID already configured.")
        return

    CALLBACK_FILE.write_text(updated, encoding="utf-8")
    print("Spotify callback Client ID updated.")


if __name__ == "__main__":
    main()
