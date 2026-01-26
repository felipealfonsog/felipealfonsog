#!/usr/bin/env python3
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

OUT = "images/spotify_now.svg"

AUTH_URL = "https://accounts.spotify.com/api/token"
RECENT_URL = "https://api.spotify.com/v1/me/player/recently-played?limit=1"

def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.getcode(), r.headers, json.loads(r.read().decode("utf-8", "replace"))

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
    )

    if code >= 400:
        raise RuntimeError(f"Token endpoint error: {payload}")

    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in response: {payload}")
    return token

def get_latest_track(access_token: str):
    code, _, payload = http_json(
        RECENT_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if code >= 400:
        raise RuntimeError(f"Spotify API error (recently-played): {payload}")

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

    return {"artist": artist, "title": title, "cover": cover}

def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def svg_original_white(artist: str, title: str, cover_url: str):
    # Tuned to look like the original "white" embed screenshot
    w, h = 720, 120
    pad_x = 14
    cover = 72
    x_art = pad_x
    y_art = 14
    x_text = x_art + cover + 16

    y_artist = 48
    y_track  = 74

    cover_block = (
        f'<image href="{esc(cover_url)}" x="{x_art}" y="{y_art}" width="{cover}" height="{cover}" />'
        if cover_url else
        f'<rect x="{x_art}" y="{y_art}" width="{cover}" height="{cover}" fill="#f2f2f2" stroke="#e5e5e5" />'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <style>
      .artist {{ fill: #111111; font: 700 20px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
      .track  {{ fill: #111111; font: 400 16px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
    </style>
  </defs>

  {cover_block}
  <text class="artist" x="{x_text}" y="{y_artist}">{esc(artist)}</text>
  <text class="track"  x="{x_text}" y="{y_track}">{esc(title)}</text>
</svg>'''

def main():
    token = get_access_token()
    latest = get_latest_track(token)
    if not latest:
        raise RuntimeError("No recently played track returned by Spotify (items empty).")

    svg = svg_original_white(latest["artist"], latest["title"], latest["cover"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
