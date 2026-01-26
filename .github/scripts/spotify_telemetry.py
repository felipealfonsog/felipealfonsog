#!/usr/bin/env python3
# SPOTIFY TELEMETRY — CLI FEED (Spotify ©)
# Telemetry-only report: no UI/card references.

import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# ============================================================
# TOGGLES (TOP-LEVEL)
# ============================================================

# ---- Report sections
SHOW_HEADER                = True
SHOW_PLAYBACK_BLOCK         = True
SHOW_DELTA_BLOCK            = True
SHOW_TIMING_BLOCK           = True
SHOW_API_BLOCK              = True
SHOW_INTEGRITY_BLOCK        = True
SHOW_DAILY_SITREP           = True
SHOW_WEEKLY_CADENCE         = True

# ---- Playback details
SHOW_NOW_PLAYING_CONTEXT    = True   # album/device/shuffle/repeat
SHOW_PROGRESS               = True   # progress/duration %
SHOW_VOLUME                 = True   # volume % (needs /me/player, may be None)
SHOW_DEVICE                 = True   # device name/type

# ---- Daily / Weekly windows
DAILY_WINDOW_HOURS          = 24
WEEKLY_WINDOW_DAYS          = 7
OBS_WINDOW_SECONDS          = 30 * 60   # "Observation window" display (e.g., 00:30:00)

# ---- Output formatting
TITLE = "SPOTIFY TELEMETRY — CLI FEED (Spotify ©)"
SEP   = "-" * 60

# ---- README markers
README_PATH = "README.md"
MARKER_START = "<!-- SPOTIFY_TLM:START -->"
MARKER_END   = "<!-- SPOTIFY_TLM:END -->"

# ---- State file (committed) to compute deltas
STATE_PATH = "data/spotify_telemetry_state.json"

# ============================================================
# Spotify OAuth / API endpoints
# ============================================================

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

AUTH_URL     = "https://accounts.spotify.com/api/token"
PLAYER_URL   = "https://api.spotify.com/v1/me/player"  # includes device/shuffle/repeat/progress
CURRENT_URL  = "https://api.spotify.com/v1/me/player/currently-playing"
RECENT_URL   = "https://api.spotify.com/v1/me/player/recently-played?limit=50"

# ============================================================
# Helpers
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def hms(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def safe_read_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def safe_write_json(path: str, payload: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            payload = json.loads(raw) if raw.strip() else None
            return r.getcode(), dict(r.headers), payload
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        try:
            payload = json.loads(body) if body.strip() else None
        except Exception:
            payload = {"raw": body[:300]}
        return e.code, dict(e.headers), payload
    except Exception as e:
        return 0, {}, {"error": str(e)}

def get_access_token() -> str:
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise RuntimeError("Missing Spotify secrets (SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIFY_REFRESH_TOKEN).")

    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }).encode("utf-8")

    code, headers, payload = http_json(
        AUTH_URL,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=body,
        timeout=25,
    )

    if code != 200 or not payload or "access_token" not in payload:
        raise RuntimeError(f"Token refresh failed (HTTP {code}).")

    return payload["access_token"]

def auth_capabilities(scope_str: str | None) -> str:
    # Normalize raw scopes -> pro capabilities
    if not scope_str:
        return "UNKNOWN"

    scope_map = {
        "user-read-playback-state": "PLAYBACK_STATE",
        "user-read-currently-playing": "NOW_PLAYING",
        "user-read-recently-played": "RECENT_ACTIVITY",
    }
    caps = []
    for s in (scope_str.split() if scope_str else []):
        caps.append(scope_map.get(s.strip(), s.strip().upper()))
    # Deduplicate in order
    seen = set()
    caps2 = []
    for c in caps:
        if c not in seen:
            seen.add(c)
            caps2.append(c)
    return " | ".join(caps2) if caps2 else "UNKNOWN"

def parse_recent_items(items: list) -> list:
    out = []
    for it in (items or []):
        tr = it.get("track") or {}
        artists = tr.get("artists") or []
        artist = ", ".join([a.get("name","") for a in artists if a.get("name")]) or "Unknown artist"
        title  = tr.get("name") or "Unknown track"
        played_at = it.get("played_at") or ""
        out.append({
            "artist": artist,
            "title": title,
            "played_at": played_at,
        })
    return out

def best_dominant_artist(recent_tracks: list) -> str:
    if not recent_tracks:
        return "N/A"
    counts = {}
    for t in recent_tracks:
        a = t.get("artist") or "Unknown"
        counts[a] = counts.get(a, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

def cadence_classification(n_tracks: int, window_hours: int) -> str:
    # simple, stable classification
    if n_tracks <= 0:
        return "NONE"
    per_hour = n_tracks / max(1, window_hours)
    if per_hour >= 2.0:
        return "VERY HIGH"
    if per_hour >= 1.0:
        return "HIGH"
    if per_hour >= 0.25:
        return "MODERATE"
    return "LOW"

def compute_integrity(api_http: int, token_ok: bool) -> tuple[str, str]:
    if not token_ok:
        return ("DEGRADED", "AUTH")
    if api_http == 200 or api_http == 204:
        return ("OK", "NORMAL")
    if api_http in (401, 403):
        return ("DEGRADED", "AUTH")
    if api_http in (429,):
        return ("DEGRADED", "RATE_LIMIT")
    if api_http >= 500:
        return ("DEGRADED", "UPSTREAM")
    if api_http == 0:
        return ("DEGRADED", "NETWORK")
    return ("DEGRADED", "ANOMALY")

def dt_from_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

# ============================================================
# Core acquisition
# ============================================================

def fetch_player(access_token: str):
    # /me/player returns 200 with state OR 204 if no active device
    code, headers, payload = http_json(
        PLAYER_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=20,
    )
    return code, headers, payload

def fetch_current(access_token: str):
    code, headers, payload = http_json(
        CURRENT_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=20,
    )
    return code, headers, payload

def fetch_recent(access_token: str, limit: int = 50):
    url = "https://api.spotify.com/v1/me/player/recently-played?limit=" + str(limit)
    code, headers, payload = http_json(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=25,
    )
    return code, headers, payload

# ============================================================
# Report build
# ============================================================

def build_report(now_dt: datetime, token_scope: str | None, player_code: int, player_payload, current_code: int, current_payload, recent_code: int, recent_payload, prev_state: dict | None):
    # Determine status
    # Prefer /me/player for is_playing; fallback to /currently-playing
    status = "UNKNOWN"
    playback_state = "UNKNOWN"
    is_playing = None

    device_name = None
    device_type = None
    volume = None
    shuffle = None
    repeat = None
    progress_ms = None
    duration_ms = None

    # Parse /me/player
    if player_code == 200 and isinstance(player_payload, dict):
        is_playing = player_payload.get("is_playing")
        status = "PLAYING" if is_playing else "IDLE"
        playback_state = "ONLINE (active session)"
        dev = player_payload.get("device") or {}
        device_name = dev.get("name")
        device_type = dev.get("type")
        volume = dev.get("volume_percent")
        shuffle = player_payload.get("shuffle_state")
        repeat = player_payload.get("repeat_state")
        progress_ms = player_payload.get("progress_ms")
        item = player_payload.get("item") or {}
        duration_ms = item.get("duration_ms")

    elif player_code == 204:
        status = "IDLE"
        playback_state = "OFFLINE (no active session)"

    # Parse /currently-playing for now playing track info
    now_playing = None
    if current_code == 200 and isinstance(current_payload, dict):
        tr = current_payload.get("item") or {}
        artists = tr.get("artists") or []
        artist = ", ".join([a.get("name","") for a in artists if a.get("name")]) or "Unknown artist"
        title  = tr.get("name") or "Unknown track"
        album  = (tr.get("album") or {}).get("name")
        now_playing = {
            "artist": artist,
            "title": title,
            "album": album,
            "device": device_name,
            "device_type": device_type,
            "shuffle": shuffle if shuffle is not None else None,
            "repeat": repeat if repeat is not None else None,
            "volume": volume if volume is not None else None,
            "progress_ms": progress_ms if progress_ms is not None else current_payload.get("progress_ms"),
            "duration_ms": duration_ms if duration_ms is not None else tr.get("duration_ms"),
        }

    # Recent items
    recent_items = []
    last_played = None
    if recent_code == 200 and isinstance(recent_payload, dict):
        recent_items = parse_recent_items((recent_payload.get("items") or []))
        if recent_items:
            last_played = recent_items[0]

    # SITREP
    if status == "PLAYING":
        sitrep = "GREEN"
    elif status == "IDLE":
        sitrep = "AMBER"
    else:
        sitrep = "RED"

    # Timing / ages
    last_played_dt = dt_from_iso(last_played["played_at"]) if last_played else None
    time_since_last_play = None
    if last_played_dt:
        time_since_last_play = int((now_dt - last_played_dt).total_seconds())

    telemetry_age = 0  # generated now, so 0 in strict sense; we’ll compute "observation age" as time since last_play if idle
    if status == "IDLE" and time_since_last_play is not None:
        telemetry_age = time_since_last_play

    # Deltas
    def delta_str(label: str, prev_val, cur_val):
        if prev_state is None:
            return f"{label:<24}: N/A (first report)"
        if prev_val is None or cur_val is None:
            return f"{label:<24}: N/A"
        if prev_val == cur_val:
            return f"{label:<24}: NO CHANGE"
        return f"{label:<24}: {prev_val} → {cur_val}"

    prev_track = None
    prev_last_played = None
    prev_status = None
    prev_generated = None

    if prev_state:
        prev_track = prev_state.get("last_track")
        prev_last_played = prev_state.get("last_played_utc")
        prev_status = prev_state.get("status")
        prev_generated = dt_from_iso(prev_state.get("generated_utc") or "")

    cur_track = None
    if last_played:
        cur_track = f"{last_played['artist']} — {last_played['title']}"

    cur_last_played = iso_z(last_played_dt) if last_played_dt else None

    delta_time_since_last_report = None
    if prev_generated:
        delta_time_since_last_report = int((now_dt - prev_generated).total_seconds())

    # Daily / weekly summaries
    daily_tracks = []
    weekly_tracks = []
    if recent_items:
        for t in recent_items:
            tdt = dt_from_iso(t.get("played_at") or "")
            if not tdt:
                continue
            if tdt >= (now_dt - timedelta(hours=DAILY_WINDOW_HOURS)):
                daily_tracks.append(t)
            if tdt >= (now_dt - timedelta(days=WEEKLY_WINDOW_DAYS)):
                weekly_tracks.append(t)

    # Confidence (simple heuristic)
    confidence = "HIGH"
    if recent_code != 200:
        confidence = "LOW"
    elif status == "UNKNOWN":
        confidence = "MEDIUM"

    # API integrity
    token_ok = True
    integrity, api_condition = compute_integrity(
        api_http=(player_code if player_code else (current_code if current_code else recent_code)),
        token_ok=token_ok
    )

    # Build lines
    out = []
    out.append(TITLE)
    out.append(SEP)

    if SHOW_HEADER:
        out.append(f"Telemetry source          : Spotify Playback Telemetry (Developer Platform) ©")
        out.append(f"Acquisition mode          : OAuth2 / automated workflow")
        out.append(f"Snapshot type             : Last-known playback state")
        out.append(f"Observation window        : {hms(OBS_WINDOW_SECONDS)}")
        out.append(SEP)

    if SHOW_PLAYBACK_BLOCK:
        out.append(f"Status                    : {status}")
        out.append(f"Playback state            : {playback_state}")
        out.append(f"SITREP                    : {sitrep}")
        out.append(SEP)

        # Now playing: telemetry-only (no UI references)
        if status == "PLAYING" and now_playing:
            out.append(f"Now playing               : {now_playing['artist']} — {now_playing['title']}")
            if SHOW_NOW_PLAYING_CONTEXT:
                ctx = []
                if now_playing.get("album"):
                    ctx.append(f"album={now_playing['album']}")
                if SHOW_DEVICE and now_playing.get("device"):
                    dtype = now_playing.get("device_type") or "Device"
                    ctx.append(f"device={now_playing['device']} ({dtype})")
                if now_playing.get("shuffle") is not None:
                    ctx.append(f"shuffle={'ON' if now_playing['shuffle'] else 'OFF'}")
                if now_playing.get("repeat"):
                    ctx.append(f"repeat={str(now_playing['repeat']).upper()}")
                if ctx:
                    out.append("Now playing (context)     : " + " | ".join(ctx))

            if SHOW_PROGRESS and now_playing.get("progress_ms") is not None and now_playing.get("duration_ms"):
                prog = int(now_playing["progress_ms"]) / 1000.0
                dur  = int(now_playing["duration_ms"]) / 1000.0
                pct  = (prog / dur) * 100.0 if dur > 0 else 0.0

                def mmss(x):
                    x = int(x)
                    return f"{x//60:02d}:{x%60:02d}"

                out.append(f"Progress                  : {mmss(prog)} / {mmss(dur)} ({pct:0.1f}%)")

            if SHOW_VOLUME and now_playing.get("volume") is not None:
                out.append(f"Volume                    : {now_playing['volume']}%")

        else:
            out.append("Now playing               : N/A")

        if last_played:
            out.append(f"Last played               : {last_played['artist']} — {last_played['title']}")
            out.append(f"Last played (UTC)         : {iso_z(last_played_dt) if last_played_dt else 'N/A'}")
        else:
            out.append("Last played               : N/A")
            out.append("Last played (UTC)         : N/A")

        out.append(SEP)

    if SHOW_DELTA_BLOCK:
        out.append("SINCE LAST REPORT")
        out.append(SEP)
        out.append(delta_str("Δ track", prev_track, cur_track))
        out.append(delta_str("Δ last played (UTC)", prev_last_played, cur_last_played))
        out.append(delta_str("Δ status", prev_status, status))
        if prev_state is None:
            out.append(f"{'Δ time (report gap)':<24}: N/A (first report)")
        else:
            out.append(f"{'Δ time (report gap)':<24}: {hms(delta_time_since_last_report or 0)}")
        out.append(SEP)

    if SHOW_TIMING_BLOCK:
        out.append("TIMING")
        out.append(SEP)
        out.append(f"Time since last play      : {hms(time_since_last_play) if time_since_last_play is not None else 'N/A'}")
        out.append(f"Telemetry age             : {hms(telemetry_age) if telemetry_age is not None else 'N/A'}")
        out.append(SEP)

    if SHOW_API_BLOCK:
        # Prefer player_code: it’s the richest endpoint
        api_http = player_code if player_code else (current_code if current_code else recent_code)
        api_class = f"{api_http} OK" if api_http in (200, 204) else (f"{api_http} ERROR" if api_http else "NETWORK ERROR")

        out.append("API")
        out.append(SEP)
        out.append(f"API response class        : {api_class}")
        out.append(f"API condition             : {api_condition}")
        # No raw scopes: pro capabilities only
        out.append(f"Authorization scope       : {auth_capabilities(token_scope)}")
        out.append(SEP)

    if SHOW_INTEGRITY_BLOCK:
        out.append("INTEGRITY")
        out.append(SEP)
        out.append(f"Data integrity            : {integrity}")
        out.append(f"Confidence level          : {confidence}")
        out.append(SEP)

    if SHOW_DAILY_SITREP:
        out.append("DAILY SPOTIFY SITREP")
        out.append(SEP)
        out.append(f"Tracks played (last {DAILY_WINDOW_HOURS}h) : {len(daily_tracks)}")
        out.append(f"Dominant artist           : {best_dominant_artist(daily_tracks)}")
        out.append(f"Daily activity status     : {cadence_classification(len(daily_tracks), DAILY_WINDOW_HOURS)}")
        out.append(SEP)

    if SHOW_WEEKLY_CADENCE:
        out.append("WEEKLY CADENCE SUMMARY")
        out.append(SEP)
        w_start = iso_z(now_dt - timedelta(days=WEEKLY_WINDOW_DAYS))
        w_end   = iso_z(now_dt)
        out.append(f"Week window (UTC)         : {w_start} → {w_end}")
        out.append(f"Total tracks played       : {len(weekly_tracks)}")
        out.append(f"Dominant artist           : {best_dominant_artist(weekly_tracks)}")
        out.append(f"Cadence classification    : {cadence_classification(len(weekly_tracks), WEEKLY_WINDOW_DAYS * 24)}")
        out.append(SEP)

    out.append(f"Report generated (UTC)    : {iso_z(now_dt)}")

    # Next state to persist
    next_state = {
        "generated_utc": iso_z(now_dt),
        "status": status,
        "last_track": cur_track,
        "last_played_utc": cur_last_played,
    }

    return "\n".join(out), next_state

def update_readme_block(report_text: str):
    with open(README_PATH, "r", encoding="utf-8") as f:
        md = f.read()

    pattern = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), re.S)
    if not pattern.search(md):
        raise RuntimeError(f"Markers not found in README: {MARKER_START} ... {MARKER_END}")

    block = (
        f"{MARKER_START}\n"
        "```text\n"
        f"{report_text.rstrip()}\n"
        "```\n"
        f"{MARKER_END}"
    )

    md2 = pattern.sub(block, md)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(md2)

def main():
    now_dt = utc_now()

    # Load previous state
    prev_state = safe_read_json(STATE_PATH)

    # Acquire token + scope (scope is in token response; we fetch it here)
    token_ok = False
    token_scope = None

    try:
        # token refresh (manual for scope)
        if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
            raise RuntimeError("Missing Spotify secrets.")

        auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
        }).encode("utf-8")

        code, headers, payload = http_json(
            AUTH_URL,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=body,
            timeout=25,
        )

        if code == 200 and payload and payload.get("access_token"):
            token_ok = True
            access_token = payload["access_token"]
            token_scope = payload.get("scope")
        else:
            raise RuntimeError(f"Token refresh failed (HTTP {code}).")

    except Exception as e:
        # Fail-safe: do not touch README/state if auth fails
        print(f"[spotify_telemetry_cli] AUTH ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch endpoints
    player_code, _, player_payload = fetch_player(access_token)
    current_code, _, current_payload = fetch_current(access_token)
    recent_code, _, recent_payload = fetch_recent(access_token, limit=50)

    # Basic sanity: if everything failed, don’t rewrite README
    if (player_code in (0,)) and (current_code in (0,)) and (recent_code in (0,)):
        print("[spotify_telemetry_cli] Network failure; preserving previous README.", file=sys.stderr)
        sys.exit(1)

    # Build report
    report, next_state = build_report(
        now_dt=now_dt,
        token_scope=token_scope,
        player_code=player_code,
        player_payload=player_payload,
        current_code=current_code,
        current_payload=current_payload,
        recent_code=recent_code,
        recent_payload=recent_payload,
        prev_state=prev_state,
    )

    # Update README + persist state
    update_readme_block(report)
    safe_write_json(STATE_PATH, next_state)

if __name__ == "__main__":
    main()
