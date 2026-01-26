#!/usr/bin/env python3
import base64
import json
import os
import sys
import time
import hashlib
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# ============================================================
# CONFIG TOGGLES (TURN ON/OFF SECTIONS + SUBSECTIONS)
# ============================================================

SHOW_HEADER_BLOCK         = True
SHOW_STATUS_BLOCK         = True
SHOW_TRACK_BLOCK          = True
SHOW_DELTAS_BLOCK         = True
SHOW_TIMING_BLOCK         = True
SHOW_API_BLOCK            = True
SHOW_INTEGRITY_BLOCK      = True
SHOW_DAILY_SITREP         = True
SHOW_WEEKLY_SUMMARY       = True

# Subsections (fine control)
SHOW_EVENT_SIGNATURE      = True
SHOW_TRACK_FINGERPRINT    = True
SHOW_CONTINUITY           = True
SHOW_CONFIDENCE           = True
SHOW_FALLBACK_LINES       = True
SHOW_CACHE_HINTS          = True

# Emphasis (bold) - only meaningful because we render via <pre> HTML
BOLD_NOW_PLAYING          = True
BOLD_LAST_PLAYED          = True
BOLD_DOMINANT_GENRE       = True
BOLD_PEAK_LISTENING_DAY   = True

# Observation/rollups windows
OBS_WINDOW_MINUTES        = 30
DAILY_WINDOW_HOURS        = 24
WEEKLY_WINDOW_DAYS        = 7

# Output/markers
README_PATH               = "README.md"
MARKER_START              = "<!-- SPOTIFY_TELEMETRY:START -->"
MARKER_END                = "<!-- SPOTIFY_TELEMETRY:END -->"

STATE_JSON_PATH           = "images/spotify_telemetry_state.json"  # committed cache
MIN_STATE_FIELDS          = ("last_report_utc",)

# Spotify endpoints
AUTH_URL                  = "https://accounts.spotify.com/api/token"
CURRENT_URL               = "https://api.spotify.com/v1/me/player/currently-playing"
RECENT_URL                = "https://api.spotify.com/v1/me/player/recently-played?limit=10"

CLIENT_ID                 = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET             = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN             = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

# ============================================================
# Helpers
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def fmt_utc(dt: datetime | None) -> str:
    if not dt:
        return "-"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def fmt_hms(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def html_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def bold_if(s: str, enabled: bool) -> str:
    s = html_escape(s)
    return f"<b>{s}</b>" if enabled else s

def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace").strip()
        if not raw:
            return r.getcode(), dict(r.headers), None
        return r.getcode(), dict(r.headers), json.loads(raw)

def load_state() -> dict:
    try:
        with open(STATE_JSON_PATH, "r", encoding="utf-8") as f:
            st = json.load(f)
        if not isinstance(st, dict):
            return {}
        return st
    except Exception:
        return {}

def save_state(st: dict):
    os.makedirs(os.path.dirname(STATE_JSON_PATH), exist_ok=True)
    with open(STATE_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2, sort_keys=True)

def replace_readme_block(md: str, new_block_html: str) -> str:
    if MARKER_START not in md or MARKER_END not in md:
        raise RuntimeError(f"Markers not found in README: {MARKER_START} ... {MARKER_END}")
    pre = md.split(MARKER_START, 1)[0] + MARKER_START
    post = md.split(MARKER_END, 1)[1]
    return pre + "\n" + new_block_html.rstrip() + "\n" + MARKER_END + post

# ============================================================
# Spotify
# ============================================================

def get_access_token() -> tuple[str, str]:
    """
    Returns (access_token, scope_string)
    """
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise RuntimeError("Missing Spotify secrets: SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIFY_REFRESH_TOKEN.")

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
        raise RuntimeError(f"Token endpoint error (HTTP {code}): {payload}")

    token = payload.get("access_token")
    scope = payload.get("scope", "")
    if not token:
        raise RuntimeError(f"No access_token in response: {payload}")
    return token, scope

def get_current_playback(access_token: str) -> tuple[str, dict | None]:
    """
    Returns (api_class, payload)
      - 204 => IDLE (no payload)
      - 200 => payload present
    """
    req = urllib.request.Request(
        CURRENT_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 204:
                return "204 NO CONTENT", None
            raw = r.read().decode("utf-8", "replace").strip()
            if not raw:
                return f"{r.status} EMPTY", None
            return f"{r.status} OK", json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return "204 NO CONTENT", None
        return f"{e.code} ERROR", None

def get_recent_tracks(access_token: str) -> tuple[str, list]:
    code, _, payload = http_json(
        RECENT_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=20,
    )
    if code >= 400 or not payload:
        return f"{code} ERROR", []
    items = payload.get("items") or []
    return f"{code} OK", items

# ============================================================
# Telemetry logic
# ============================================================

def track_str(artist: str, title: str) -> str:
    if not artist and not title:
        return "-"
    if not artist:
        return title
    if not title:
        return artist
    return f"{artist} — {title}"

def extract_now_playing(current_payload: dict | None) -> dict | None:
    if not current_payload:
        return None
    item = current_payload.get("item") or {}
    artists = item.get("artists") or []
    artist = ", ".join([a.get("name","") for a in artists if a.get("name")]).strip()
    title = (item.get("name") or "").strip()
    is_playing = bool(current_payload.get("is_playing"))
    progress_ms = current_payload.get("progress_ms")
    duration_ms = item.get("duration_ms")
    return {
        "is_playing": is_playing,
        "artist": artist,
        "title": title,
        "progress_ms": progress_ms,
        "duration_ms": duration_ms,
    }

def extract_last_played(recent_items: list) -> dict | None:
    if not recent_items:
        return None
    it = recent_items[0] or {}
    track = it.get("track") or {}
    artists = track.get("artists") or []
    artist = ", ".join([a.get("name","") for a in artists if a.get("name")]).strip()
    title = (track.get("name") or "").strip()
    played_at = it.get("played_at") or ""
    try:
        played_dt = datetime.fromisoformat(played_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        played_dt = None
    return {
        "artist": artist,
        "title": title,
        "played_at_raw": played_at,
        "played_at_dt": played_dt,
    }

def infer_activity_type(now_playing: dict | None, last_played: dict | None) -> str:
    if now_playing and now_playing.get("is_playing"):
        return "TRACK_PLAYING"
    if last_played and last_played.get("played_at_dt"):
        return "TRACK_END"
    return "UNKNOWN"

def fingerprint_track(s: str) -> str:
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return h[:8]

def sitrep(status: str, api_ok: bool) -> str:
    # GREEN: live playing + good api
    if status == "PLAYING" and api_ok:
        return "GREEN"
    # AMBER: idle/offline but api ok
    if status in ("IDLE", "OFFLINE") and api_ok:
        return "AMBER"
    # RED: no api / broken
    return "RED"

def confidence(telemetry_age_s: int | None, api_ok: bool) -> str:
    if not api_ok:
        return "LOW"
    if telemetry_age_s is None:
        return "MEDIUM"
    if telemetry_age_s <= 15 * 60:
        return "HIGH"
    if telemetry_age_s <= 60 * 60:
        return "MEDIUM"
    return "LOW"

def classify_cache_state(api_class: str) -> str:
    # Heuristic: if we get 204 often, GitHub caching isn't the reason; it's just no session.
    if api_class.startswith("200"):
        return "POSSIBLE HIT"
    return "N/A"

def daily_rollup(recent_items: list) -> dict:
    # naive rollup from recently-played window (limit=10) + timestamps
    # For a stable daily sitrep, you’d normally paginate, but we keep it lightweight.
    now = utc_now()
    cutoff = now - timedelta(hours=DAILY_WINDOW_HOURS)
    tracks = []
    for it in recent_items:
        p = it.get("played_at") or ""
        try:
            dt = datetime.fromisoformat(p.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue
        if dt < cutoff:
            continue
        tr = it.get("track") or {}
        artists = tr.get("artists") or []
        artist = ", ".join([a.get("name","") for a in artists if a.get("name")]).strip()
        title = (tr.get("name") or "").strip()
        tracks.append((dt, artist, title))

    tracks.sort(key=lambda x: x[0])
    tracks_played = len(tracks)

    # Very conservative “time” estimate: sum of track durations when available
    total_sec = 0
    artist_count = {}
    for it in recent_items:
        p = it.get("played_at") or ""
        try:
            dt = datetime.fromisoformat(p.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue
        if dt < cutoff:
            continue
        tr = it.get("track") or {}
        dur_ms = tr.get("duration_ms") or 0
        if isinstance(dur_ms, int) and dur_ms > 0:
            total_sec += dur_ms // 1000
        artists = tr.get("artists") or []
        artist = ", ".join([a.get("name","") for a in artists if a.get("name")]).strip() or "Unknown"
        artist_count[artist] = artist_count.get(artist, 0) + 1

    dominant_artist = max(artist_count, key=artist_count.get) if artist_count else "N/A"

    # Genre is not directly available from these endpoints; keep it honest.
    dominant_genre = "N/A (not exposed by endpoint)"

    # Pattern heuristic
    if tracks_played >= 12:
        pattern = "INTENSE"
        status = "HIGH"
    elif tracks_played >= 5:
        pattern = "FOCUSED"
        status = "MODERATE"
    elif tracks_played >= 1:
        pattern = "SPARSE"
        status = "LOW"
    else:
        pattern = "QUIET"
        status = "LOW"

    return {
        "tracks_played_today": tracks_played,
        "total_listening_time": fmt_hms(total_sec),
        "dominant_artist": dominant_artist,
        "dominant_genre": dominant_genre,
        "listening_pattern": pattern,
        "daily_activity_status": status,
    }

def weekly_rollup(recent_items: list) -> dict:
    # same limitation: not full pagination; still useful as “last 10 events” + time window
    now = utc_now()
    cutoff = now - timedelta(days=WEEKLY_WINDOW_DAYS)
    days = {}
    count = 0
    total_sec = 0

    for it in recent_items:
        p = it.get("played_at") or ""
        try:
            dt = datetime.fromisoformat(p.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue
        if dt < cutoff:
            continue

        count += 1
        day = dt.strftime("%A")
        days[day] = days.get(day, 0) + 1

        tr = it.get("track") or {}
        dur_ms = tr.get("duration_ms") or 0
        if isinstance(dur_ms, int) and dur_ms > 0:
            total_sec += dur_ms // 1000

    active_days = len(days)
    peak_day = max(days, key=days.get) if days else "N/A"

    # session length estimate: total time / max(1, count)
    avg_session = int(total_sec / max(1, count))
    avg_session_str = f"{max(1, avg_session)//60} min"

    if count >= 20:
        cadence = "HIGH"
        trend = "UP"
    elif count >= 8:
        cadence = "MODERATE"
        trend = "STABLE"
    elif count >= 1:
        cadence = "LOW"
        trend = "DOWN"
    else:
        cadence = "LOW"
        trend = "STABLE"

    # We can’t really compare vs last week without more history; keep it honest.
    trend_vs_last_week = "N/A (insufficient history)"

    return {
        "week_window": f"{(now - timedelta(days=WEEKLY_WINDOW_DAYS)).strftime('%Y-%m-%d')} → {now.strftime('%Y-%m-%d')}",
        "active_days": f"{active_days} / {WEEKLY_WINDOW_DAYS}",
        "total_tracks_played": count,
        "total_listening_time": fmt_hms(total_sec),
        "avg_session_length": avg_session_str,
        "peak_listening_day": peak_day,
        "cadence_classification": cadence,
        "trend_vs_last_week": trend_vs_last_week,
        "trend": trend,
    }

def main():
    # Load last state for deltas
    prev = load_state()

    report_dt = utc_now()
    report_utc = fmt_utc(report_dt)

    token, scope = get_access_token()
    api_class_current, current_payload = get_current_playback(token)
    api_class_recent, recent_items = get_recent_tracks(token)

    api_ok = api_class_recent.startswith("200") or api_class_current.startswith("200") or api_class_current.startswith("204")

    now_playing = extract_now_playing(current_payload)
    last_played = extract_last_played(recent_items)

    # Status logic
    if now_playing and now_playing.get("is_playing"):
        status = "PLAYING"
        playback_state = "ONLINE (active session)"
    else:
        # if 204 or is_playing false, treat as idle/offline
        status = "IDLE"
        playback_state = "OFFLINE (no active session)"

    activity_type = infer_activity_type(now_playing, last_played)

    # Now playing string
    if now_playing and now_playing.get("is_playing"):
        now_str = track_str(now_playing.get("artist",""), now_playing.get("title",""))
    else:
        now_str = "-"

    # Last played string/time
    last_str = "-"
    last_dt = None
    if last_played:
        last_str = track_str(last_played.get("artist",""), last_played.get("title",""))
        last_dt = last_played.get("played_at_dt")

    # time since last play
    if last_dt:
        since_last_play_s = int((report_dt - last_dt).total_seconds())
        since_last_play = fmt_hms(since_last_play_s)
        telemetry_age_s = since_last_play_s  # last known playback state age (proxy)
        telemetry_age = fmt_hms(telemetry_age_s)
    else:
        since_last_play_s = None
        since_last_play = "N/A"
        telemetry_age_s = None
        telemetry_age = "N/A"

    # deltas
    prev_track_fp = prev.get("last_track_fp")
    curr_track_fp = fingerprint_track(last_str) if last_str != "-" else None

    delta_track = "N/A (first report)" if not prev_track_fp else ("CHANGED" if curr_track_fp != prev_track_fp else "UNCHANGED")
    delta_last_played = "N/A (first report)"
    delta_status = "N/A (first report)"

    if prev.get("last_played_utc") and last_dt:
        delta_last_played = "CHANGED" if fmt_utc(last_dt) != prev.get("last_played_utc") else "UNCHANGED"

    if prev.get("status"):
        delta_status = "CHANGED" if status != prev.get("status") else "UNCHANGED"

    # API / integrity
    api_condition = "NORMAL" if api_ok else "DEGRADED"
    data_integrity = "OK" if (api_ok and (last_str != "-" or now_str != "-")) else ("PARTIAL" if api_ok else "UNKNOWN")
    cache_state = classify_cache_state(api_class_current if api_class_current else api_class_recent)
    fb_mode = "HOLD-LAST" if api_ok else "HOLD-LAST (API DEGRADED)"
    lkg = prev.get("last_known_good_snapshot_utc") or (fmt_utc(last_dt) if last_dt else "-")

    # Confidence
    conf = confidence(telemetry_age_s, api_ok)
    sr = sitrep(status if status else "OFFLINE", api_ok)

    # Rollups
    daily = daily_rollup(recent_items) if SHOW_DAILY_SITREP else None
    weekly = weekly_rollup(recent_items) if SHOW_WEEKLY_SUMMARY else None

    # Build CLI lines
    out = []
    title = "SPOTIFY TELEMETRY — CLI FEED (Spotify ©)"
    out.append(title)
    out.append("-" * 60)

    if SHOW_HEADER_BLOCK:
        out.append(f"{'Spotify Developer API Source':<26}: Spotify Web API")
        out.append(f"{'Acquisition mode':<26}: OAuth2 / automated workflow")
        out.append(f"{'Snapshot type':<26}: Last-known playback state")
        out.append(f"{'Observation window':<26}: {fmt_hms(OBS_WINDOW_MINUTES*60)}")
        out.append("-" * 60)

    if SHOW_STATUS_BLOCK:
        out.append(f"{'Status':<26}: {status}")
        out.append(f"{'Playback state':<26}: {playback_state}")
        out.append(f"{'Operational mode':<26}: {'ACTIVE' if status=='PLAYING' else 'PASSIVE'}")
        out.append(f"{'Session lifecycle':<26}: {'LIVE' if status=='PLAYING' else 'TERMINATED'}")
        out.append(f"{'SITREP':<26}: {sr}")
        out.append("-" * 60)

    if SHOW_TRACK_BLOCK:
        # Bold targets
        now_line = bold_if(now_str, BOLD_NOW_PLAYING)
        last_line = bold_if(last_str, BOLD_LAST_PLAYED)

        out.append(f"{'Now playing':<26}: {now_line}")
        out.append(f"{'Last played':<26}: {last_line}")
        out.append(f"{'Last played (UTC)':<26}: {fmt_utc(last_dt)}")
        out.append(f"{'Last activity type':<26}: {activity_type}")

        if SHOW_EVENT_SIGNATURE:
            out.append(f"{'Event signature':<26}: {activity_type}@UTC")

        if SHOW_TRACK_FINGERPRINT:
            fp = fingerprint_track(last_str) if last_str != "-" else "N/A"
            out.append(f"{'Track fingerprint':<26}: {fp}")

        out.append("-" * 60)

    if SHOW_DELTAS_BLOCK:
        out.append(f"{'Δ track (since last)':<26}: {delta_track}")
        out.append(f"{'Δ last played (since last)':<26}: {delta_last_played}")
        out.append(f"{'Δ status (since last)':<26}: {delta_status}")
        out.append("-" * 60)

    if SHOW_TIMING_BLOCK:
        out.append(f"{'Time since last play':<26}: {since_last_play}")
        out.append(f"{'Telemetry age':<26}: {telemetry_age}")

        if SHOW_CONTINUITY:
            continuity = "CONTINUOUS" if delta_track in ("UNCHANGED", "N/A (first report)") else "INTERRUPTED"
            cadence = "LOW"
            if daily and isinstance(daily.get("tracks_played_today",0), int):
                n = daily["tracks_played_today"]
                cadence = "HIGH" if n >= 12 else ("MODERATE" if n >= 5 else "LOW")
            out.append(f"{'Playback continuity':<26}: {continuity}")
            out.append(f"{'Activity cadence':<26}: {cadence}")

        out.append("-" * 60)

    if SHOW_API_BLOCK:
        out.append(f"{'API response class':<26}: {api_class_current} / {api_class_recent}")
        out.append(f"{'API condition':<26}: {api_condition}")
        out.append(f"{'Auth state':<26}: {'VALID' if api_ok else 'UNKNOWN'}")
        out.append(f"{'Token scope':<26}: {html_escape(scope) if scope else 'N/A'}")
        if SHOW_CACHE_HINTS:
            out.append(f"{'Cache state':<26}: {cache_state}")
        if SHOW_FALLBACK_LINES:
            out.append(f"{'Fallback mode':<26}: {fb_mode}")
            out.append(f"{'Last known good snapshot':<26}: {lkg}")
        out.append("-" * 60)

    if SHOW_INTEGRITY_BLOCK:
        out.append(f"{'Data integrity':<26}: {data_integrity}")
        if SHOW_CONFIDENCE:
            out.append(f"{'Confidence level':<26}: {conf}")
        out.append("-" * 60)

    if SHOW_DAILY_SITREP and daily:
        out.append("DAILY SPOTIFY SITREP")
        out.append("-" * 60)
        out.append(f"{'Tracks played today':<26}: {daily['tracks_played_today']}")
        out.append(f"{'Total listening time':<26}: {daily['total_listening_time']}")
        out.append(f"{'Dominant artist':<26}: {daily['dominant_artist']}")
        dg = bold_if(daily["dominant_genre"], BOLD_DOMINANT_GENRE)
        out.append(f"{'Dominant genre':<26}: {dg}")
        out.append(f"{'Listening pattern':<26}: {daily['listening_pattern']}")
        out.append(f"{'Daily activity status':<26}: {daily['daily_activity_status']}")
        out.append("-" * 60)

    if SHOW_WEEKLY_SUMMARY and weekly:
        out.append("WEEKLY CADENCE SUMMARY")
        out.append("-" * 60)
        out.append(f"{'Week window (UTC)':<26}: {weekly['week_window']}")
        out.append(f"{'Active days':<26}: {weekly['active_days']}")
        out.append(f"{'Total tracks played':<26}: {weekly['total_tracks_played']}")
        out.append(f"{'Total listening time':<26}: {weekly['total_listening_time']}")
        out.append(f"{'Average session length':<26}: {weekly['avg_session_length']}")
        pk = bold_if(weekly["peak_listening_day"], BOLD_PEAK_LISTENING_DAY)
        out.append(f"{'Peak listening day':<26}: {pk}")
        out.append(f"{'Cadence classification':<26}: {weekly['cadence_classification']}")
        out.append(f"{'Trend vs last week':<26}: {weekly['trend_vs_last_week']}")
        out.append("-" * 60)

    out.append(f"{'Report generated (UTC)':<26}: {report_utc}")

    # Wrap as HTML <pre> so bold works but layout stays CLI
    pre = "<pre>" + "\n".join(out) + "\n</pre>"

    # Update README block
    with open(README_PATH, "r", encoding="utf-8") as f:
        md = f.read()
    md2 = replace_readme_block(md, pre)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(md2)

    # Save state for deltas
    new_state = {
        "last_report_utc": report_utc,
        "status": status,
        "last_played_utc": fmt_utc(last_dt) if last_dt else "",
        "last_track_fp": fingerprint_track(last_str) if last_str != "-" else "",
        "last_known_good_snapshot_utc": fmt_utc(last_dt) if last_dt else (prev.get("last_known_good_snapshot_utc") or ""),
    }
    save_state(new_state)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
