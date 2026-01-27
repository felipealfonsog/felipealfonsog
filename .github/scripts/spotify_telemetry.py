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
from zoneinfo import ZoneInfo

# =============================================================================
# TOGGLES (set True/False) — keep these at top, clear and surgical
# =============================================================================

# ---- Master blocks (README output sections) ----
SHOW_HEADER_META          = True
SHOW_STATUS_BLOCK         = True
SHOW_DEVICE_BLOCK         = True
SHOW_TRACK_BLOCK          = True
SHOW_DELTAS_BLOCK         = True
SHOW_TIME_BLOCK           = True
SHOW_API_BLOCK            = True
SHOW_INTEGRITY_BLOCK      = True
SHOW_DAILY_SITREP         = True
SHOW_WEEKLY_SUMMARY       = True

# ---- Device privacy / details ----
SHOW_DEVICE_NAME          = True   # <-- your requested toggle (type stays ON)

# ---- Extra telemetry (derived from recently-played) ----
SHOW_GENRE_INTEL          = True    # inferred via artist profiles (needs extra API calls, cached)
SHOW_HOURLY_HEATMAP       = True    # listening hours histogram (local time)
SHOW_SESSION_ESTIMATES    = True    # inferred sessions from gaps between plays

# ---- Formatting sub-toggles ----
SCOPE_MODE                = "COMPACT"   # "WRAP" | "COMPACT" | "OFF"
WRAP_WIDTH                = 34          # for WRAP mode (if used)
LOCAL_TIMEZONE            = "America/Santiago"  # hour histogram display (telemetry only)

# ---- Behavior toggles ----
FAIL_SAFE_DO_NOT_BREAK_README = True   # if Spotify fails, keep README as-is and exit 0
WRITE_STATE_FILE              = True   # store last report for deltas
OBS_WINDOW_SECONDS            = 30 * 60 # observation window label (telemetry narrative)

# ---- Heuristics / safety caps ----
SESSION_GAP_MINUTES       = 25     # gap threshold => new "session" (inferred)
MAX_RECENT_ITEMS          = 50     # keep 50 (Spotify limit with your call)
MAX_ARTIST_LOOKUPS        = 80     # safety cap per run (cache reduces this a lot)

# ---- Volume formatting ----
SHOW_VOLUME_BAR           = True
VOLUME_BAR_WIDTH          = 12     # how many blocks to draw (visual density)

# =============================================================================
# Config / files
# =============================================================================

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

AUTH_URL      = "https://accounts.spotify.com/api/token"
CURRENT_URL   = "https://api.spotify.com/v1/me/player/currently-playing"
PLAYER_URL    = "https://api.spotify.com/v1/me/player"
RECENT_URL    = "https://api.spotify.com/v1/me/player/recently-played?limit=50"

README_PATH   = "README.md"
MARKER_START  = "<!-- SPOTIFY_TEL:START -->"
MARKER_END    = "<!-- SPOTIFY_TEL:END -->"

STATE_DIR     = ".github/state"
STATE_FILE    = os.path.join(STATE_DIR, "spotify_last_report.json")
ARTIST_CACHE_KEY = "artist_genre_cache"

# =============================================================================
# Helpers
# =============================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def utc_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%SZ")

def parse_iso_z(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

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

def local_tz():
    try:
        return ZoneInfo(LOCAL_TIMEZONE)
    except Exception:
        return timezone.utc

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

    code, _, payload = http_json(
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

def fetch_json_endpoint(url: str, token: str, timeout: int = 15):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
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

def fetch_currently_playing(token: str):
    return fetch_json_endpoint(CURRENT_URL, token, timeout=15)

def fetch_player_state(token: str):
    # This is the key fix: device + volume live here.
    return fetch_json_endpoint(PLAYER_URL, token, timeout=15)

def fetch_recently_played(token: str, limit: int = 50):
    url = "https://api.spotify.com/v1/me/player/recently-played?limit=" + str(limit)
    code, _, payload = http_json(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
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
        "artist_ids": [a.get("id") for a in artists if a.get("id")],
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

def classify_sitrep(status: str, playback_state: str, api_ok: bool):
    if not api_ok:
        return "RED"
    if status == "PLAYING" and playback_state.startswith("ONLINE"):
        return "GREEN"
    if status in ("IDLE", "UNKNOWN"):
        return "AMBER"
    return "AMBER"

def fmt_scope_lines(scope_str: str):
    s = (scope_str or "").strip()
    if not s or SCOPE_MODE == "OFF":
        return []

    scope_map = {
        "user-read-playback-state": "PLAYBACK_STATE",
        "user-read-currently-playing": "NOW_PLAYING",
        "user-read-recently-played": "RECENT_ACTIVITY",
        "user-top-read": "TOP_READ",
        "playlist-read-private": "PLAYLIST_PRIVATE",
        "playlist-read-collaborative": "PLAYLIST_COLLAB",
    }
    tokens = [scope_map.get(x, x.upper()) for x in s.split()]

    if SCOPE_MODE == "COMPACT":
        return [" | ".join(tokens)]

    # WRAP: clean telemetry wrap
    lines = []
    cur = ""
    for t in tokens:
        if not cur:
            cur = t
        elif len(cur) + 3 + len(t) <= WRAP_WIDTH:
            cur += " | " + t
        else:
            lines.append(cur)
            cur = t
    if cur:
        lines.append(cur)
    return lines

def fetch_artist(token: str, artist_id: str):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    code, _, payload = http_json(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    return code, payload

def get_artist_genres(token: str, artist_id: str, state: dict, lookups_counter: dict):
    cache = state.get(ARTIST_CACHE_KEY) or {}
    if artist_id in cache:
        return cache.get(artist_id) or []

    lookups_counter["n"] += 1
    if lookups_counter["n"] > MAX_ARTIST_LOOKUPS:
        return []

    code, payload = fetch_artist(token, artist_id)
    if code != 200 or not isinstance(payload, dict):
        return []

    genres = payload.get("genres") or []
    cache[artist_id] = genres
    state[ARTIST_CACHE_KEY] = cache
    return genres

def topk(lst, k=6):
    if not lst:
        return []
    counts = {}
    for x in lst:
        x = (x or "").strip().lower()
        if not x:
            continue
        counts[x] = counts.get(x, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:k]

def peak_hour(hist):
    if not hist or max(hist) == 0:
        return "N/A"
    h = max(range(24), key=lambda i: hist[i])
    return f"{h:02d}:00"

def heatmap_line(hist):
    if not hist or max(hist) == 0:
        return "N/A"
    m = max(hist)
    chars = " ▁▂▃▄▅▆▇█"
    out = []
    for v in hist:
        idx = int(round((v / m) * (len(chars)-1)))
        out.append(chars[clamp(idx, 0, len(chars)-1)])
    return "".join(out)

def infer_sessions(dts):
    if not dts:
        return 0, None
    dts = sorted(dts)
    gap_s = SESSION_GAP_MINUTES * 60
    sessions = 1
    gaps = []
    for i in range(1, len(dts)):
        delta = (dts[i] - dts[i-1]).total_seconds()
        gaps.append(delta)
        if delta > gap_s:
            sessions += 1
    avg_gap = (sum(gaps)/len(gaps)) if gaps else None
    return sessions, avg_gap

def volume_bar(percent: int | None) -> str:
    if percent is None:
        return "-"
    p = clamp(int(percent), 0, 100)
    # map to spark blocks; denser than heatmap
    chars = " ▁▂▃▄▅▆▇█"
    filled_steps = int(round((p / 100) * VOLUME_BAR_WIDTH))
    if filled_steps <= 0:
        return chars[1] * VOLUME_BAR_WIDTH
    # build by ramping levels (visual “signal” look)
    out = []
    for i in range(VOLUME_BAR_WIDTH):
        if i < filled_steps:
            level = int(round(((i + 1) / VOLUME_BAR_WIDTH) * (len(chars)-1)))
            out.append(chars[clamp(level, 1, len(chars)-1)])
        else:
            out.append(" ")
    return "".join(out).rstrip() or "-"

# =============================================================================
# Main telemetry build
# =============================================================================

def build_report():
    now = utc_now()
    now_s = utc_iso(now)

    # state for deltas + caches
    prev = load_state() if WRITE_STATE_FILE else {}
    mutable_state = dict(prev)

    prev_track = prev.get("last_track", "")
    prev_last_played = prev.get("last_played_utc", "")
    prev_status = prev.get("status", "")
    prev_report_ts = prev.get("report_generated_utc", "")

    # acquire token
    token, scope = spotify_access_token()

    # 1) PLAYER STATE (device + volume + active session truth)
    player = fetch_player_state(token)
    player_http = player.get("http", -1)
    player_data = player.get("data") if isinstance(player.get("data"), dict) else None

    # This is the authoritative "session exists" check
    has_active_session = (player_http == 200 and player_data is not None and isinstance(player_data.get("device"), dict))

    device_type = "N/A"
    device_name = "N/A"
    volume_percent = None

    volume_telemetry = "NO ACTIVE SESSION"
    if has_active_session:
        dev = player_data.get("device") or {}
        device_type = dev.get("type") or "N/A"
        device_name = dev.get("name") or "N/A"
        volume_percent = dev.get("volume_percent", None)

        if volume_percent is None:
            volume_telemetry = "NOT EXPOSED BY DEVICE"
        else:
            volume_telemetry = "OK"

    # 2) CURRENTLY PLAYING (track truth)
    cur = fetch_currently_playing(token)
    api_http = cur.get("http", -1)
    api_ok_current = (api_http in (200, 204))

    status = "UNKNOWN"
    playback_state = "UNKNOWN"
    last_activity_type = "UNKNOWN"
    now_track_name = "N/A"

    if has_active_session:
        # if player exists, we can trust playback_state from it
        is_playing = bool(player_data.get("is_playing"))
        status = "PLAYING" if is_playing else "IDLE"
        playback_state = "ONLINE (active session)" if is_playing else "OFFLINE (no active session)"
        last_activity_type = "PLAYBACK_ACTIVE" if is_playing else "PLAYBACK_INACTIVE"
    else:
        # no session
        status = "IDLE"
        playback_state = "OFFLINE (no active session)"
        last_activity_type = "NO_ACTIVE_SESSION"

    # Now playing track name
    if api_http == 200 and isinstance(cur.get("data"), dict):
        d = cur["data"]
        is_playing = bool(d.get("is_playing"))
        item = d.get("item") or {}
        now_track_obj = parse_track_item(item)
        if is_playing and now_track_obj:
            now_track_name = f"{now_track_obj['artist']} — {now_track_obj['title']}"
        else:
            now_track_name = "N/A"

    # recently played
    recent_code, recent_payload = fetch_recently_played(token, limit=MAX_RECENT_ITEMS)
    recent_ok = (recent_code == 200 and isinstance(recent_payload, dict))

    last_track_name = "-"
    last_played_utc = ""
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
                dtp = parse_iso_z(last_played_utc)
                if dtp:
                    last_played_utc = utc_iso(dtp)

    # time since last play
    time_since_last_play = "N/A"
    telemetry_age = "N/A"
    if last_played_utc:
        last_dt = parse_iso_z(last_played_utc)
        if last_dt:
            delta = (now - last_dt).total_seconds()
            time_since_last_play = fmt_hms(delta)
            telemetry_age = fmt_hms(delta)

    # deltas
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
        pdt = parse_iso_z(prev_report_ts)
        if pdt:
            d_time = fmt_hms((now - pdt).total_seconds())

    # Derived telemetry
    tz = local_tz()
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d  = now - timedelta(days=7)

    genre_24h = []
    genre_7d  = []
    artist_lookup_counter = {"n": 0}

    hour_hist_24h = [0] * 24
    hour_hist_7d  = [0] * 24

    played_times_24h = []
    played_times_7d  = []

    daily_tracks = None
    dominant_artist_24h = None
    daily_pattern = None
    daily_status = None

    weekly_total = None
    dominant_artist_week = None
    cadence = None
    week_window_start = now - timedelta(days=7)

    if recent_ok:
        items = recent_payload.get("items") or []
        cnt24 = 0
        cnt7  = 0
        artist_counts_24h = {}
        artist_counts_7d  = {}

        for it in items:
            pa = it.get("played_at") or ""
            dtp = parse_iso_z(pa)
            if not dtp:
                continue

            local_hour = dtp.astimezone(tz).hour

            if dtp >= cutoff_7d:
                hour_hist_7d[local_hour] += 1
                played_times_7d.append(dtp)
                cnt7 += 1

            if dtp >= cutoff_24h:
                hour_hist_24h[local_hour] += 1
                played_times_24h.append(dtp)
                cnt24 += 1

            tr = it.get("track") or {}
            artists = tr.get("artists") or []
            a0 = (artists[0].get("name") if artists else "") or ""

            if dtp >= cutoff_24h and a0:
                artist_counts_24h[a0] = artist_counts_24h.get(a0, 0) + 1

            if dtp >= cutoff_7d and a0:
                artist_counts_7d[a0] = artist_counts_7d.get(a0, 0) + 1

            if SHOW_GENRE_INTEL:
                parsed = parse_track_item(tr)
                if parsed:
                    for aid in parsed.get("artist_ids") or []:
                        g = get_artist_genres(token, aid, mutable_state, artist_lookup_counter)
                        if dtp >= cutoff_24h:
                            genre_24h.extend(g)
                        if dtp >= cutoff_7d:
                            genre_7d.extend(g)

        if SHOW_DAILY_SITREP:
            daily_tracks = cnt24
            if artist_counts_24h:
                dominant_artist_24h = max(artist_counts_24h.items(), key=lambda x: x[1])[0]

            if cnt24 >= 25:
                daily_status = "HIGH"
                daily_pattern = "Sustained operational tempo"
            elif cnt24 >= 10:
                daily_status = "MEDIUM"
                daily_pattern = "Regular cadence"
            elif cnt24 >= 1:
                daily_status = "LOW"
                daily_pattern = "Light activity"
            else:
                daily_status = "NONE"
                daily_pattern = "No activity"

        if SHOW_WEEKLY_SUMMARY:
            weekly_total = cnt7
            if artist_counts_7d:
                dominant_artist_week = max(artist_counts_7d.items(), key=lambda x: x[1])[0]

            if cnt7 >= 80:
                cadence = "VERY HIGH"
            elif cnt7 >= 40:
                cadence = "HIGH"
            elif cnt7 >= 15:
                cadence = "MEDIUM"
            elif cnt7 >= 1:
                cadence = "LOW"
            else:
                cadence = "NONE"

    # sessions
    sessions_24h = 0
    sessions_7d  = 0
    avg_session_gap_7d = "N/A"
    if SHOW_SESSION_ESTIMATES:
        sessions_24h, _ = infer_sessions(played_times_24h)
        sessions_7d, avg_gap = infer_sessions(played_times_7d)
        avg_session_gap_7d = fmt_hms(avg_gap) if avg_gap is not None else "N/A"

    # API OK = player ok + current ok + recent ok
    api_ok = (player_http in (200, 204)) and api_ok_current and recent_ok
    sitrep = classify_sitrep(status, playback_state, api_ok)

    # API response class (focus on CURRENT endpoint, since that’s what most people expect)
    if api_http == 200:
        api_class = "200 OK"
    elif api_http == 204:
        api_class = "204 NO CONTENT"
    elif api_http == -1:
        api_class = "NETWORK/EXCEPTION"
    else:
        api_class = f"{api_http} ERROR"

    integrity = "OK" if (api_ok and last_track_name != "-") else "DEGRADED"
    confidence = "HIGH" if integrity == "OK" else "MEDIUM"

    # Volume output
    if not has_active_session or status != "PLAYING":
        vol_str = "N/A"
        vol_bar = "-"
        vol_tel = "NO ACTIVE SESSION"
    else:
        if volume_percent is None:
            vol_str = "N/A"
            vol_bar = "-"
            vol_tel = "NOT EXPOSED BY DEVICE"
        else:
            vol_str = f"{int(volume_percent)}%"
            vol_bar = volume_bar(int(volume_percent)) if SHOW_VOLUME_BAR else "-"
            vol_tel = "OK"

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
        # Your requested exact OFFLINE/IDLE when no session:
        out.append(f"Playback state            : {playback_state}")
        out.append(f"Status                    : {status}")
        out.append(f"SITREP                    : {sitrep}")
        out.append("------------------------------------------------------------")

    if SHOW_DEVICE_BLOCK:
        out.append("PLAYBACK DEVICE (Spotify)")
        out.append("------------------------------------------------------------")
        out.append(f"Device type               : {device_type or 'N/A'}")
        if SHOW_DEVICE_NAME:
            out.append(f"Device name               : {device_name or 'N/A'}")

        out.append(f"Volume                    : {vol_str}")
        out.append(f"Volume telemetry          : {vol_tel}")
        if SHOW_VOLUME_BAR and vol_bar and vol_bar != "-":
            out.append(f"Volume bar                : {vol_bar}")
        out.append("------------------------------------------------------------")

    if SHOW_TRACK_BLOCK:
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
        out.append(f"API response class        : {api_class}")
        out.append(f"API condition             : {'NORMAL' if api_ok else 'DEGRADED'}")

        scope_lines = fmt_scope_lines(scope)
        if scope_lines:
            if SCOPE_MODE == "COMPACT":
                out.append(f"Authorization scope       : {scope_lines[0]}")
            else:
                out.append(f"Authorization scope       : {scope_lines[0]}")
                for ln in scope_lines[1:]:
                    out.append(f"                           {ln}")

        # Helpful to debug why volume/device may be N/A
        if player_http == 200:
            out.append(f"Player endpoint           : 200 OK")
        elif player_http == 204:
            out.append(f"Player endpoint           : 204 NO CONTENT")
        elif player_http == -1:
            out.append(f"Player endpoint           : NETWORK/EXCEPTION")
        else:
            out.append(f"Player endpoint           : {player_http} ERROR")

        out.append("------------------------------------------------------------")

    if SHOW_INTEGRITY_BLOCK:
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

    if SHOW_HOURLY_HEATMAP:
        out.append("LISTENING HOURS (local time)")
        out.append("------------------------------------------------------------")
        out.append(f"Local timezone            : {LOCAL_TIMEZONE}")
        out.append(f"Peak hour (24h)           : {peak_hour(hour_hist_24h)}")
        out.append(f"Peak hour (7d)            : {peak_hour(hour_hist_7d)}")
        out.append(f"Heatmap (24h)             : {heatmap_line(hour_hist_24h)}")
        out.append(f"Heatmap (7d)              : {heatmap_line(hour_hist_7d)}")
        out.append("------------------------------------------------------------")

    if SHOW_SESSION_ESTIMATES:
        out.append("SESSION ESTIMATES (inferred)")
        out.append("------------------------------------------------------------")
        out.append(f"Session gap threshold     : {SESSION_GAP_MINUTES} minutes")
        out.append(f"Sessions (24h)            : {sessions_24h if sessions_24h else 'N/A'}")
        out.append(f"Sessions (7d)             : {sessions_7d if sessions_7d else 'N/A'}")
        out.append(f"Avg inter-play gap (7d)   : {avg_session_gap_7d}")
        out.append("------------------------------------------------------------")

    if SHOW_GENRE_INTEL:
        out.append("GENRE INTEL (inferred)")
        out.append("------------------------------------------------------------")
        t24 = topk(genre_24h, 6)
        t7  = topk(genre_7d,  6)
        out.append("Top genres (24h)          : " + (" | ".join([f"{g}({c})" for g, c in t24]) if t24 else "N/A"))
        out.append("Top genres (7d)           : " + (" | ".join([f"{g}({c})" for g, c in t7])  if t7 else "N/A"))
        out.append(f"Artist lookups (this run) : {artist_lookup_counter['n']} (cached)")
        out.append("------------------------------------------------------------")

    out.append(f"Report generated (UTC)    : {now_s}")

    if WRITE_STATE_FILE:
        mutable_state.update({
            "report_generated_utc": now_s,
            "status": status,
            "last_track": last_track_name,
            "last_played_utc": last_played_utc,
            "sitrep": sitrep,
        })
        save_state(mutable_state)

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
