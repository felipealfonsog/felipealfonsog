#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

ENDPOINT = (
    "https://spotify-github-profile.kittinanx.com/api/view"
    "?uid=12133266428"
    "&cover_image=true"
    "&theme=natemoo-re"
    "&show_offline=false"
    "&background_color=000000"
    "&interchange=false"
    "&bar_color=53b14f"
    "&bar_color_cover=true"
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images" / "spotify-live.svg"
BLANK = ROOT / "images" / "blank.svg"

TIMEOUT_SECONDS = 6


def fetch(url: str) -> tuple[int, str, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "felipe-spotify-healthcheck/1.0",
            "Accept": "image/svg+xml,image/*;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        status = getattr(resp, "status", 200)
        ctype = resp.headers.get("Content-Type", "") or ""
        data = resp.read()
        return status, ctype, data


def looks_like_svg(data: bytes) -> bool:
    # ultra simple heuristics (enough to detect obvious HTML error pages)
    head = data[:400].lstrip()
    if b"<svg" in head or head.startswith(b"<?xml"):
        return True
    return False


def write_blank() -> None:
    OUT.write_bytes(BLANK.read_bytes())


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    try:
        status, ctype, data = fetch(ENDPOINT)

        # must be HTTP 200 + looks like SVG (avoid saving HTML error pages)
        if status != 200 or not looks_like_svg(data):
            write_blank()
            return 0

        # If it’s SVG, write it out
        OUT.write_bytes(data)
        return 0

    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        # Any failure → blank
        write_blank()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
