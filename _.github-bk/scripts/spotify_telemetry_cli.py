#!/usr/bin/env python3
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

README = "README.md"
STATE_PATH = "data/spotify_telemetry_state.json"

AUTH_URL   = "https://accounts.spotify.com/api/token"
CURRENT_URL = "https://api.spotify.com/v1/me/player/currently-playing"
RECENT_URL  = "https://api.spotify.com/v1/me/player/recently-played?limit=1"

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

# ---- toggles (enable/disable sections) ----
SHOW_HEADER = True
SHOW_SOURCE = True
SHOW_STATUS = True
SHOW_NOW_PLAYING = True
SHOW_LAST_PLAYED = True
SHOW_DELTAS = True
SHOW_TIMERS = True
SHOW_HEALTH = True
SHOW_FOOTER = True

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
        return r.getcode(), dict(r.headers), (json.loads(raw) if raw.strip() else {})

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
        timeout=25
    )
    if code >= 400:
        raise RuntimeError(f"Token endpoint error: {payload}")
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in response: {payload}")
    return token

def try_get_current(token: str):
    req = urllib.request.Request(CURRENT_URL, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 204:
                return {"status_code": 204, "data": None}
            raw = r.read().decode("utf-8", "replace").strip()
            return {"status_code": r.status, "data": json.loads(raw) if raw else None}
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return {"status_code": 204, "data": None}
        return {"status_code": e.code, "data": None}
    except Exception:
        return {"status_code": -1, "data": None}

def get_recent(token: str):
    code, _, payload = http_json(
        RECENT_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=20
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
    played_at = it.get("played_at") or ""
    return {
        "track": f"{artist} — {title}",
        "played_at": played_at,
    }

def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def parse_iso(ts: str):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def fmt_age(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "N/A"
    sec = int(seconds)
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def build_report(now_playing: str | None, status: str, last_track: str | None, last_played_utc: str | None, prev: dict | None, api_condition: str, cache_state: str):
    lines = []

    if SHOW_HEADER:
        lines.append("SPOTIFY TELEMETRY — CLI FEED (Spotify ©)")
        lines.append("------------------------------------------------------------")

    if SHOW_SOURCE:
        lines.append("Spotify Developer API Source : Spotify Web API")
        lines.append("Acquisition mode             : OAuth2 / automated workflow")
        lines.append("Snapshot type                : Last-known playback state")
        lines.append("------------------------------------------------------------")

    if SHOW_STATUS:
        sitrep = "GREEN" if status == "PLAYING" else ("AMBER" if status == "IDLE" else "RED")
        playback_state = "ONLINE (active session)" if status == "PLAYING" else "OFFLINE (no active session)"
        lines.append(f"Status                    : {status}")
        lines.append(f"Playback state            : {playback_state}")
        lines.append(f"SITREP                    : {sitrep}")
        lines.append("------------------------------------------------------------")

    if SHOW_NOW_PLAYING:
        # “bold” no existe en fenced text; lo simulo con énfasis visual.
        np = now_playing or "-"
        lines.append(f"NOW PLAYING               : {np}")
        lines.append("------------------------------------------------------------")

    if SHOW_LAST_PLAYED:
        lt = last_track or "-"
        lp = last_played_utc or "-"
        lines.append(f"Last played               : {lt}")
        lines.append(f"Last played (UTC)         : {lp}")
        lines.append("Last activity type        : " + ("TRACK_PROGRESS" if status == "PLAYING" else "TRACK_END"))
        lines.append("------------------------------------------------------------")

    if SHOW_DELTAS:
        if prev:
            prev_track = prev.get("last_track")
            prev_lp = prev.get("last_played_utc")
            prev_status = prev.get("status")

            d_track = "UNCHANGED" if (prev_track == (last_track or "")) else "CHANGED"
            d_lp = "UNCHANGED" if (prev_lp == (last_played_utc or "")) else "CHANGED"
            d_st = "UNCHANGED" if (prev_status == status) else f"{prev_status} -> {status}"
            lines.append(f"Δ track (since last)      : {d_track}")
            lines.append(f"Δ last played (since last): {d_lp}")
            lines.append(f"Δ status (since last)     : {d_st}")
        else:
            lines.append("Δ track (since last)      : N/A (first report)")
            lines.append("Δ last played (since last): N/A (first report)")
            lines.append("Δ status (since last)     : N/A (first report)")
        lines.append("------------------------------------------------------------")

    if SHOW_TIMERS:
        now_dt = datetime.now(timezone.utc)
        lp_dt = parse_iso(last_played_utc) if last_played_utc else None
        prev_gen = parse_iso(prev.get("generated_utc")) if prev else None

        since_last_play = (now_dt - lp_dt).total_seconds() if lp_dt else None
        telemetry_age = (now_dt - prev_gen).total_seconds() if prev_gen else None

        lines.append(f"Time since last play      : {fmt_age(since_last_play)}")
        lines.append(f"Telemetry age             : {fmt_age(telemetry_age)}")
        lines.append("------------------------------------------------------------")

    if SHOW_HEALTH:
        lines.append("Data integrity            : OK")
        lines.append(f"API condition             : {api_condition}")
        lines.append(f"Cache state               : {cache_state}")
        lines.append("------------------------------------------------------------")

    if SHOW_FOOTER:
        lines.append(f"Report generated (UTC)    : {utc_now()}")

    return "\n".join(lines)

def replace_block(readme: str, block_text: str) -> str:
    pattern = re.compile(r"<!-- SPOTIFY_TELEMETRY:START -->.*?<!-- SPOTIFY_TELEMETRY:END -->", re.S)
    if not pattern.search(readme):
        raise RuntimeError("Markers not found: <!-- SPOTIFY_TELEMETRY:START --> ... <!-- SPOTIFY_TELEMETRY:END -->")
    injected = (
        "<!-- SPOTIFY_TELEMETRY:START -->\n"
        "```text\n"
        f"{block_text.rstrip()}\n"
        "```\n"
        "<!-- SPOTIFY_TELEMETRY:END -->"
    )
    return pattern.sub(injected, readme)

def main():
    api_condition = "NORMAL"
    cache_state = "POSSIBLE HIT"

    prev = load_state()

    token = get_access_token()

    cur = try_get_current(token)
    status = "UNKNOWN"
    now_playing = None

    if cur["status_code"] == 200 and cur["data"]:
        status = "PLAYING" if cur["data"].get("is_playing") else "IDLE"
        item = cur["data"].get("item") or {}
        artists = item.get("artists") or []
        artist = ", ".join([a.get("name","") for a in artists if a.get("name")]) or "Unknown artist"
        title = item.get("name") or "Unknown track"
        now_playing = f"{artist} — {title}" if status == "PLAYING" else None
    elif cur["status_code"] == 204:
        status = "IDLE"
    else:
        status = "UNKNOWN"
        api_condition = "DEGRADED"

    recent = get_recent(token)
    if not recent:
        api_condition = "DEGRADED"
        last_track = None
        last_played_utc = None
    else:
        last_track = recent["track"]
        last_played_utc = recent["played_at"]

    report = build_report(
        now_playing=now_playing,
        status=status,
        last_track=last_track,
        last_played_utc=last_played_utc,
        prev=prev,
        api_condition=api_condition,
        cache_state=cache_state,
    )

    with open(README, "r", encoding="utf-8") as f:
        md = f.read()

    md2 = replace_block(md, report)

    with open(README, "w", encoding="utf-8") as f:
        f.write(md2)

    save_state({
        "status": status,
        "now_playing": now_playing or "",
        "last_track": last_track or "",
        "last_played_utc": last_played_utc or "",
        "generated_utc": utc_now(),
    })

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
