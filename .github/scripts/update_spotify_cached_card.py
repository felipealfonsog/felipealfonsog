#!/usr/bin/env python3
import hashlib
import os
import re
import time
import urllib.request

UID = "12133266428"

KITTINANX = (
    "https://spotify-github-profile.kittinanx.com/api/view"
    f"?uid={UID}"
    "&cover_image=true"
    "&theme=natemoo-re"
    "&show_offline=false"
    "&background_color=000000"
    "&interchange=false"
    "&bar_color=53b14f"
    "&bar_color_cover=true"
)

OUT_SVG = "images/spotify_now.svg"
README = "README.md"

RAW_SVG_BASE = (
    "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/master/images/spotify_now.svg"
)

MIN_BYTES = 3000  # anti-placeholder

def fetch(url: str, timeout: int = 25) -> tuple[str, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "github-actions-spotify-cachebust",
            "Accept": "image/*,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ct = (r.headers.get("Content-Type") or "").lower()
        data = r.read()
    return ct, data

def main():
    # Cache-bust upstream too
    url = f"{KITTINANX}&_={int(time.time())}"
    ct, data = fetch(url)

    if "image" not in ct:
        raise SystemExit(f"Not an image response (Content-Type={ct})")

    if len(data) < MIN_BYTES:
        raise SystemExit(f"Too small ({len(data)} bytes) — likely placeholder/error")

    # Must contain <svg (very strong sanity check)
    if b"<svg" not in data[:6000].lower():
        # Sometimes services return HTML error pages with 200 OK; block that.
        head = data[:200].decode("utf-8", "replace")
        raise SystemExit("Payload is not SVG. Head: " + head)

    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    with open(OUT_SVG, "wb") as f:
        f.write(data)

    # Hash for cache-bust
    h = hashlib.sha256(data).hexdigest()[:10]
    img_url = f"{RAW_SVG_BASE}?v={h}"

    # Rewrite only the Spotify block
    with open(README, "r", encoding="utf-8") as f:
        md = f.read()

    pattern = re.compile(r"<!-- SPOTIFY:START -->.*?<!-- SPOTIFY:END -->", re.S)
    if not pattern.search(md):
        raise SystemExit("Markers not found: <!-- SPOTIFY:START --> ... <!-- SPOTIFY:END -->")

    block = (
        "<!-- SPOTIFY:START -->\n"
        f"[![spotify-now]({img_url})](https://open.spotify.com/user/{UID})\n\n"
        "<sub>To view the latest track, click "
        "[refresh here](https://github.com/felipealfonsog?cache-bypass=1) "
        "to reload the profile with cache bypass (Although it's best to reload the profile by right-clicking on the page and selecting "
        "\"Reload\" or \"Refresh\").</sub>\n"
        "<!-- SPOTIFY:END -->"
    )

    md2 = pattern.sub(block, md)

    with open(README, "w", encoding="utf-8") as f:
        f.write(md2)

if __name__ == "__main__":
    main()
