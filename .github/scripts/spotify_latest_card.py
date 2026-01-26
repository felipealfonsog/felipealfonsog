#!/usr/bin/env python3
import base64
import json
import os
import sys
import time
import hashlib
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

OUT = "images/spotify_now.svg"

AUTH_URL = "https://accounts.spotify.com/api/token"
CURRENT_URL = "https://api.spotify.com/v1/me/player/currently-playing"
RECENT_URL = "https://api.spotify.com/v1/me/player/recently-played?limit=1"


def esc_xml(s: str) -> str:
    # critical: avoid XML parse errors (unescaped & etc.)
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace").strip()
        payload = json.loads(raw) if raw else {}
        return r.getcode(), dict(r.headers), payload


def get_access_token() -> str:
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise RuntimeError("Missing Spotify secrets (SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIFY_REFRESH_TOKEN).")

    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }).encode("utf-8")

    code, _, payload = http_json(
        AUTH_URL,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=body,
        timeout=25,
    )

    if code >= 400:
        raise RuntimeError(f"Token refresh failed: {payload}")

    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in response: {payload}")

    return token


def get_currently_playing(access_token: str):
    req = urllib.request.Request(CURRENT_URL, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 204:
                return None  # idle
            raw = r.read().decode("utf-8", "replace").strip()
            if not raw:
                return None
            data = json.loads(raw)
            if not data.get("item"):
                return None
            item = data["item"]
            artists = item.get("artists") or []
            artist = ", ".join([a.get("name", "") for a in artists if a.get("name")]) or "Unknown artist"
            title = item.get("name") or "Unknown track"
            album = item.get("album") or {}
            imgs = album.get("images") or []
            cover = imgs[1]["url"] if len(imgs) > 1 else (imgs[0]["url"] if imgs else "")
            track_id = item.get("id") or ""
            return {
                "mode": "PLAYING" if data.get("is_playing") else "IDLE",
                "artist": artist,
                "title": title,
                "cover": cover,
                "track_id": track_id,
            }
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return None
        # if playback-state scope is missing/blocked, we still can fall back to recent
        return None
    except Exception:
        return None


def get_recently_played(access_token: str):
    code, _, payload = http_json(RECENT_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=25)
    if code >= 400:
        raise RuntimeError(f"Spotify recently-played failed: {payload}")

    items = payload.get("items") or []
    if not items:
        return None

    it = items[0]
    track = it.get("track") or {}
    artists = track.get("artists") or []
    artist = ", ".join([a.get("name", "") for a in artists if a.get("name")]) or "Unknown artist"
    title = track.get("name") or "Unknown track"

    album = track.get("album") or {}
    imgs = album.get("images") or []
    cover = imgs[1]["url"] if len(imgs) > 1 else (imgs[0]["url"] if imgs else "")

    track_id = track.get("id") or ""
    played_at = it.get("played_at") or ""

    return {
        "mode": "RECENT",
        "artist": artist,
        "title": title,
        "cover": cover,
        "track_id": track_id,
        "played_at": played_at,
    }


def equalizer_bars(seed: str, n: int = 48):
    # deterministic “live-looking” bars based on track + current 30s window
    bucket = int(time.time() // 30)
    h = hashlib.sha256(f"{seed}:{bucket}".encode()).digest()
    vals = []
    for i in range(n):
        b = h[i % len(h)]
        # heights tuned to look like v1.1
        vals.append(4 + (b % 16))  # 4..19
    return vals


def svg_v1_style(artist: str, title: str, cover_url: str, mode: str, seed: str):
    # target: your v1/v1.1 visual language (white, minimal, cover left)
    w, h = 900, 170
    pad = 14
    cover = 118
    x_cover = pad
    y_cover = (h - cover) // 2

    x_text = x_cover + cover + 18
    y_artist = 70
    y_title = 108

    show_eq = (mode == "PLAYING")
    bars = equalizer_bars(seed) if show_eq else []

    # equalizer geometry
    eq_x = x_text
    eq_y = 132
    bar_w = 6
    gap = 3

    # soft “card” edge like the service (very subtle)
    stroke = "#e6e6e6"
    text_main = "#111111"
    text_sub = "#222222"
    green = "#53b14f"

    cover_block = (
        f'<image href="{esc_xml(cover_url)}" x="{x_cover}" y="{y_cover}" width="{cover}" height="{cover}" />'
        if cover_url else
        f'<rect x="{x_cover}" y="{y_cover}" width="{cover}" height="{cover}" fill="#f2f2f2" />'
    )

    eq_block = ""
    if show_eq:
        parts = []
        for i, bh in enumerate(bars):
            x = eq_x + i * (bar_w + gap)
            y = eq_y - bh
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bh}" fill="{green}" />')
        eq_block = "\n  " + "\n  ".join(parts)

    rendered_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <!-- rendered_utc={esc_xml(rendered_utc)} mode={esc_xml(mode)} -->
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" ry="12" fill="#ffffff" stroke="{stroke}"/>
  {cover_block}

  <text x="{x_text}" y="{y_artist}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif"
        font-size="34" font-weight="700" fill="{text_main}">{esc_xml(artist)}</text>

  <text x="{x_text}" y="{y_title}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif"
        font-size="24" font-weight="400" fill="{text_sub}">{esc_xml(title)}</text>
  {eq_block}
</svg>'''


def main():
    token = get_access_token()

    current = get_currently_playing(token)
    if current and current.get("mode") == "PLAYING":
        data = current
        mode = "PLAYING"
    else:
        recent = get_recently_played(token)
        if not recent:
            raise RuntimeError("Spotify returned no recently-played items (empty history).")
        data = recent
        mode = "RECENT"

    svg = svg_v1_style(
        artist=data["artist"],
        title=data["title"],
        cover_url=data.get("cover", ""),
        mode=mode,
        seed=data.get("track_id", "") or f"{data['artist']}|{data['title']}",
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
