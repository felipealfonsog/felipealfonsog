#!/usr/bin/env python3

import os
import time
import urllib.request


# ─────────────────────────────────────────────────────────────
# PRIMARY — configuración original
# ─────────────────────────────────────────────────────────────

PRIMARY_URL = (
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


# ─────────────────────────────────────────────────────────────
# FALLBACK — nueva configuración
# ─────────────────────────────────────────────────────────────

FALLBACK_URL = (
    "https://spotify-github-profile.kittinanx.com/api/view"
    "?uid=12133266428"
    "&cover_image=true"
    "&theme=natemoo-re"
    "&show_offline=true"
    "&background_color=121212"
    "&interchange=true"
    "&profanity=true"
    "&hide_remaster=true"
    "&bar_color=53b14f"
    "&bar_color_cover=true"
)


OUT_PATH = "images/spotify_now.svg"
MIN_BYTES = 4_000


def http_get(url: str, timeout: int = 25):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "github-actions-spotify-card-cache",
            "Accept": "image/svg+xml,image/*,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    with urllib.request.urlopen(req, timeout=timeout) as r:
        content_type = (r.headers.get("Content-Type") or "").lower()
        data = r.read()

    return content_type, data


def fetch_and_validate(base_url: str, name: str):
    # Cache bust
    url = f"{base_url}&_={int(time.time())}"

    print(f"Trying Spotify source: {name}")

    content_type, data = http_get(url)

    # Validar Content-Type
    if "image" not in content_type and "svg" not in content_type:
        raise RuntimeError(
            f"{name}: invalid Content-Type "
            f"({content_type or 'unknown'})"
        )

    # Detectar respuestas demasiado pequeñas / placeholders
    if len(data) < MIN_BYTES:
        raise RuntimeError(
            f"{name}: image too small "
            f"({len(data)} bytes)"
        )

    # Validar que realmente sea SVG
    if b"<svg" not in data[:5000].lower():
        raise RuntimeError(
            f"{name}: response does not contain a valid SVG"
        )

    print(
        f"{name}: OK "
        f"({len(data)} bytes, Content-Type={content_type})"
    )

    return data


def main():
    data = None

    # ── 1. Intentar fuente original ──────────────────────────
    try:
        data = fetch_and_validate(
            PRIMARY_URL,
            "PRIMARY"
        )

    except Exception as primary_error:
        print(f"PRIMARY failed: {primary_error}")
        print("Switching to FALLBACK...")

        # ── 2. Si falla, intentar nueva configuración ────────
        try:
            data = fetch_and_validate(
                FALLBACK_URL,
                "FALLBACK"
            )

        except Exception as fallback_error:
            print(f"FALLBACK failed: {fallback_error}")

            raise SystemExit(
                "Both Spotify sources failed. "
                "Existing cached SVG will be preserved."
            )

    # ── 3. Guardar solamente si obtuvimos un SVG válido ─────

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    # Escritura temporal para evitar dejar un SVG corrupto
    # si el proceso se interrumpe mientras escribe.
    temp_path = OUT_PATH + ".tmp"

    with open(temp_path, "wb") as f:
        f.write(data)

    os.replace(temp_path, OUT_PATH)

    print(f"Spotify profile successfully updated: {OUT_PATH}")


if __name__ == "__main__":
    main()
