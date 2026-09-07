#!/usr/bin/env python3
import os
import time
import urllib.request

KITTINANX_URL = (
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

OUT_PATH = "images/spotify_now.svg"
MIN_BYTES = 4_000  # SVG suele ser más chico que PNG; no lo pongas muy alto

def http_get(url: str, timeout: int = 25):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "github-actions-spotify-card-cache",
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
    url = f"{KITTINANX_URL}&_={int(time.time())}"  # cache-bust real

    ct, data = http_get(url)

    if "image" not in ct:
        raise SystemExit(f"Not an image response (Content-Type={ct})")

    if len(data) < MIN_BYTES:
        raise SystemExit(f"Image too small ({len(data)} bytes) — likely error/placeholder")

    # Validación extra: si es SVG, debería traer <svg
    if "svg" in ct and b"<svg" not in data[:5000]:
        raise SystemExit("Content-Type says SVG but no <svg> tag found")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(data)

if __name__ == "__main__":
    main()
