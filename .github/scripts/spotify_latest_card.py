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


def http_raw(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return r.getcode(), dict(r.headers), body


def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    code, hdrs, body = http_raw(url, headers=headers, data=data, timeout=timeout)
    txt = body.decode("utf-8", "replace").strip()
    return code, hdrs, (json.loads(txt) if txt else None)


def get_access_token() -> str:
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise RuntimeError("Missing Spotify secrets: SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIFY_REFRESH_TOKEN")

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

    if code >= 400 or not payload:
        raise RuntimeError(f"Token endpoint error (code={code}): {payload}")

    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in token response: {payload}")

    return token


def pick_cover(track: dict) -> str:
    album = track.get("album") or {}
    imgs = album.get("images") or []
    if len(imgs) > 1 and imgs[1].get("url"):
        return imgs[1]["url"]
    if imgs and imgs[0].get("url"):
        return imgs[0]["url"]
    return ""


def get_current_or_last(access_token: str):
    # 1) Try live currently-playing (may be 204)
    req = urllib.request.Request(CURRENT_URL, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 204:
                data = None
            else:
                raw = r.read().decode("utf-8", "replace").strip()
                data = json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        if e.code == 204:
            data = None
        else:
            raise
    except Exception:
        data = None

    if data and (data.get("item") is not None):
        track = data["item"]
        artists = track.get("artists") or []
        artist = ", ".join([a.get("name","") for a in artists if a.get("name")]) or "Unknown artist"
        title = track.get("name") or "Unknown track"
        cover = pick_cover(track)
        return {
            "artist": artist,
            "title": title,
            "cover": cover,
            "mode": "LIVE",
            "played_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
        }

    # 2) Fallback to recently-played
    code, _, payload = http_json(
        RECENT_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )

    if code >= 400 or not payload:
        raise RuntimeError(f"Spotify API error (recently-played) code={code}: {payload}")

    items = payload.get("items") or []
    if not items:
        raise RuntimeError("Spotify returned empty recently-played items.")

    it = items[0]
    track = it.get("track") or {}
    artists = track.get("artists") or []
    artist = ", ".join([a.get("name","") for a in artists if a.get("name")]) or "Unknown artist"
    title = track.get("name") or "Unknown track"
    cover = pick_cover(track)
    played_at = it.get("played_at") or ""

    return {
        "artist": artist,
        "title": title,
        "cover": cover,
        "mode": "LAST",
        "played_at": played_at,
    }


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg_white_card(artist: str, title: str, cover_url: str, mode: str, played_at: str):
    # White, similar proportions to your old embed screenshot
    w, h = 900, 205
    cover = 80
    x0, y0 = 38, 55
    x_text = x0 + cover + 22

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    mode_label = "LIVE" if mode == "LIVE" else "LAST"
    played_line = played_at or "N/A"

    cover_block = (
        f'<image href="{esc(cover_url)}" x="{x0}" y="{y0}" width="{cover}" height="{cover}" />'
        if cover_url else
        f'<rect x="{x0}" y="{y0}" width="{cover}" height="{cover}" fill="#f2f2f2" stroke="#e6e6e6" />'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="{w}" height="{h}" fill="#ffffff"/>
  {cover_block}

  <text x="{x_text}" y="{y0+28}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif"
        font-size="28" font-weight="700" fill="#111111">{esc(artist)}</text>

  <text x="{x_text}" y="{y0+58}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif"
        font-size="20" fill="#111111">{esc(title)} - {mode_label}</text>

  <text x="{x_text}" y="{y0+92}" font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono','Courier New',monospace"
        font-size="14" fill="#555555">Rendered (UTC): {esc(updated)}</text>

  <text x="{x_text}" y="{y0+112}" font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono','Courier New',monospace"
        font-size="14" fill="#555555">Last activity (UTC): {esc(played_line)}</text>
</svg>'''


def main():
    token = get_access_token()
    info = get_current_or_last(token)

    svg = svg_white_card(
        info["artist"],
        info["title"],
        info["cover"],
        info["mode"],
        info["played_at"],
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
