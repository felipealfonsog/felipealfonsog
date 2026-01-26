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

OUT_PATH = "images/spotify_now.png"

MIN_BYTES = 8_000  # umbral anti-respuesta vacía/errónea (ajustable)

def http_get(url: str, timeout: int = 25) -> bytes:
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
    # cache-bust para forzar refresh real
    url = f"{KITTINANX_URL}&_={int(time.time())}"

    ct, data = http_get(url)

    # Validaciones duras: si no es imagen, o es demasiado chico, aborta
    if "image" not in ct:
        raise SystemExit(f"Not an image response (Content-Type={ct})")

    if len(data) < MIN_BYTES:
        raise SystemExit(f"Image too small ({len(data)} bytes) — likely error/placeholder")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(data)

if __name__ == "__main__":
    main()
