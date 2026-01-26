#!/usr/bin/env python3
import base64
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

OUT = "images/spotify_now.svg"

def req_json(url, headers=None, data=None, timeout=25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def get_access_token():
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise SystemExit("Missing Spotify secrets (CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN).")

    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    body = "grant_type=refresh_token&refresh_token=" + urllib.parse.quote(REFRESH_TOKEN)
    data = body.encode("utf-8")

    token = req_json(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=data,
    )
    return token["access_token"]

def get_latest_track(access_token: str):
    data = req_json(
        "https://api.spotify.com/v1/me/player/recently-played?limit=1",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    items = data.get("items") or []
    if not items:
        return None

    it = items[0]
    track = it.get("track") or {}
    artist = ", ".join([a.get("name","") for a in (track.get("artists") or []) if a.get("name")]) or "Unknown"
    name = track.get("name") or "Unknown"
    url = (track.get("external_urls") or {}).get("spotify") or ""
    album = track.get("album") or {}
    images = album.get("images") or []
    cover = images[1]["url"] if len(images) > 1 else (images[0]["url"] if images else "")

    played_at = it.get("played_at") or ""
    return {
        "artist": artist,
        "track": name,
        "cover": cover,
        "spotify_url": url,
        "played_at": played_at,
    }

def esc(s: str) -> str:
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def svg_card(artist, track, cover_url, played_at_utc):
    # Card layout similar to screenshot: cover left, text right, dark bg
    # Note: external image references in SVG are allowed by GitHub for many cases; if it fails, we can embed the cover (heavier).
    w, h = 720, 160
    pad = 18
    cover = 124
    x_text = pad + cover + 18

    title = "Currently or previously on Spotify"
    line1 = artist
    line2 = track

    stamp = played_at_utc or "N/A"
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <style>
      .bg {{ fill: #000; }}
      .muted {{ fill: #a9a9a9; font: 12px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
      .h1 {{ fill: #eaeaea; font: 13px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
      .a {{ fill: #f5f5f5; font: 22px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-weight: 700; }}
      .t {{ fill: #f5f5f5; font: 18px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
    </style>
    <clipPath id="r">
      <rect x="{pad}" y="{(h-cover)//2}" width="{cover}" height="{cover}" rx="8" ry="8"/>
    </clipPath>
  </defs>

  <rect class="bg" x="0" y="0" width="{w}" height="{h}" rx="12" ry="12"/>

  {"<image href=\\"" + esc(cover_url) + "\\" x=\\"" + str(pad) + "\\" y=\\"" + str((h-cover)//2) + "\\" width=\\"" + str(cover) + "\\" height=\\"" + str(cover) + "\\" clip-path=\\"url(#r)\\"/>" if cover_url else f"<rect x='{pad}' y='{(h-cover)//2}' width='{cover}' height='{cover}' rx='8' ry='8' fill='#111'/>"}

  <text class="h1" x="{x_text}" y="{pad+18}">{esc(title)}</text>
  <text class="a"  x="{x_text}" y="{pad+62}">{esc(line1)}</text>
  <text class="t"  x="{x_text}" y="{pad+96}">{esc(line2)}</text>

  <text class="muted" x="{x_text}" y="{h-22}">Last played (UTC): {esc(stamp)}  |  Rendered: {esc(updated)}</text>
</svg>'''

def main():
    access = get_access_token()
    latest = get_latest_track(access)
    if not latest:
        raise SystemExit("No recently played track returned.")

    svg = svg_card(
        latest["artist"],
        latest["track"],
        latest["cover"],
        latest["played_at"],
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    import urllib.parse
    main()
