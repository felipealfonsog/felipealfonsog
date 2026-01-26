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
        return r.getcode(), dict(r.headers), json.loads(raw) if raw.strip() else {}

def get_access_token() -> str:
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise RuntimeError("Missing Spotify secrets (SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIFY_REFRESH_TOKEN).")

    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")).decode("ascii")
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
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def svg_card_white(artist: str, title: str, cover_url: str, played_at: str) -> str:
    # White, clean, stable XML
    w, h = 900, 205
    pad = 18
    cover = 150
    y_cover = (h - cover) // 2
    x_text = pad + cover + 18

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    played = played_at or "N/A"

    cover_block = (
        f'<image href="{esc(cover_url)}" x="{pad}" y="{y_cover}" width="{cover}" height="{cover}" clip-path="url(#clip)"/>'
        if cover_url else
        f'<rect x="{pad}" y="{y_cover}" width="{cover}" height="{cover}" rx="12" ry="12" fill="#f2f2f2"/>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <style>
      .bg {{ fill: #ffffff; }}
      .frame {{ fill: none; stroke: #e6e6e6; stroke-width: 1; }}
      .label {{ fill: #6b6b6b; font: 12px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
      .artist {{ fill: #111111; font: 24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-weight: 700; }}
      .track {{ fill: #111111; font: 18px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
      .meta {{ fill: #6b6b6b; font: 12px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
    </style>
    <clipPath id="clip">
      <rect x="{pad}" y="{y_cover}" width="{cover}" height="{cover}" rx="12" ry="12"/>
    </clipPath>
  </defs>

  <rect class="bg" x="0" y="0" width="{w}" height="{h}" rx="16" ry="16"/>
  <rect class="frame" x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="16" ry="16"/>

  {cover_block}

  <text class="label" x="{x_text}" y="{pad+26}">CURRENTLY OR PREVIOUSLY ON SPOTIFY</text>
  <text class="artist" x="{x_text}" y="{pad+78}">{esc(artist)}</text>
  <text class="track"  x="{x_text}" y="{pad+118}">{esc(title)}</text>

  <text class="meta" x="{x_text}" y="{h-26}">Last played (UTC): {esc(played)}  |  Rendered (UTC): {esc(updated)}</text>
</svg>'''
    # Hard guarantee: no leading whitespace/BOM before <svg
    return svg.lstrip()

def main():
    token = get_access_token()
    latest = get_latest_track(token)
    if not latest:
        raise RuntimeError("No recently played track returned by Spotify (items empty).")

    svg = svg_card_white(latest["artist"], latest["title"], latest["cover"], latest["played_at"])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(svg.encode("utf-8"))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
