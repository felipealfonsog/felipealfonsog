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
CURRENT_URL = "https://api.spotify.com/v1/me/player/currently-playing"

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

def get_playback_status(access_token: str) -> str:
    req = urllib.request.Request(
        CURRENT_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            # 200 => a track is currently playing (or at least an active playback context)
            if r.status == 200:
                return "PLAYING (live)"
            # sometimes Spotify returns 204 for no content, but urllib treats 204 as success with no body;
            # still, status check:
            if r.status == 204:
                return "IDLE (last activity)"
    except urllib.error.HTTPError as e:
        # 204 usually comes through as HTTPError in some stacks, keep it safe:
        if e.code == 204:
            return "IDLE (last activity)"
        # 403 can happen if scopes are insufficient
        if e.code == 403:
            return "UNKNOWN"
        # 401 token issue etc.
        if e.code == 401:
            return "UNKNOWN"
    except Exception:
        return "UNKNOWN"
    return "UNKNOWN"

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

    played_at = it.get("played_at") or ""
    track_url = (track.get("external_urls") or {}).get("spotify") or ""

    return {
        "artist": artist,
        "title": title,
        "cover": cover,
        "played_at": played_at,
        "track_url": track_url,
    }

def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def svg_card(artist: str, title: str, cover_url: str, played_at: str, status: str):
    # Dark, clean card similar to your screenshot: cover left, text right.
    w, h = 900, 205
    pad = 18
    cover = 150
    y_cover = (h - cover) // 2
    x_text = pad + cover + 18

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    played = played_at or "N/A"

    # Layout:
    # y positions tuned to avoid crowding while keeping the look compact.
    y_label  = pad + 20
    y_artist = pad + 70
    y_track  = pad + 108
    y_status = pad + 136
    y_meta   = h - 24

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <style>
      .bg {{ fill: #000; }}
      .label {{ fill: #a9a9a9; font: 12px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
      .artist {{ fill: #f5f5f5; font: 24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-weight: 700; }}
      .track {{ fill: #f5f5f5; font: 18px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
      .meta {{ fill: #a9a9a9; font: 12px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
    </style>
    <clipPath id="clip">
      <rect x="{pad}" y="{y_cover}" width="{cover}" height="{cover}" rx="10" ry="10"/>
    </clipPath>
  </defs>

  <rect class="bg" x="0" y="0" width="{w}" height="{h}" rx="14" ry="14"/>

  {"<image href=\\"" + esc(cover_url) + "\\" x=\\"" + str(pad) + "\\" y=\\"" + str(y_cover) + "\\" width=\\"" + str(cover) + "\\" height=\\"" + str(cover) + "\\" clip-path=\\"url(#clip)\\"/>" if cover_url else f"<rect x='{pad}' y='{y_cover}' width='{cover}' height='{cover}' rx='10' ry='10' fill='#111'/>"}

  <text class="label" x="{x_text}" y="{y_label}">CURRENTLY OR PREVIOUSLY ON SPOTIFY</text>
  <text class="artist" x="{x_text}" y="{y_artist}">{esc(artist)}</text>
  <text class="track"  x="{x_text}" y="{y_track}">{esc(title)}</text>

  <text class="meta" x="{x_text}" y="{y_status}">Status : {esc(status)}</text>
  <text class="meta" x="{x_text}" y="{y_meta}">Last played (UTC): {esc(played)}  |  Rendered (UTC): {esc(updated)}</text>
</svg>'''

def main():
    token = get_access_token()

    status = get_playback_status(token)
    latest = get_latest_track(token)

    if not latest:
        raise RuntimeError("No recently played track returned by Spotify (items empty).")

    svg = svg_card(
        latest["artist"],
        latest["title"],
        latest["cover"],
        latest["played_at"],
        status,
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
