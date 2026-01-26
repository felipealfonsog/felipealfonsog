#!/usr/bin/env python3
# .github/scripts/spotify_telemetry.py

import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# =============================================================================
# TOGGLES (set True/False)
# =============================================================================

# Master switches
SHOW_HEADER_META          = True
SHOW_STATUS_BLOCK         = True
SHOW_TRACK_BLOCK          = True
SHOW_DELTAS_BLOCK         = True
SHOW_TIME_BLOCK           = True
SHOW_API_BLOCK            = True
SHOW_INTEGRITY_BLOCK      = True
SHOW_DAILY_SITREP         = True
SHOW_WEEKLY_SUMMARY       = True

# Sub-toggles / formatting
SCOPE_MODE = "WRAP"   # "WRAP" | "COMPACT" | "OFF"
WRAP_WIDTH = 34       # scope wrapping width for WRAP mode

# Behavior toggles
FAIL_SAFE_DO_NOT_BREAK_README = True   # if Spotify fails, keep old README block
WRITE_STATE_FILE              = True   # store last report for deltas
OBS_WINDOW_SECONDS            = 30 * 60 # "Observation window" label

# =============================================================================
# Config / files
# =============================================================================

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

AUTH_URL      = "https://accounts.spotify.com/api/token"
CURRENT_URL   = "https://api.spotify.com/v1/me/player/currently-playing"
RECENT_URL    = "https://api.spotify.com/v1/me/player/recently-played?limit=50"

README_PATH   = "README.md"
MARKER_START  = "<!-- SPOTIFY_TEL:START -->"
MARKER_END    = "<!-- SPOTIFY_TEL:END -->"

STATE_DIR     = ".github/state"
STATE_FILE    = os.path.join(STATE_DIR, "spotify_last_report.json")

# =============================================================================
# Helpers
# =============================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def utc_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%SZ")

def clamp(n, lo, hi):
    return max(lo, min(hi, n))

def fmt_hms(seconds: float) -> str:
    if seconds is None or seconds < 0:
        return "N/A"
    sec = int(round(seconds))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        if not body.strip():
            return r.status, dict(r.headers), None
        return r.status, dict(r.headers), json.loads(body)

def spotify_access_token():
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise RuntimeError("Missing Spotify secrets: SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIFY_REFRESH_TOKEN")

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
        timeout=25
    )

    if code >= 400 or not payload:
        raise RuntimeError(f"Spotify token refresh failed (HTTP {code}): {payload}")

    token = payload.get("access_token")
    scope = payload.get("scope") or ""
    if not token:
        raise RuntimeError(f"No access_token in token response: {payload}")

    return token, scope

def fetch_currently_playing(token: str):
    req = urllib.request.Request(CURRENT_URL, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 204:
                return {"http": 204, "data": None}
            raw = r.read().decode("utf-8", "replace").strip()
            if not raw:
                return {"http": r.status, "data": None}
            return {"http": r.status, "data": json.loads(raw)}
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return {"http": 204, "data": None}
        try:
            raw = e.read().decode("utf-8", "replace")
        except Exception:
            raw = ""
        return {"http": e.code, "data": raw or None}
    except Exception as e:
        return {"http": -1, "data": str(e)}

def fetch_recently_played(token: str, limit: int = 50):
    url = "https://api.spotify.com/v1/me/player/recently-played?limit=" + str(limit)
    code, headers, payload = http_json(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    return code, payload

def parse_track_item(track_obj: dict):
    if not track_obj:
        return None
    artists = track_obj.get("artists") or []
    artist = ", ".join([a.get("name","") for a in artists if a.get("name")]) or "Unknown artist"
    title = track_obj.get("name") or "Unknown track"
    uri = track_obj.get("uri") or ""
    ext = (track_obj.get("external_urls") or {}).get("spotify") or ""
    album = track_obj.get("album") or {}
    album_name = album.get("name") or ""
    return {
        "artist": artist,
        "title": title,
        "album": album_name,
        "uri": uri,
        "url": ext,
    }

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(obj: dict):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def fmt_scope_lines(scope_str: str):
    s = (scope_str or "").strip()
    if not s:
        return ["N/A"]

    if SCOPE_MODE == "OFF":
        return []

    scope_map = {
        "user-read-playback-state": "PLAYBACK_STATE",
        "user-read-currently-playing": "NOW_PLAYING",
        "user-read-recently-played": "RECENT_ACTIVITY",
    }

    tokens = [scope_map.get(x, x.upper()) for x in s.split()]

    if SCOPE_MODE == "COMPACT":
        return [" | ".join(tokens)]

    # WRAP (one token per line; clean + aligned)
    # NOTE: This is intentionally NOT word-wrapped mid-token; it's a telemetry list.
    return tokens

def classify_sitrep(status: str, playback_state: str, api_ok: bool):
    if not api_ok:
        return "RED"
    if status == "PLAYING" and playback_state.startswith("ONLINE"):
        return "GREEN"
    if status in ("IDLE", "UNKNOWN"):
        return "AMBER"
    return "AMBER"

def rewrite_readme_block(new_block: str):
    with open(README_PATH, "r", encoding="utf-8") as f:
        md = f.read()

    pattern = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), re.S)
    if not pattern.search(md):
        raise RuntimeError(f"Markers not found in README: {MARKER_START} ... {MARKER_END}")

    replacement = f"{MARKER_START}\n```text\n{new_block.rstrip()}\n```\n{MARKER_END}"
    md2 = pattern.sub(replacement, md)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(md2)

# =============================================================================
# Main telemetry build
# =============================================================================

def build_report():
    now = utc_now()
    now_s = utc_iso(now)

    # state for deltas
    prev = load_state() if WRITE_STATE_FILE else {}
    prev_track = prev.get("last_track", "")
    prev_last_played = prev.get("last_played_utc", "")
    prev_status = prev.get("status", "")
    prev_report_ts = prev.get("report_generated_utc", "")

    # acquire token
    token, scope = spotify_access_token()

    # current playback
    cur = fetch_currently_playing(token)
    api_http = cur.get("http", -1)
    api_ok = (api_http in (200, 204))

    status = "UNKNOWN"
    playback_state = "UNKNOWN"
    last_activity_type = "UNKNOWN"

    now_track_obj = None
    now_track_name = "N/A"  # telemetry-only default

    if api_http == 200 and isinstance(cur.get("data"), dict):
        d = cur["data"]
        is_playing = d.get("is_playing")
        status = "PLAYING" if is_playing else "IDLE"
        playback_state = "ONLINE (active session)" if is_playing else "OFFLINE (no active session)"
        last_activity_type = "PLAYBACK_ACTIVE" if is_playing else "PLAYBACK_INACTIVE"

        item = d.get("item") or {}
        now_track_obj = parse_track_item(item)
        if is_playing and now_track_obj:
            now_track_name = f"{now_track_obj['artist']} — {now_track_obj['title']}"
        else:
            now_track_name = "N/A"

    elif api_http == 204:
        status = "IDLE"
        playback_state = "OFFLINE (no active session)"
        last_activity_type = "NO_CONTENT_204"
        now_track_name = "N/A"
    else:
        status = "UNKNOWN"
        playback_state = "UNKNOWN"
        last_activity_type = "API_ERROR"
        now_track_name = "N/A"

    # recently played (for last known track)
    recent_code, recent_payload = fetch_recently_played(token, limit=50)
    recent_ok = (recent_code == 200 and isinstance(recent_payload, dict))

    last_track_name = "-"
    last_played_utc = ""
    last_track_obj = None

    if recent_ok:
        items = recent_payload.get("items") or []
        if items:
            it0 = items[0]
            played_at = it0.get("played_at") or ""
            tr = it0.get("track") or {}
            last_track_obj = parse_track_item(tr)
            if last_track_obj:
                last_track_name = f"{last_track_obj['artist']} — {last_track_obj['title']}"
            last_played_utc = played_at.replace(".000Z", "Z") if played_at else ""
            if last_played_utc and last_played_utc.endswith("Z"):
                try:
                    dtp = datetime.fromisoformat(last_played_utc.replace("Z", "+00:00"))
                    last_played_utc = utc_iso(dtp)
                except Exception:
                    pass

    # time since last play
    time_since_last_play = "N/A"
    telemetry_age = "N/A"
    if last_played_utc:
        try:
            last_dt = datetime.fromisoformat(last_played_utc.replace("Z", "+00:00"))
            delta = (now - last_dt).total_seconds()
            time_since_last_play = fmt_hms(delta)
            telemetry_age = fmt_hms(delta)
        except Exception:
            pass

    # deltas since last report
    def delta_str(prev_val, new_val, first_label="N/A (first report)"):
        if not prev_val:
            return first_label
        if prev_val == new_val:
            return "NO CHANGE"
        return f"{prev_val} → {new_val}"

    d_track = delta_str(prev_track, last_track_name)
    d_last  = delta_str(prev_last_played, last_played_utc)
    d_stat  = delta_str(prev_status, status)

    d_time = "N/A (first report)"
    if prev_report_ts:
        try:
            pdt = datetime.fromisoformat(prev_report_ts.replace("Z", "+00:00"))
            d_time = fmt_hms((now - pdt).total_seconds())
        except Exception:
            d_time = "N/A"

    # Daily SITREP (last 24h)
    daily_tracks = None
    dominant_artist_24h = None
    daily_pattern = None
    daily_status = None

    if SHOW_DAILY_SITREP and recent_ok:
        cutoff = now - timedelta(hours=24)
        cnt = 0
        artist_counts = {}
        for it in (recent_payload.get("items") or []):
            pa = it.get("played_at") or ""
            try:
                dtp = datetime.fromisoformat(pa.replace("Z", "+00:00"))
            except Exception:
                continue
            if dtp < cutoff:
                continue
            cnt += 1
            tr = it.get("track") or {}
            a0 = ((tr.get("artists") or [{}])[0]).get("name") or ""
            if a0:
                artist_counts[a0] = artist_counts.get(a0, 0) + 1

        daily_tracks = cnt
        if artist_counts:
            dominant_artist_24h = max(artist_counts.items(), key=lambda x: x[1])[0]

        if cnt >= 25:
            daily_status = "HIGH"
            daily_pattern = "Sustained operational tempo"
        elif cnt >= 10:
            daily_status = "MEDIUM"
            daily_pattern = "Regular cadence"
        elif cnt >= 1:
            daily_status = "LOW"
            daily_pattern = "Light activity"
        else:
            daily_status = "NONE"
            daily_pattern = "No activity"

    # Weekly summary
    week_window_start = now - timedelta(days=7)
    weekly_total = None
    dominant_artist_week = None
    cadence = None

    if SHOW_WEEKLY_SUMMARY and recent_ok:
        cnt = 0
        artist_counts = {}
        for it in (recent_payload.get("items") or []):
            pa = it.get("played_at") or ""
            try:
                dtp = datetime.fromisoformat(pa.replace("Z", "+00:00"))
            except Exception:
                continue
            if dtp < week_window_start:
                continue
            cnt += 1
            tr = it.get("track") or {}
            a0 = ((tr.get("artists") or [{}])[0]).get("name") or ""
            if a0:
                artist_counts[a0] = artist_counts.get(a0, 0) + 1

        weekly_total = cnt
        if artist_counts:
            dominant_artist_week = max(artist_counts.items(), key=lambda x: x[1])[0]

        if cnt >= 80:
            cadence = "VERY HIGH"
        elif cnt >= 40:
            cadence = "HIGH"
        elif cnt >= 15:
            cadence = "MEDIUM"
        elif cnt >= 1:
            cadence = "LOW"
        else:
            cadence = "NONE"

    # Compute SITREP
    sitrep = classify_sitrep(status, playback_state, api_ok and recent_ok)

    # Build output
    out = []
    out.append("SPOTIFY TELEMETRY — CLI FEED (Spotify ©)")
    out.append("------------------------------------------------------------")

    if SHOW_HEADER_META:
        out.append("Telemetry source          : Spotify Developer Platform — Playback Telemetry ©")
        out.append("Acquisition mode          : OAuth2 / automated workflow")
        out.append("Snapshot type             : Last-known playback state")
        out.append(f"Observation window        : {fmt_hms(OBS_WINDOW_SECONDS)}")
        out.append("------------------------------------------------------------")

    if SHOW_STATUS_BLOCK:
        out.append(f"Status                    : {status}")
        out.append(f"Playback state            : {playback_state}")
        out.append(f"SITREP                    : {sitrep}")
        out.append("------------------------------------------------------------")

    if SHOW_TRACK_BLOCK:
        # TELEMETRY-ONLY: no UI commentary
        out.append(f"Now playing               : {now_track_name}")
        out.append(f"Last played               : {last_track_name}")
        out.append(f"Last played (UTC)         : {last_played_utc or 'N/A'}")
        out.append(f"Last activity type        : {last_activity_type}")
        out.append("------------------------------------------------------------")

    if SHOW_DELTAS_BLOCK:
        out.append(f"Δ track (since last)      : {d_track}")
        out.append(f"Δ last played (since last): {d_last}")
        out.append(f"Δ status (since last)     : {d_stat}")
        out.append("------------------------------------------------------------")

    if SHOW_TIME_BLOCK:
        out.append(f"Time since last play      : {time_since_last_play}")
        out.append(f"Telemetry age             : {telemetry_age}")
        out.append(f"Δ time (since last report): {d_time}")
        out.append("------------------------------------------------------------")

    if SHOW_API_BLOCK:
        if api_http == 200:
            api_class = "200 OK"
        elif api_http == 204:
            api_class = "204 NO CONTENT"
        elif api_http == -1:
            api_class = "NETWORK/EXCEPTION"
        else:
            api_class = f"{api_http} ERROR"

        out.append(f"API response class        : {api_class}")
        out.append(f"API condition             : {'NORMAL' if (api_ok and recent_ok) else 'DEGRADED'}")

        # Authorization scope (formatted, aligned, not ugly)
        scope_lines = fmt_scope_lines(scope)
        if SCOPE_MODE != "OFF" and scope_lines:
            if SCOPE_MODE == "COMPACT":
                out.append(f"Authorization scope       : {scope_lines[0]}")
            else:
                # WRAP mode: one token per line, aligned
                out.append(f"Authorization scope       : {scope_lines[0]}")
                for ln in scope_lines[1:]:
                    out.append(f"                           {ln}")

        out.append("------------------------------------------------------------")

    if SHOW_INTEGRITY_BLOCK:
        integrity = "OK" if (api_ok and recent_ok and last_track_name != "-") else "DEGRADED"
        confidence = "HIGH" if integrity == "OK" else "MEDIUM"
        out.append(f"Data integrity            : {integrity}")
        out.append(f"Confidence level          : {confidence}")
        out.append("------------------------------------------------------------")

    if SHOW_DAILY_SITREP:
        out.append("DAILY SPOTIFY SITREP")
        out.append("------------------------------------------------------------")
        out.append(f"Tracks played (last 24h)  : {daily_tracks if daily_tracks is not None else 'N/A'}")
        out.append(f"Dominant artist           : {dominant_artist_24h or 'N/A'}")
        out.append(f"Listening pattern         : {daily_pattern or 'N/A'}")
        out.append(f"Daily activity status     : {daily_status or 'N/A'}")
        out.append("------------------------------------------------------------")

    if SHOW_WEEKLY_SUMMARY:
        out.append("WEEKLY CADENCE SUMMARY")
        out.append("------------------------------------------------------------")
        out.append(f"Week window (UTC)         : {utc_iso(week_window_start)} → {now_s}")
        out.append(f"Total tracks played       : {weekly_total if weekly_total is not None else 'N/A'}")
        out.append(f"Dominant artist           : {dominant_artist_week or 'N/A'}")
        out.append(f"Cadence classification    : {cadence or 'N/A'}")
        out.append("------------------------------------------------------------")

    out.append(f"Report generated (UTC)    : {now_s}")

    # state update
    if WRITE_STATE_FILE:
        save_state({
            "report_generated_utc": now_s,
            "status": status,
            "last_track": last_track_name,
            "last_played_utc": last_played_utc,
            "sitrep": sitrep,
        })

    return "\n".join(out)

def main():
    report = build_report()
    rewrite_readme_block(report)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        print(msg, file=sys.stderr)

        if FAIL_SAFE_DO_NOT_BREAK_README:
            print("FAIL-SAFE: preserving existing README telemetry block.", file=sys.stderr)
            sys.exit(0)

        sys.exit(1)
