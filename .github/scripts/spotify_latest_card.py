#!/usr/bin/env python3
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

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
        raw = r.read().decode("utf-8", "replace")
        return r.getcode(), r.headers, json.loads(raw) if raw.strip() else {}

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
        timeout=25,
    )

    if code >= 400:
        raise RuntimeError(f"Spotify API error (recently-played): {payload}")

    items = payload.get("items") or []
    if not items:
        return None

    it = items[0]
    track = it.get("track") or {}
    artists = track.get("artists") or []
    artist = ", ".join([a.get("name","") for a in artists if a.get("name")]) or "Unknown artist"
    title = track.get("name") or "Unknown track"

    album = track.get("album") or {}
    imgs = album.get("images") or []
    cover = imgs[-1]["url"] if len(imgs) else ""  # smallest is usually last; looks like the external card
    played_at = it.get("played_at") or ""

    return {
        "artist": artist,
        "title": title,
        "cover": cover,
        "played_at": played_at,
    }

def esc(s: str) -> str:
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def svg_card_white(artist: str, title: str, cover_url: str, played_at: str):
    # White template similar to the external render:
    # cover-left (small), text-right, clean typography, no dark container.
    w, h = 900, 205
    pad = 22
    cover = 92
    x_cover = pad
    y_cover = 54

    x_text = x_cover + cover + 26
    y_header = 42
    y_artist = 92
    y_title  = 122
    y_footer = 188

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    played = played_at or "N/A"

    cover_block = (
        f'<image href="{esc(cover_url)}" x="{x_cover}" y="{y_cover}" width="{cover}" height="{cover}" preserveAspectRatio="xMidYMid slice" />'
        if cover_url else
        f'<rect x="{x_cover}" y="{y_cover}" width="{cover}" height="{cover}" fill="#f2f2f2" stroke="#e5e5e5"/>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="{w}" height="{h}" fill="#ffffff"/>
  {cover_block}

  <text x="{x_text}" y="{y_header}"
        font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"
        font-size="14" fill="#111111">CURRENTLY OR PREVIOUSLY ON SPOTIFY ...</text>

  <text x="{x_text}" y="{y_artist}"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif"
        font-size="26" fill="#111111" font-weight="700">{esc(artist)}</text>

  <text x="{x_text}" y="{y_title}"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif"
        font-size="18" fill="#111111">{esc(title)}</text>

  <text x="{x_text}" y="{y_footer}"
        font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"
        font-size="12" fill="#444444">Last played (UTC): {esc(played)}  |  Rendered (UTC): {esc(updated)}</text>
</svg>'''

def main():
    token = get_access_token()
    latest = get_latest_track(token)
    if not latest:
        raise RuntimeError("No recently played track returned by Spotify (items empty).")

    svg = svg_card_white(latest["artist"], latest["title"], latest["cover"], latest["played_at"])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
