#!/usr/bin/env python3
import base64
import json
import os
import re
import sys
import hashlib
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# ============================================================
# TOGGLES (sections + subsections)
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

SHOW_EVENT_SIGNATURE      = True
SHOW_TRACK_FINGERPRINT    = True
SHOW_CONTINUITY           = True
SHOW_CONFIDENCE           = True
SHOW_CACHE_HINTS          = True
SHOW_FALLBACK_LINES       = True

# Windows
DAILY_WINDOW_HOURS        = 24
WEEKLY_WINDOW_DAYS        = 7

# Output / markers
README_PATH               = "README.md"
MARKER_START              = "<!-- SPOTIFY_TELEMETRY:START -->"
MARKER_END                = "<!-- SPOTIFY_TELEMETRY:END -->"

STATE_JSON_PATH           = "images/spotify_telemetry_state.json"

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

def safe(s: str) -> str:
    # Keep it stable inside ```text```; avoid weird newlines/tabs
    return (s or "").replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()

def fingerprint(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]

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
        return st if isinstance(st, dict) else {}
    except Exception:
        return {}

def save_state(st: dict):
    os.makedirs(os.path.dirname(STATE_JSON_PATH), exist_ok=True)
    with open(STATE_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2, sort_keys=True)

def replace_block(md: str, new_block: str) -> str:
    # Robust regex replacement between markers
    pattern = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), re.S)
    if not pattern.search(md):
        raise RuntimeError(f"Markers not found: {MARKER_START} ... {MARKER_END}")
    return pattern.sub(MARKER_START + "\n" + new_block.rstrip() + "\n" + MARKER_END, md)

# ============================================================
# Spotify
# ============================================================

def get_access_token() -> tuple[str, str]:
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
    return f"{code} OK", payload.get("items") or []

# ============================================================
# Telemetry extraction
# ============================================================

def track_line(artist: str, title: str) -> str:
    artist = safe(artist)
    title = safe(title)
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
    artist = ", ".join([a.get("name","") for a in artists if a.get("name")])
    title = item.get("name") or ""
    return {
        "is_playing": bool(current_payload.get("is_playing")),
        "artist": artist,
        "title": title,
    }

def extract_last_played(recent_items: list) -> dict | None:
    if not recent_items:
        return None
    it = recent_items[0] or {}
    track = it.get("track") or {}
    artists = track.get("artists") or []
    artist = ", ".join([a.get("name","") for a in artists if a.get("name")])
    title = track.get("name") or ""
    played_at = it.get("played_at") or ""
    dt = None
    try:
        dt = datetime.fromisoformat(played_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        dt = None
    return {"artist": artist, "title": title, "played_at_dt": dt}

def sitrep(status: str, api_ok: bool) -> str:
    if status == "PLAYING" and api_ok:
        return "GREEN"
    if status in ("IDLE", "OFFLINE") and api_ok:
        return "AMBER"
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

def daily_rollup(recent_items: list) -> dict:
    now = utc_now()
    cutoff = now - timedelta(hours=DAILY_WINDOW_HOURS)

    count = 0
    artists = {}
    total_sec = 0

    for it in recent_items:
        played_at = (it.get("played_at") or "").strip()
        try:
            dt = datetime.fromisoformat(played_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue
        if dt < cutoff:
            continue

        count += 1
        tr = it.get("track") or {}
        dur_ms = tr.get("duration_ms") or 0
        if isinstance(dur_ms, int) and dur_ms > 0:
            total_sec += dur_ms // 1000

        arts = tr.get("artists") or []
        a = ", ".join([x.get("name","") for x in arts if x.get("name")]) or "Unknown"
        artists[a] = artists.get(a, 0) + 1

    dominant_artist = max(artists, key=artists.get) if artists else "N/A"
    dominant_genre = "N/A (not exposed by endpoint)"

    if count >= 12:
        pattern = "INTENSE"
    elif count >= 5:
        pattern = "FOCUSED"
    elif count >= 1:
        pattern = "SPARSE"
    else:
        pattern = "QUIET"

    return {
        "tracks": count,
        "time": fmt_hms(total_sec),
        "dominant_artist": dominant_artist,
        "dominant_genre": dominant_genre,
        "pattern": pattern,
    }

def weekly_rollup(recent_items: list) -> dict:
    # With limit=10 we keep it honest: a lightweight “cadence sample”
    days = {}
    for it in recent_items:
        played_at = (it.get("played_at") or "").strip()
        try:
            dt = datetime.fromisoformat(played_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue
        day = dt.strftime("%A")
        days[day] = days.get(day, 0) + 1

    peak_day = max(days, key=days.get) if days else "N/A"

    cadence = "LOW"
    if len(recent_items) >= 10:
        cadence = "MODERATE"
    if len(recent_items) >= 20:
        cadence = "HIGH"

    return {
        "peak_day": peak_day,
        "cadence": cadence,
        "trend_vs_last_week": "N/A (insufficient history)",
    }

# ============================================================
# Main
# ============================================================

def main():
    prev = load_state()
    report_dt = utc_now()

    token, scope = get_access_token()
    cur_class, cur_payload = get_current_playback(token)
    rec_class, rec_items = get_recent_tracks(token)

    api_ok = cur_class.startswith("200") or cur_class.startswith("204") or rec_class.startswith("200")

    nowp = extract_now_playing(cur_payload)
    last = extract_last_played(rec_items)

    if nowp and nowp.get("is_playing"):
        status = "PLAYING"
        playback_state = "ONLINE (active session)"
        now_line = track_line(nowp.get("artist",""), nowp.get("title",""))
    else:
        status = "IDLE"
        playback_state = "OFFLINE (no active session)"
        now_line = "-"

    last_line = "-"
    last_dt = None
    if last:
        last_line = track_line(last.get("artist",""), last.get("title",""))
        last_dt = last.get("played_at_dt")

    # Pseudo-bold emphasis: make key lines visually dominant
    now_line_emph  = f">> {now_line}" if now_line != "-" else "-"
    last_line_emph = f">> {last_line}" if last_line != "-" else "-"

    # Timing
    telemetry_age_s = None
    if last_dt:
        telemetry_age_s = int((report_dt - last_dt).total_seconds())
        time_since_last = fmt_hms(telemetry_age_s)
        telemetry_age = fmt_hms(telemetry_age_s)
    else:
        time_since_last = "N/A"
        telemetry_age = "N/A"

    # Deltas
    prev_fp = (prev.get("last_track_fp") or "").strip()
    curr_fp = fingerprint(last_line) if last_line != "-" else ""
    if not prev_fp:
        delta_track = "N/A (first report)"
    else:
        delta_track = "CHANGED" if curr_fp and curr_fp != prev_fp else "UNCHANGED"

    prev_last_played = (prev.get("last_played_utc") or "").strip()
    curr_last_played = fmt_utc(last_dt) if last_dt else ""
    if not prev_last_played:
        delta_last_played = "N/A (first report)"
    else:
        delta_last_played = "CHANGED" if curr_last_played and curr_last_played != prev_last_played else "UNCHANGED"

    prev_status = (prev.get("status") or "").strip()
    if not prev_status:
        delta_status = "N/A (first report)"
    else:
        delta_status = "CHANGED" if status != prev_status else "UNCHANGED"

    # Integrity / API condition
    api_condition = "NORMAL" if api_ok else "DEGRADED"
    data_integrity = "OK" if (api_ok and (now_line != "-" or last_line != "-")) else ("PARTIAL" if api_ok else "UNKNOWN")
    cache_state = "POSSIBLE HIT" if cur_class.startswith("200") else "N/A"
    conf = confidence(telemetry_age_s, api_ok)
    sr = sitrep(status, api_ok)

    daily = daily_rollup(rec_items) if SHOW_DAILY_SITREP else None
    weekly = weekly_rollup(rec_items) if SHOW_WEEKLY_SUMMARY else None

    # Build report
    out = []
    out.append("SPOTIFY TELEMETRY — CLI FEED (Spotify ©)")
    out.append("-" * 60)

    if SHOW_HEADER_BLOCK:
        out.append(f"{'Spotify Developer API Source':<27}: Spotify Web API")
        out.append(f"{'Acquisition mode':<27}: OAuth2 / automated workflow")
        out.append(f"{'Snapshot type':<27}: Last-known playback state")
        out.append("-" * 60)

    if SHOW_STATUS_BLOCK:
        out.append(f"{'Status':<27}: {status}")
        out.append(f"{'Playback state':<27}: {playback_state}")
        out.append(f"{'SITREP':<27}: {sr}")
        out.append("-" * 60)

    if SHOW_TRACK_BLOCK:
        out.append(f"{'NOW PLAYING':<27}: {now_line_emph}")
        out.append(f"{'LAST PLAYED':<27}: {last_line_emph}")
        out.append(f"{'Last played (UTC)':<27}: {fmt_utc(last_dt)}")
        if SHOW_EVENT_SIGNATURE:
            out.append(f"{'Event signature':<27}: {'TRACK_PLAYING' if status=='PLAYING' else 'TRACK_END'}@UTC")
        if SHOW_TRACK_FINGERPRINT:
            out.append(f"{'Track fingerprint':<27}: {curr_fp or 'N/A'}")
        out.append("-" * 60)

    if SHOW_DELTAS_BLOCK:
        out.append(f"{'Δ track (since last)':<27}: {delta_track}")
        out.append(f"{'Δ last played (since last)':<27}: {delta_last_played}")
        out.append(f"{'Δ status (since last)':<27}: {delta_status}")
        out.append("-" * 60)

    if SHOW_TIMING_BLOCK:
        out.append(f"{'Time since last play':<27}: {time_since_last}")
        out.append(f"{'Telemetry age':<27}: {telemetry_age}")
        if SHOW_CONTINUITY:
            continuity = "CONTINUOUS" if delta_track in ("UNCHANGED", "N/A (first report)") else "INTERRUPTED"
            out.append(f"{'Playback continuity':<27}: {continuity}")
        out.append("-" * 60)

    if SHOW_API_BLOCK:
        out.append(f"{'API response class':<27}: {cur_class} / {rec_class}")
        out.append(f"{'API condition':<27}: {api_condition}")
        out.append(f"{'Token scope':<27}: {safe(scope) or 'N/A'}")
        if SHOW_CACHE_HINTS:
            out.append(f"{'Cache state':<27}: {cache_state}")
        if SHOW_FALLBACK_LINES:
            lkg = prev.get("last_known_good_snapshot_utc") or "-"
            out.append(f"{'Fallback mode':<27}: HOLD-LAST")
            out.append(f"{'Last known good snapshot':<27}: {lkg}")
        out.append("-" * 60)

    if SHOW_INTEGRITY_BLOCK:
        out.append(f"{'Data integrity':<27}: {data_integrity}")
        if SHOW_CONFIDENCE:
            out.append(f"{'Confidence level':<27}: {conf}")
        out.append("-" * 60)

    if SHOW_DAILY_SITREP and daily:
        out.append("DAILY SPOTIFY SITREP")
        out.append("-" * 60)
        out.append(f"{'Tracks played (24h sample)':<27}: {daily['tracks']}")
        out.append(f"{'Listening time (sample)':<27}: {daily['time']}")
        out.append(f"{'Dominant artist':<27}: {safe(daily['dominant_artist'])}")
        out.append(f"{'Dominant genre':<27}: {safe(daily['dominant_genre'])}")
        out.append(f"{'Listening pattern':<27}: {daily['pattern']}")
        out.append("-" * 60)

    if SHOW_WEEKLY_SUMMARY and weekly:
        out.append("WEEKLY CADENCE SUMMARY")
        out.append("-" * 60)
        out.append(f"{'Peak listening day':<27}: {safe(weekly['peak_day'])}")
        out.append(f"{'Cadence classification':<27}: {weekly['cadence']}")
        out.append(f"{'Trend vs last week':<27}: {weekly['trend_vs_last_week']}")
        out.append("-" * 60)

    out.append(f"{'Report generated (UTC)':<27}: {fmt_utc(report_dt)}")

    block = "```text\n" + "\n".join(out).rstrip() + "\n```"

    # Update README
    with open(README_PATH, "r", encoding="utf-8") as f:
        md = f.read()
    md2 = replace_block(md, block)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(md2)

    # Save state
    new_state = {
        "last_report_utc": fmt_utc(report_dt),
        "status": status,
        "last_played_utc": curr_last_played,
        "last_track_fp": curr_fp,
        "last_known_good_snapshot_utc": curr_last_played or (prev.get("last_known_good_snapshot_utc") or ""),
    }
    save_state(new_state)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
