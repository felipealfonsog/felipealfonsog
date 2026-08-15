#!/usr/bin/env python3
# .github/scripts/spotify_telemetry.py
# v4.0 — persistent historical telemetry + past-oriented analytics

import base64
import json
import math
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# =============================================================================
# TOGGLES (set True/False) — keep these at top, clear and surgical
# =============================================================================

# ---- Master blocks (README output sections) ----
SHOW_HEADER_META          = True
SHOW_STATUS_BLOCK         = True
SHOW_DEVICE_BLOCK         = True
SHOW_RECENT_HISTORY       = True
SHOW_BEHAVIOUR_ANALYTICS  = True
SHOW_DAYPART_ANALYTICS    = True
SHOW_TEMPORAL_ANALYTICS   = True
SHOW_DATA_COVERAGE        = True
SHOW_DELTAS_BLOCK         = True
SHOW_API_BLOCK            = True
SHOW_INTEGRITY_BLOCK      = True
SHOW_DAILY_SITREP         = True
SHOW_WEEKLY_SUMMARY       = True

# Historical snapshot remains persisted internally for fail-safe continuity,
# but is intentionally not rendered because it duplicated several blocks.
SHOW_HISTORICAL_SNAPSHOT  = False

# ---- Device privacy / details ----
SHOW_DEVICE_NAME          = True   # device type stays ON

# ---- Extra telemetry (derived from recently-played) ----
SHOW_GENRE_INTEL          = True
SHOW_HOURLY_HEATMAP       = True
SHOW_SESSION_ESTIMATES    = True
SHOW_WEEK_ACTIVITY        = True
SHOW_WEEKLY_HOUR_MATRIX   = True

# ---- Formatting sub-toggles ----
SCOPE_MODE                = "COMPACT"   # "WRAP" | "COMPACT" | "OFF"
WRAP_WIDTH                = 34
LOCAL_TIMEZONE            = "America/Santiago"

# ---- Behavior toggles ----
FAIL_SAFE_DO_NOT_BREAK_README = True
WRITE_STATE_FILE              = True
OBS_WINDOW_SECONDS            = 30 * 60

# ---- Debug (GitHub Actions only) ----
DEBUG_ACTIONS        = True
DEBUG_DUMP_PAYLOADS  = False   # keep False (privacy)

# ---- Heuristics / safety caps ----
SESSION_GAP_MINUTES       = 25
MAX_RECENT_ITEMS          = 50
MAX_ARTIST_LOOKUPS        = 80

# Cantidad de canciones recientes mostradas/guardadas (1-50)
RECENT_HISTORY_LIMIT      = 25

# ---- ASCII/Unicode visual analytics ----
ANALYTICS_BAR_WIDTH       = 18
VOLUME_BAR_WIDTH          = 12
SHOW_VOLUME_BAR           = True

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
HISTORY_FILE  = os.path.join(STATE_DIR, "spotify_listening_history.json")
DEBUG_FILE    = os.path.join(STATE_DIR, "spotify_debug.json")

ARTIST_CACHE_KEY = "artist_genre_cache"
LAST_SUCCESSFUL_REPORT_KEY = "last_successful_report"
LAST_SUCCESSFUL_REPORT_UTC_KEY = "last_successful_report_utc"
RECENT_HISTORY_STATE_KEY = "recent_playback_history"
LAST_DEVICE_TYPE_STATE_KEY = "last_known_device_type"
LAST_DEVICE_NAME_STATE_KEY = "last_known_device_name"
LAST_VOLUME_STATE_KEY = "last_known_volume_percent"
LAST_VOLUME_TELEMETRY_STATE_KEY = "last_known_volume_telemetry"
HISTORICAL_SNAPSHOT_STATE_KEY = "historical_listening_snapshot"
LAST_DEVICE_CAPTURED_UTC_KEY = "last_known_device_captured_utc"
HISTORY_SCHEMA_VERSION = 1

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


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


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


def dlog(msg: str):
    if not DEBUG_ACTIONS:
        return
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        print(f"[SPOTIFY_DEBUG] {msg}", file=sys.stderr)


class SpotifyAuthError(Exception):
    def __init__(self, reason: str, detail: str = ""):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


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


def load_history_store():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            raise ValueError("history root is not an object")
    except Exception:
        obj = {}
    obj.setdefault("schema_version", HISTORY_SCHEMA_VERSION)
    obj.setdefault("created_utc", None)
    obj.setdefault("updated_utc", None)
    obj.setdefault("events", [])
    obj.setdefault("playback_context", [])
    return obj


def save_history_store(obj: dict):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def history_event_key(entry: dict):
    return (
        entry.get("played_at_utc") or "",
        entry.get("uri") or entry.get("track") or "",
    )


def merge_history_events(store: dict, new_events: list[dict], now_s: str):
    existing = store.get("events") or []
    merged = {}
    for entry in existing + new_events:
        if not isinstance(entry, dict):
            continue
        key = history_event_key(entry)
        if not key[0]:
            continue
        merged[key] = entry
    events = sorted(
        merged.values(),
        key=lambda e: parse_iso_z(e.get("played_at_utc") or "")
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    store["events"] = events
    store["schema_version"] = HISTORY_SCHEMA_VERSION
    store["created_utc"] = store.get("created_utc") or now_s
    store["updated_utc"] = now_s
    return events


def append_playback_context(store: dict, snapshot: dict):
    contexts = store.get("playback_context") or []
    # Preserve every materially distinct observed context while avoiding
    # identical snapshots produced by consecutive scheduled runs.
    signature_fields = (
        "is_playing", "track", "device_type", "device_name",
        "volume_percent", "volume_telemetry", "playback_state",
    )
    previous = contexts[0] if contexts else None
    changed = not previous or any(
        previous.get(k) != snapshot.get(k) for k in signature_fields
    )
    if changed:
        contexts.insert(0, snapshot)
    store["playback_context"] = contexts
    return contexts


def filter_history_window(events: list[dict], cutoff: datetime):
    out = []
    for entry in events:
        dt = parse_iso_z(entry.get("played_at_utc") or "")
        if dt and dt >= cutoff:
            out.append(entry)
    return out


def hour_hist_from_history(events: list[dict]):
    hist = [0] * 24
    for entry in events:
        dt = parse_iso_z(entry.get("played_at_utc") or "")
        if not dt:
            continue
        hist[dt.astimezone(local_tz()).hour] += 1
    return hist


def week_activity_from_history(events: list[dict]):
    counts = [0] * 7
    for entry in events:
        dt = parse_iso_z(entry.get("played_at_utc") or "")
        if dt:
            counts[dt.astimezone(local_tz()).weekday()] += 1
    return counts


def weekly_hour_matrix_from_history(events: list[dict]):
    matrix = [[0] * 24 for _ in range(7)]
    for entry in events:
        dt = parse_iso_z(entry.get("played_at_utc") or "")
        if not dt:
            continue
        local_dt = dt.astimezone(local_tz())
        matrix[local_dt.weekday()][local_dt.hour] += 1
    return matrix


def daily_activity_series(events: list[dict], days: int, now: datetime):
    if days <= 0:
        return []
    tz = local_tz()
    today = now.astimezone(tz).date()
    start = today - timedelta(days=days - 1)
    counts = [0] * days
    for entry in events:
        dt = parse_iso_z(entry.get("played_at_utc") or "")
        if not dt:
            continue
        day = dt.astimezone(tz).date()
        offset = (day - start).days
        if 0 <= offset < days:
            counts[offset] += 1
    return counts


def build_auth_watch_block(
    refresh_token_state: str,
    user_action_required: str,
    secret_to_update: str = "NONE",
    last_good_utc: str | None = None,
):
    client_id_state = "CONFIGURED" if CLIENT_ID else "MISSING"
    client_secret_state = "CONFIGURED" if CLIENT_SECRET else "NOT SET (PKCE OPTIONAL)"
    out = []
    out.append("AUTHORIZATION WATCH")
    out.append("------------------------------------------------------------")
    out.append(f"Client ID state           : {client_id_state}")
    out.append(f"Client secret state       : {client_secret_state}")
    out.append(f"Refresh token state       : {refresh_token_state}")
    out.append(f"User action required      : {user_action_required}")
    out.append(f"Secret to update          : {secret_to_update}")
    out.append("Recovery repository       : felipealfonsog/felipealfonsog.github.io")
    out.append("Recovery workflow         : update-spotify-callback.yml")
    out.append("Callback page             : https://felipealfonsog.github.io/spotify-callback.html")
    if str(user_action_required).upper() == "YES":
        out.append("Recovery step 1           : Run Update Spotify Callback")
        out.append("Recovery step 2           : Enter Spotify Client ID")
        out.append("Recovery step 3           : Open callback page")
        out.append("Recovery step 4           : Authorize Spotify and copy token")
        out.append("Recovery step 5           : Update SPOTIFY_REFRESH_TOKEN")
        out.append("Recovery step 6           : Run Spotify Telemetry")
    else:
        out.append("Recovery procedure        : NOT REQUIRED")
    if last_good_utc:
        out.append(f"Last good telemetry UTC   : {last_good_utc}")
    out.append("------------------------------------------------------------")
    return "\n".join(out)


def replace_auth_watch_block(
    report: str,
    refresh_token_state: str,
    user_action_required: str,
    secret_to_update: str = "NONE",
    last_good_utc: str | None = None,
):
    new_block = build_auth_watch_block(
        refresh_token_state,
        user_action_required,
        secret_to_update,
        last_good_utc,
    )
    pattern = re.compile(
        r"AUTHORIZATION WATCH\n"
        r"------------------------------------------------------------\n"
        r".*?"
        r"------------------------------------------------------------",
        re.S,
    )
    if pattern.search(report):
        return pattern.sub(new_block, report, count=1)

    marker = "Report generated (UTC)"
    idx = report.find(marker)
    if idx >= 0:
        return report[:idx] + new_block + "\n" + report[idx:]
    return report.rstrip() + "\n" + new_block


def build_auth_failsafe_report(reason: str, detail: str = ""):
    state = load_state()
    last_report = state.get(LAST_SUCCESSFUL_REPORT_KEY) or ""
    last_good_utc = state.get(LAST_SUCCESSFUL_REPORT_UTC_KEY) or state.get("report_generated_utc") or "N/A"

    if reason == "SPOTIFY_SECRETS_MISSING":
        missing_secrets = []
        if not CLIENT_ID:
            missing_secrets.append("SPOTIFY_CLIENT_ID")
        if not REFRESH_TOKEN:
            missing_secrets.append("SPOTIFY_REFRESH_TOKEN")
        secret_to_update = " | ".join(missing_secrets) or "VERIFY OAUTH SECRETS"
    elif reason == "SPOTIFY_REFRESH_TOKEN":
        secret_to_update = "SPOTIFY_REFRESH_TOKEN"
    else:
        secret_to_update = "VERIFY SPOTIFY OAUTH SECRETS"

    # Preserve the full last successful historical telemetry and replace only
    # the auth status. This is the core continuity behaviour.
    if last_report:
        return replace_auth_watch_block(
            last_report,
            "REAUTH REQUIRED",
            "YES",
            secret_to_update,
            last_good_utc,
        )

    now_s = utc_iso(utc_now())
    out = []
    out.append("SPOTIFY TELEMETRY — CLI FEED (Spotify ©)")
    out.append("------------------------------------------------------------")
    out.append("Telemetry source          : Spotify Developer Platform — Playback Telemetry ©")
    out.append("Acquisition mode          : OAuth2 / automated workflow")
    out.append("Snapshot type             : Authorization failsafe state")
    out.append("------------------------------------------------------------")
    out.append("Playback state            : OFFLINE (authorization unavailable)")
    out.append("Status                    : IDLE")
    out.append("SITREP                    : AMBER")
    out.append("------------------------------------------------------------")
    out.append("Last historical telemetry : NOT AVAILABLE")
    out.append("------------------------------------------------------------")
    out.append(f"API response class        : {reason}")
    out.append("API condition             : DEGRADED")
    out.append("Data integrity            : DEGRADED")
    out.append("Confidence level          : MEDIUM")
    out.append("------------------------------------------------------------")
    out.append(f"Failure detail            : {detail or 'N/A'}")
    out.append(build_auth_watch_block("REAUTH REQUIRED", "YES", secret_to_update, None))
    out.append(f"Report generated (UTC)    : {now_s}")
    return "\n".join(out)


def spotify_token_request(headers: dict, form: dict):
    body = urllib.parse.urlencode(form).encode("utf-8")
    try:
        code, _, payload = http_json(AUTH_URL, headers=headers, data=body, timeout=25)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except Exception:
            payload = {"raw": raw}
        return e.code, payload
    return code, payload


def spotify_access_token():
    if not (CLIENT_ID and REFRESH_TOKEN):
        raise SpotifyAuthError(
            "SPOTIFY_SECRETS_MISSING",
            "Missing Spotify secrets: SPOTIFY_CLIENT_ID / SPOTIFY_REFRESH_TOKEN",
        )

    attempts = []

    if CLIENT_SECRET:
        auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        code, payload = spotify_token_request(
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            form={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
        )
        attempts.append(("AUTHORIZATION_CODE", code, payload))
        if code < 400 and isinstance(payload, dict) and payload.get("access_token"):
            return payload["access_token"], payload.get("scope") or ""

    code, payload = spotify_token_request(
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        form={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
        },
    )
    attempts.append(("PKCE", code, payload))
    if code < 400 and isinstance(payload, dict) and payload.get("access_token"):
        return payload["access_token"], payload.get("scope") or ""

    errors = [
        payload.get("error")
        for _, _, payload in attempts
        if isinstance(payload, dict)
    ]
    if errors and all(error == "invalid_grant" for error in errors):
        raise SpotifyAuthError(
            "SPOTIFY_REFRESH_TOKEN",
            "Refresh token expired, revoked, invalid, or issued for another Client ID",
        )

    safe_attempts = [
        {
            "mode": mode,
            "http": code,
            "error": payload.get("error") if isinstance(payload, dict) else None,
            "description": payload.get("error_description") if isinstance(payload, dict) else None,
        }
        for mode, code, payload in attempts
    ]
    raise SpotifyAuthError(
        "SPOTIFY_TOKEN_REFRESH_FAILED",
        json.dumps(safe_attempts, ensure_ascii=False),
    )


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
    return fetch_json_endpoint(PLAYER_URL, token, timeout=15)


def fetch_recently_played(token: str, limit: int = 50):
    url = "https://api.spotify.com/v1/me/player/recently-played?limit=" + str(limit)
    code, _, payload = http_json(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    return code, payload


def parse_track_item(track_obj: dict):
    if not track_obj:
        return None
    artists = track_obj.get("artists") or []
    artist = ", ".join([a.get("name", "") for a in artists if a.get("name")]) or "Unknown artist"
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
        idx = int(round((v / m) * (len(chars) - 1)))
        out.append(chars[clamp(idx, 0, len(chars) - 1)])
    return "".join(out)


def ratio_bar(percent: float | None, width: int = ANALYTICS_BAR_WIDTH) -> str:
    if percent is None:
        return "N/A"
    p = clamp(float(percent), 0.0, 100.0)
    filled = int(round((p / 100.0) * width))
    return "█" * filled + "░" * (width - filled)


def daypart_for_hour(hour: int) -> str:
    if 0 <= hour < 6:
        return "NIGHT"
    if 6 <= hour < 12:
        return "MORNING"
    if 12 <= hour < 18:
        return "AFTERNOON"
    return "EVENING"


def daypart_distribution(dts: list[datetime]):
    counts = {"NIGHT": 0, "MORNING": 0, "AFTERNOON": 0, "EVENING": 0}
    for dt in dts:
        local_hour = dt.astimezone(local_tz()).hour
        counts[daypart_for_hour(local_hour)] += 1
    total = sum(counts.values())
    pct = {k: ((v / total) * 100 if total else 0.0) for k, v in counts.items()}
    dominant = max(counts, key=counts.get) if total else "N/A"
    return counts, pct, dominant


def recent_history_from_payload(payload: dict, limit: int = RECENT_HISTORY_LIMIT):
    history = []
    if not isinstance(payload, dict):
        return history

    for item in payload.get("items") or []:
        track = parse_track_item(item.get("track") or {})
        played_at = item.get("played_at") or ""
        played_dt = parse_iso_z(played_at)
        if not track or not played_dt:
            continue

        local_dt = played_dt.astimezone(local_tz())
        history.append({
            "track": f"{track['artist']} — {track['title']}",
            "artist": track["artist"],
            "title": track["title"],
            "album": track.get("album") or "",
            "uri": track.get("uri") or "",
            "url": track.get("url") or "",
            "artist_ids": track.get("artist_ids") or [],
            "played_at_utc": utc_iso(played_dt),
            "played_at_local": local_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "local_hour": local_dt.hour,
            "weekday": local_dt.weekday(),
        })
        if len(history) >= limit:
            break

    return history


def recent_history_heatmap(history: list):
    hist = [0] * 24
    for entry in history:
        try:
            hour = int(entry.get("local_hour"))
        except (TypeError, ValueError):
            played_dt = parse_iso_z(entry.get("played_at_utc") or "")
            if not played_dt:
                continue
            hour = played_dt.astimezone(local_tz()).hour
        if 0 <= hour <= 23:
            hist[hour] += 1
    return hist


def infer_sessions(dts):
    if not dts:
        return 0, None
    dts = sorted(dts)
    gap_s = SESSION_GAP_MINUTES * 60
    sessions = 1
    gaps = []
    for i in range(1, len(dts)):
        delta = (dts[i] - dts[i - 1]).total_seconds()
        gaps.append(delta)
        if delta > gap_s:
            sessions += 1
    avg_gap = (sum(gaps) / len(gaps)) if gaps else None
    return sessions, avg_gap


def gap_stats(dts: list[datetime]):
    if len(dts) < 2:
        return None, None, None
    ordered = sorted(dts)
    gaps = [(ordered[i] - ordered[i - 1]).total_seconds() for i in range(1, len(ordered))]
    return (
        statistics.mean(gaps) if gaps else None,
        statistics.median(gaps) if gaps else None,
        max(gaps) if gaps else None,
    )


def longest_artist_streak(entries: list[dict]):
    if not entries:
        return "N/A", 0
    ordered = sorted(
        entries,
        key=lambda e: parse_iso_z(e.get("played_at_utc") or "") or datetime.min.replace(tzinfo=timezone.utc),
    )
    best_artist = "N/A"
    best_count = 0
    current_artist = None
    current_count = 0
    for e in ordered:
        artist = e.get("artist") or "Unknown artist"
        if artist == current_artist:
            current_count += 1
        else:
            current_artist = artist
            current_count = 1
        if current_count > best_count:
            best_count = current_count
            best_artist = artist
    return best_artist, best_count


def behavioural_metrics(history: list[dict]):
    if not history:
        return {
            "observed": 0,
            "unique_tracks": 0,
            "unique_artists": 0,
            "replay_ratio": None,
            "artist_diversity": None,
            "dominant_artist": "N/A",
            "dominant_artist_share": None,
            "switch_ratio": None,
            "longest_artist_streak_artist": "N/A",
            "longest_artist_streak_count": 0,
        }

    tracks = [e.get("track") or "N/A" for e in history]
    artists = [e.get("artist") or "Unknown artist" for e in history]
    observed = len(history)
    unique_tracks = len(set(tracks))
    unique_artists = len(set(artists))
    replay_ratio = ((observed - unique_tracks) / observed) * 100 if observed else None
    artist_diversity = (unique_artists / observed) * 100 if observed else None

    artist_counts = Counter(artists)
    dominant_artist, dominant_count = artist_counts.most_common(1)[0]
    dominant_share = (dominant_count / observed) * 100 if observed else None

    ordered = sorted(
        history,
        key=lambda e: parse_iso_z(e.get("played_at_utc") or "") or datetime.min.replace(tzinfo=timezone.utc),
    )
    switches = 0
    transitions = max(0, len(ordered) - 1)
    for i in range(1, len(ordered)):
        if (ordered[i].get("artist") or "") != (ordered[i - 1].get("artist") or ""):
            switches += 1
    switch_ratio = (switches / transitions) * 100 if transitions else 0.0

    streak_artist, streak_count = longest_artist_streak(history)

    return {
        "observed": observed,
        "unique_tracks": unique_tracks,
        "unique_artists": unique_artists,
        "replay_ratio": replay_ratio,
        "artist_diversity": artist_diversity,
        "dominant_artist": dominant_artist,
        "dominant_artist_share": dominant_share,
        "switch_ratio": switch_ratio,
        "longest_artist_streak_artist": streak_artist,
        "longest_artist_streak_count": streak_count,
    }


def week_activity_from_items(items: list[dict]):
    counts = [0] * 7
    for it in items:
        dtp = parse_iso_z(it.get("played_at") or "")
        if not dtp:
            continue
        wd = dtp.astimezone(local_tz()).weekday()
        counts[wd] += 1
    return counts


def weekly_hour_matrix_from_items(items: list[dict]):
    matrix = [[0] * 24 for _ in range(7)]
    for it in items:
        dtp = parse_iso_z(it.get("played_at") or "")
        if not dtp:
            continue
        local_dt = dtp.astimezone(local_tz())
        matrix[local_dt.weekday()][local_dt.hour] += 1
    return matrix


def matrix_heatmap_row(row: list[int]) -> str:
    return heatmap_line(row) if row and max(row) > 0 else " " * 24


def volume_bar(percent: int | None) -> str:
    if percent is None:
        return "-"
    p = clamp(int(percent), 0, 100)
    chars = " ▁▂▃▄▅▆▇█"
    filled_steps = int(round((p / 100) * VOLUME_BAR_WIDTH))
    if filled_steps <= 0:
        return chars[1] * VOLUME_BAR_WIDTH
    out = []
    for i in range(VOLUME_BAR_WIDTH):
        if i < filled_steps:
            level = int(round(((i + 1) / VOLUME_BAR_WIDTH) * (len(chars) - 1)))
            out.append(chars[clamp(level, 1, len(chars) - 1)])
        else:
            out.append(" ")
    return "".join(out).rstrip() or "-"

# =============================================================================
# Main telemetry build
# =============================================================================

def build_report():
    now = utc_now()
    now_s = utc_iso(now)

    prev = load_state() if WRITE_STATE_FILE else {}
    mutable_state = dict(prev)

    prev_track = prev.get("last_track", "")
    prev_last_played = prev.get("last_played_utc", "")
    prev_status = prev.get("status", "")
    prev_report_ts = prev.get("report_generated_utc", "")

    token, scope = spotify_access_token()

    player = fetch_player_state(token)
    player_http = player.get("http", -1)
    player_data = player.get("data") if isinstance(player.get("data"), dict) else None

    cur = fetch_currently_playing(token)
    api_http = cur.get("http", -1)
    api_ok_current = api_http in (200, 204)

    cur_data = cur.get("data") if isinstance(cur.get("data"), dict) else None
    cur_is_playing = bool(cur_data.get("is_playing")) if isinstance(cur_data, dict) else False

    has_active_session = (
        player_http == 200
        and isinstance(player_data, dict)
        and isinstance(player_data.get("device"), dict)
    )

    device_type = "N/A"
    device_name = "N/A"
    volume_percent = None

    status = "UNKNOWN"
    playback_state = "UNKNOWN"
    last_activity_type = "UNKNOWN"
    now_track_name = "N/A"
    is_playing = False
    volume_telemetry = "NO ACTIVE SESSION"

    if has_active_session:
        is_playing = cur_is_playing if api_http == 200 else bool((player_data or {}).get("is_playing"))
        status = "PLAYING" if is_playing else "IDLE"
        playback_state = "ONLINE (active session)" if is_playing else "ONLINE (idle session)"
        last_activity_type = "PLAYBACK_ACTIVE" if is_playing else "PLAYBACK_INACTIVE"
    else:
        if api_http == 200 and cur_is_playing:
            is_playing = True
            status = "PLAYING"
            playback_state = "ONLINE (active session)"
            last_activity_type = "PLAYBACK_ACTIVE"
        else:
            is_playing = False
            status = "IDLE"
            playback_state = "OFFLINE (no active session)"
            last_activity_type = "NO_ACTIVE_SESSION"

    if player_http == 200 and isinstance(player_data, dict) and isinstance(player_data.get("device"), dict):
        dev = player_data.get("device") or {}
        device_type = dev.get("type") or "N/A"
        device_name = dev.get("name") or "N/A"
        volume_percent = dev.get("volume_percent", None)
        if is_playing:
            volume_telemetry = "OK" if volume_percent is not None else "NOT EXPOSED BY DEVICE"
        else:
            volume_telemetry = "IDLE (session present, no playback)"
    else:
        volume_telemetry = "PLAYING (device not available this run)" if is_playing else "NO ACTIVE SESSION"

    if api_http == 200 and isinstance(cur_data, dict):
        item = cur_data.get("item") or {}
        now_track_obj = parse_track_item(item)
        if cur_is_playing and now_track_obj:
            now_track_name = f"{now_track_obj['artist']} — {now_track_obj['title']}"

    dlog(
        f"session={has_active_session} is_playing={is_playing} status={status} "
        f"playback_state={playback_state} player_http={player_http} api_http={api_http}"
    )

    if DEBUG_ACTIONS and os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        os.makedirs(STATE_DIR, exist_ok=True)
        debug_obj = {
            "ts_utc": now_s,
            "player_http": player_http,
            "current_http": api_http,
            "has_active_session": has_active_session,
            "is_playing": is_playing,
            "status": status,
            "playback_state": playback_state,
            "last_activity_type": last_activity_type,
            "device_type": device_type,
            "device_name": device_name if SHOW_DEVICE_NAME else None,
            "volume_percent": volume_percent,
        }
        if DEBUG_DUMP_PAYLOADS:
            debug_obj["player_payload_keys"] = sorted(list((player_data or {}).keys())) if isinstance(player_data, dict) else None
            debug_obj["current_payload_keys"] = sorted(list((cur_data or {}).keys())) if isinstance(cur_data, dict) else None
        with open(DEBUG_FILE, "w", encoding="utf-8") as f:
            json.dump(debug_obj, f, ensure_ascii=False, indent=2)

    recent_code, recent_payload = fetch_recently_played(token, limit=MAX_RECENT_ITEMS)
    recent_ok = recent_code == 200 and isinstance(recent_payload, dict)

    # -------------------------------------------------------------------------
    # Persistent listening history
    # Spotify exposes only a recent-playback window. Every run merges newly
    # observed plays into our own journal so 24h/7d/30d analytics are based on
    # retained history, not only the latest API window.
    # -------------------------------------------------------------------------
    history_store = load_history_store()
    api_history = (
        recent_history_from_payload(recent_payload, MAX_RECENT_ITEMS)
        if recent_ok else []
    )
    all_history = merge_history_events(history_store, api_history, now_s)
    recent_history = all_history[:RECENT_HISTORY_LIMIT]

    # Keep a lightweight history of observed player/device contexts. Spotify
    # does not provide per-track historical device/volume information.
    context_snapshot = {
        "captured_utc": now_s,
        "is_playing": bool(is_playing),
        "track": now_track_name if is_playing else None,
        "playback_state": playback_state,
        "device_type": device_type if has_active_session else None,
        "device_name": device_name if has_active_session else None,
        "volume_percent": volume_percent if has_active_session else None,
        "volume_telemetry": volume_telemetry,
    }
    append_playback_context(history_store, context_snapshot)

    last_track_name = recent_history[0].get("track", "-") if recent_history else "-"
    last_played_utc = recent_history[0].get("played_at_utc", "") if recent_history else ""
    last_played_local = recent_history[0].get("played_at_local", "N/A") if recent_history else "N/A"

    # Last observed playback context is persisted independently from whether a
    # live session exists at this exact run.
    if has_active_session:
        last_known_device_type = device_type or "N/A"
        last_known_device_name = device_name or "N/A"
        last_known_volume_percent = volume_percent
        last_known_volume_telemetry = volume_telemetry
        last_known_device_captured_utc = now_s
    else:
        last_known_device_type = prev.get(LAST_DEVICE_TYPE_STATE_KEY) or "N/A"
        last_known_device_name = prev.get(LAST_DEVICE_NAME_STATE_KEY) or "N/A"
        last_known_volume_percent = prev.get(LAST_VOLUME_STATE_KEY)
        last_known_volume_telemetry = prev.get(LAST_VOLUME_TELEMETRY_STATE_KEY) or "N/A"
        last_known_device_captured_utc = prev.get(LAST_DEVICE_CAPTURED_UTC_KEY) or "N/A"

    time_since_last_play = "N/A"
    telemetry_age = "N/A"
    if last_played_utc:
        last_dt = parse_iso_z(last_played_utc)
        if last_dt:
            delta = (now - last_dt).total_seconds()
            time_since_last_play = fmt_hms(delta)
            telemetry_age = fmt_hms(delta)

    def delta_str(prev_val, new_val, first_label="N/A (first report)"):
        if not prev_val:
            return first_label
        if prev_val == new_val:
            return "NO CHANGE"
        return f"{prev_val} → {new_val}"

    d_track = delta_str(prev_track, last_track_name)
    d_last = delta_str(prev_last_played, last_played_utc)
    d_stat = delta_str(prev_status, status)

    d_time = "N/A (first report)"
    if prev_report_ts:
        pdt = parse_iso_z(prev_report_ts)
        if pdt:
            d_time = fmt_hms((now - pdt).total_seconds())

    tz = local_tz()
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)

    history_24h = filter_history_window(all_history, cutoff_24h)
    history_7d = filter_history_window(all_history, cutoff_7d)
    history_30d = filter_history_window(all_history, cutoff_30d)

    hour_hist_24h = hour_hist_from_history(history_24h)
    hour_hist_7d = hour_hist_from_history(history_7d)
    hour_hist_30d = hour_hist_from_history(history_30d)

    played_times_24h = [
        dt for dt in (parse_iso_z(e.get("played_at_utc") or "") for e in history_24h) if dt
    ]
    played_times_7d = [
        dt for dt in (parse_iso_z(e.get("played_at_utc") or "") for e in history_7d) if dt
    ]

    daily_tracks = len(history_24h)
    weekly_total = len(history_7d)

    artist_counts_24h = Counter(e.get("artist") or "Unknown artist" for e in history_24h)
    artist_counts_7d = Counter(e.get("artist") or "Unknown artist" for e in history_7d)
    dominant_artist_24h = artist_counts_24h.most_common(1)[0][0] if artist_counts_24h else None
    dominant_artist_week = artist_counts_7d.most_common(1)[0][0] if artist_counts_7d else None

    if daily_tracks >= 25:
        daily_status = "HIGH"
        daily_pattern = "Sustained operational tempo"
    elif daily_tracks >= 10:
        daily_status = "MEDIUM"
        daily_pattern = "Regular cadence"
    elif daily_tracks >= 1:
        daily_status = "LOW"
        daily_pattern = "Light activity"
    else:
        daily_status = "NONE"
        daily_pattern = "No activity"

    if weekly_total >= 80:
        cadence = "VERY HIGH"
    elif weekly_total >= 40:
        cadence = "HIGH"
    elif weekly_total >= 15:
        cadence = "MEDIUM"
    elif weekly_total >= 1:
        cadence = "LOW"
    else:
        cadence = "NONE"

    week_window_start = cutoff_7d

    sessions_24h = 0
    sessions_7d = 0
    avg_session_gap_7d = "N/A"
    if SHOW_SESSION_ESTIMATES:
        sessions_24h, _ = infer_sessions(played_times_24h)
        sessions_7d, avg_gap = infer_sessions(played_times_7d)
        avg_session_gap_7d = fmt_hms(avg_gap) if avg_gap is not None else "N/A"

    # Genre intelligence is derived from persistent events and cached artist IDs.
    genre_24h = []
    genre_7d = []
    artist_lookup_counter = {"n": 0}
    if SHOW_GENRE_INTEL:
        for entry in history_7d:
            dtp = parse_iso_z(entry.get("played_at_utc") or "")
            for aid in entry.get("artist_ids") or []:
                genres = get_artist_genres(token, aid, mutable_state, artist_lookup_counter)
                if dtp and dtp >= cutoff_24h:
                    genre_24h.extend(genres)
                genre_7d.extend(genres)

    genre_top_24h = topk(genre_24h, 6)
    genre_top_7d = topk(genre_7d, 6)

    historical_snapshot = {
        "captured_utc": now_s,
        "week_window_utc": f"{utc_iso(week_window_start)} → {now_s}",
        "tracks_24h": daily_tracks,
        "tracks_7d": weekly_total,
        "dominant_artist_24h": dominant_artist_24h or "N/A",
        "dominant_artist_7d": dominant_artist_week or "N/A",
        "listening_pattern_24h": daily_pattern,
        "activity_status_24h": daily_status,
        "cadence_7d": cadence,
        "local_timezone": LOCAL_TIMEZONE,
        "peak_hour_24h": peak_hour(hour_hist_24h),
        "peak_hour_7d": peak_hour(hour_hist_7d),
        "heatmap_24h": heatmap_line(hour_hist_24h),
        "heatmap_7d": heatmap_line(hour_hist_7d),
        "sessions_24h": sessions_24h or "N/A",
        "sessions_7d": sessions_7d or "N/A",
        "avg_inter_play_gap_7d": avg_session_gap_7d,
        "top_genres_24h": " | ".join(f"{g}({c})" for g, c in genre_top_24h) if genre_top_24h else "N/A",
        "top_genres_7d": " | ".join(f"{g}({c})" for g, c in genre_top_7d) if genre_top_7d else "N/A",
    }

    api_ok = (player_http in (200, 204)) and api_ok_current and recent_ok
    sitrep = classify_sitrep(status, playback_state, api_ok)

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

    # -------------------------------------------------------------------------
    # Historical analytics from the persistent journal
    # -------------------------------------------------------------------------
    analytics_history = history_7d
    behaviour = behavioural_metrics(analytics_history)

    analytics_dts = [
        parse_iso_z(e.get("played_at_utc") or "")
        for e in analytics_history
    ]
    analytics_dts = [dt for dt in analytics_dts if dt]
    mean_gap, median_gap, longest_gap = gap_stats(analytics_dts)

    sample_first = min(analytics_dts) if analytics_dts else None
    sample_last = max(analytics_dts) if analytics_dts else None
    observed_span = (sample_last - sample_first).total_seconds() if sample_first and sample_last else None
    intensity = None
    if observed_span and observed_span > 0:
        intensity = len(analytics_dts) / (observed_span / 3600.0)

    _, daypart_pct, dominant_daypart = daypart_distribution(analytics_dts)

    week_activity = week_activity_from_history(history_7d)
    week_matrix = weekly_hour_matrix_from_history(history_7d)
    activity_30d = daily_activity_series(history_30d, 30, now)

    history_total = len(all_history)
    history_oldest_dt = None
    history_newest_dt = None
    if all_history:
        history_newest_dt = parse_iso_z(all_history[0].get("played_at_utc") or "")
        history_oldest_dt = parse_iso_z(all_history[-1].get("played_at_utc") or "")

    out = []
    out.append("SPOTIFY TELEMETRY — CLI FEED (Spotify ©)")
    out.append("------------------------------------------------------------")

    if SHOW_HEADER_META:
        out.append("Telemetry source          : Spotify Developer Platform — Playback Telemetry ©")
        out.append("Acquisition mode          : OAuth2 / automated workflow")
        out.append("Snapshot type             : Historical playback telemetry + live signal")
        out.append(f"Observation window        : {fmt_hms(OBS_WINDOW_SECONDS)}")
        out.append("------------------------------------------------------------")

    if SHOW_STATUS_BLOCK:
        out.append("LIVE PLAYBACK (current signal only)")
        out.append("------------------------------------------------------------")
        if is_playing:
            observed_local = now.astimezone(local_tz()).strftime("%Y-%m-%d %H:%M:%S %Z")
            out.append("Live state                : PLAYING")
            out.append(f"Now playing               : {now_track_name}")
            out.append(f"Observed (local)          : {observed_local}")
            out.append(f"Device                    : {device_name if SHOW_DEVICE_NAME else device_type}")
            out.append(f"Volume                    : {f'{int(volume_percent)}%' if volume_percent is not None else 'N/A'}")
            out.append(f"Volume telemetry          : {volume_telemetry}")
        else:
            out.append("Live state                : INACTIVE")
        out.append("------------------------------------------------------------")

    if SHOW_RECENT_HISTORY:
        out.append("RECENT PLAYBACK HISTORY")
        out.append("------------------------------------------------------------")
        if recent_history:
            first = recent_history[0]
            out.append(f"Last track played         : {first.get('track', 'N/A')}")
            out.append(f"Last played (UTC)         : {first.get('played_at_utc', 'N/A')}")
            out.append(f"Last played (local)       : {first.get('played_at_local', 'N/A')}")
            out.append(f"Time since last play      : {time_since_last_play}")
        else:
            out.append("Last track played         : N/A")
            out.append("Last played (UTC)         : N/A")
            out.append("Last played (local)       : N/A")
            out.append("Time since last play      : N/A")
        out.append("------------------------------------------------------------")
        for index in range(1, RECENT_HISTORY_LIMIT):
            if index < len(recent_history):
                entry = recent_history[index]
                value = f"{entry.get('track', 'N/A')} | {entry.get('played_at_local', 'N/A')}"
            else:
                value = "N/A"
            out.append(f"Previous track #{index:<2}        : {value}")
        out.append("------------------------------------------------------------")

    if SHOW_DEVICE_BLOCK:
        display_volume = (
            f"{int(last_known_volume_percent)}%"
            if last_known_volume_percent is not None else "N/A"
        )
        display_volume_bar = (
            volume_bar(int(last_known_volume_percent))
            if SHOW_VOLUME_BAR and last_known_volume_percent is not None
            else "-"
        )
        out.append("LAST KNOWN PLAYBACK CONTEXT")
        out.append("------------------------------------------------------------")
        out.append(f"Last known device type    : {last_known_device_type or 'N/A'}")
        if SHOW_DEVICE_NAME:
            out.append(f"Last known device name    : {last_known_device_name or 'N/A'}")
        out.append(f"Last known volume         : {display_volume}")
        out.append(f"Volume telemetry          : {last_known_volume_telemetry}")
        if SHOW_VOLUME_BAR and display_volume_bar and display_volume_bar != "-":
            out.append(f"Volume bar                : {display_volume_bar}")
        out.append(f"Context observed (UTC)    : {last_known_device_captured_utc}")
        out.append("------------------------------------------------------------")

    if SHOW_BEHAVIOUR_ANALYTICS:
        out.append("PLAYBACK BEHAVIOUR ANALYTICS (7d history)")
        out.append("------------------------------------------------------------")
        out.append(f"Observed events           : {behaviour['observed']}")
        out.append(f"Unique tracks             : {behaviour['unique_tracks']}")
        out.append(f"Unique artists            : {behaviour['unique_artists']}")
        out.append(f"Replay ratio              : {ratio_bar(behaviour['replay_ratio'])}  {fmt_pct(behaviour['replay_ratio'])}")
        out.append(f"Artist diversity          : {ratio_bar(behaviour['artist_diversity'])}  {fmt_pct(behaviour['artist_diversity'])}")
        out.append(f"Dominant artist           : {behaviour['dominant_artist']}")
        out.append(f"Dominant artist share     : {ratio_bar(behaviour['dominant_artist_share'])}  {fmt_pct(behaviour['dominant_artist_share'])}")
        out.append(f"Artist switch ratio       : {ratio_bar(behaviour['switch_ratio'])}  {fmt_pct(behaviour['switch_ratio'])}")
        out.append(
            f"Longest artist streak     : {behaviour['longest_artist_streak_artist']} × {behaviour['longest_artist_streak_count']}"
            if behaviour['longest_artist_streak_count']
            else "Longest artist streak     : N/A"
        )
        out.append("------------------------------------------------------------")

    if SHOW_DAYPART_ANALYTICS:
        out.append("DAYPART DISTRIBUTION (7d history)")
        out.append("------------------------------------------------------------")
        for key, label in [
            ("NIGHT", "Night      00–06"),
            ("MORNING", "Morning    06–12"),
            ("AFTERNOON", "Afternoon  12–18"),
            ("EVENING", "Evening    18–24"),
        ]:
            pct = daypart_pct.get(key, 0.0)
            out.append(f"{label:<27}: {ratio_bar(pct)}  {pct:5.1f}%")
        out.append(f"Dominant period           : {dominant_daypart}")
        out.append("------------------------------------------------------------")

    if SHOW_TEMPORAL_ANALYTICS:
        out.append("TEMPORAL PLAYBACK ANALYSIS (7d history)")
        out.append("------------------------------------------------------------")
        out.append(f"History first play (7d)  : {utc_iso(sample_first) if sample_first else 'N/A'}")
        out.append(f"History last play (7d)   : {utc_iso(sample_last) if sample_last else 'N/A'}")
        out.append(f"Observed time span        : {fmt_hms(observed_span) if observed_span is not None else 'N/A'}")
        out.append(f"Mean inter-play gap       : {fmt_hms(mean_gap) if mean_gap is not None else 'N/A'}")
        out.append(f"Median inter-play gap     : {fmt_hms(median_gap) if median_gap is not None else 'N/A'}")
        out.append(f"Longest inactivity gap    : {fmt_hms(longest_gap) if longest_gap is not None else 'N/A'}")
        out.append(f"Listening intensity       : {intensity:.2f} tracks/hour" if intensity is not None else "Listening intensity       : N/A")
        out.append("------------------------------------------------------------")

    if SHOW_HOURLY_HEATMAP:
        out.append("LISTENING HOURS (local time)")
        out.append("------------------------------------------------------------")
        out.append(f"Local timezone            : {LOCAL_TIMEZONE}")
        out.append(f"Peak hour (24h)           : {peak_hour(hour_hist_24h)}")
        out.append(f"Peak hour (7d)            : {peak_hour(hour_hist_7d)}")
        out.append(f"Heatmap (24h)             : {heatmap_line(hour_hist_24h)}")
        out.append(f"Heatmap (7d)               : {heatmap_line(hour_hist_7d)}")
        out.append("------------------------------------------------------------")

    if SHOW_WEEK_ACTIVITY:
        out.append("WEEK ACTIVITY (7d history)")
        out.append("------------------------------------------------------------")
        out.append(f"Activity (Mon→Sun)        : {heatmap_line(week_activity)}")
        out.append("Day order                 : Mon Tue Wed Thu Fri Sat Sun")
        out.append("Activity trend (30d)      : " + heatmap_line(activity_30d))
        out.append("Trend order               : oldest → newest")
        out.append("------------------------------------------------------------")

    if SHOW_WEEKLY_HOUR_MATRIX:
        out.append("WEEKLY HOUR MATRIX (7d history)")
        out.append("------------------------------------------------------------")
        for idx, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            out.append(f"{day}                       : {matrix_heatmap_row(week_matrix[idx])}")
        out.append("Hour axis                 : 00      06      12      18     23")
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
        out.append(f"Tracks played (7d)       : {weekly_total if weekly_total is not None else 'N/A'}")
        out.append(f"Dominant artist           : {dominant_artist_week or 'N/A'}")
        out.append(f"Cadence classification    : {cadence or 'N/A'}")
        out.append("------------------------------------------------------------")

    if SHOW_SESSION_ESTIMATES:
        out.append("SESSION ESTIMATES (inferred)")
        out.append("------------------------------------------------------------")
        out.append(f"Session gap threshold     : {SESSION_GAP_MINUTES} minutes")
        out.append(f"Sessions (24h)            : {sessions_24h if sessions_24h else 'N/A'}")
        out.append(f"Sessions (7d)             : {sessions_7d if sessions_7d else 'N/A'}")
        out.append(f"Avg inter-play gap        : {avg_session_gap_7d}")
        out.append("------------------------------------------------------------")

    if SHOW_GENRE_INTEL:
        out.append("GENRE INTEL (inferred)")
        out.append("------------------------------------------------------------")
        out.append("Top genres (24h)          : " + (" | ".join([f"{g}({c})" for g, c in genre_top_24h]) if genre_top_24h else "N/A"))
        out.append("Top genres (7d)           : " + (" | ".join([f"{g}({c})" for g, c in genre_top_7d]) if genre_top_7d else "N/A"))
        out.append(f"Artist lookups (this run) : {artist_lookup_counter['n']} (cached)")
        out.append("------------------------------------------------------------")

    if SHOW_DELTAS_BLOCK:
        out.append("CHANGE TELEMETRY")
        out.append("------------------------------------------------------------")
        out.append(f"Track transition          : {d_track}")
        out.append(f"Playback timestamp Δ      : {d_last}")
        out.append(f"State transition          : {d_stat}")
        out.append(f"Telemetry interval        : {d_time}")
        out.append("------------------------------------------------------------")

    if SHOW_DATA_COVERAGE:
        oldest_history_local = "N/A"
        newest_history_local = "N/A"
        if history_oldest_dt:
            oldest_history_local = history_oldest_dt.astimezone(local_tz()).strftime("%Y-%m-%d %H:%M:%S %Z")
        if history_newest_dt:
            newest_history_local = history_newest_dt.astimezone(local_tz()).strftime("%Y-%m-%d %H:%M:%S %Z")
        out.append("HISTORICAL DATA COVERAGE")
        out.append("------------------------------------------------------------")
        out.append(f"Events retained           : {history_total}")
        out.append(f"Oldest retained event     : {oldest_history_local}")
        out.append(f"Newest retained event     : {newest_history_local}")
        out.append(f"Events (24h)              : {len(history_24h)}")
        out.append(f"Events (7d)               : {len(history_7d)}")
        out.append(f"Events (30d)              : {len(history_30d)}")
        out.append("Storage mode              : PERSISTENT LOCAL JOURNAL")
        out.append("Deduplication             : played_at + track URI")
        out.append("------------------------------------------------------------")

    if SHOW_API_BLOCK:
        out.append("API / AUTHORIZATION TELEMETRY")
        out.append("------------------------------------------------------------")
        out.append(f"API response class        : {api_class}")
        out.append(f"API condition             : {'NORMAL' if api_ok else 'DEGRADED'}")
        scope_lines = fmt_scope_lines(scope)
        if scope_lines:
            out.append(f"Authorization scope       : {scope_lines[0]}")
            if SCOPE_MODE != "COMPACT":
                for ln in scope_lines[1:]:
                    out.append(f"                           {ln}")
        if player_http == 200:
            out.append("Player endpoint           : 200 OK")
        elif player_http == 204:
            out.append("Player endpoint           : 204 NO CONTENT")
        elif player_http == -1:
            out.append("Player endpoint           : NETWORK/EXCEPTION")
        else:
            out.append(f"Player endpoint           : {player_http} ERROR")
        out.append("------------------------------------------------------------")

    if SHOW_INTEGRITY_BLOCK:
        out.append("DATA INTEGRITY")
        out.append("------------------------------------------------------------")
        out.append(f"Data integrity            : {integrity}")
        out.append(f"Confidence level          : {confidence}")
        out.append("------------------------------------------------------------")

    # Internal historical snapshot intentionally not rendered by default.
    if SHOW_HISTORICAL_SNAPSHOT:
        out.append("HISTORICAL LISTENING SNAPSHOT")
        out.append("------------------------------------------------------------")
        out.append(f"Snapshot captured (UTC)   : {historical_snapshot.get('captured_utc', 'N/A')}")
        out.append(f"Week window (UTC)         : {historical_snapshot.get('week_window_utc', 'N/A')}")
        out.append(f"Tracks played (last 24h)  : {historical_snapshot.get('tracks_24h', 'N/A')}")
        out.append(f"Total tracks played (7d)  : {historical_snapshot.get('tracks_7d', 'N/A')}")
        out.append("------------------------------------------------------------")

    out.append(build_auth_watch_block("PASSING", "NO", "NONE"))
    out.append(f"Report generated (UTC)    : {now_s}")

    report = "\n".join(out)

    if WRITE_STATE_FILE:
        mutable_state.update({
            "report_generated_utc": now_s,
            "status": status,
            "last_track": last_track_name,
            "last_played_utc": last_played_utc,
            "sitrep": sitrep,
            RECENT_HISTORY_STATE_KEY: recent_history,
            LAST_DEVICE_TYPE_STATE_KEY: last_known_device_type,
            LAST_DEVICE_NAME_STATE_KEY: last_known_device_name,
            LAST_VOLUME_STATE_KEY: last_known_volume_percent,
            LAST_VOLUME_TELEMETRY_STATE_KEY: last_known_volume_telemetry,
            LAST_DEVICE_CAPTURED_UTC_KEY: last_known_device_captured_utc,
            HISTORICAL_SNAPSHOT_STATE_KEY: historical_snapshot,
            LAST_SUCCESSFUL_REPORT_KEY: report,
            LAST_SUCCESSFUL_REPORT_UTC_KEY: now_s,
        })
        save_state(mutable_state)
        save_history_store(history_store)

    return report


def main():
    try:
        report = build_report()
        rewrite_readme_block(report)
    except SpotifyAuthError as e:
        print(f"Spotify auth failsafe: {e.reason} — {e.detail}", file=sys.stderr)
        if FAIL_SAFE_DO_NOT_BREAK_README:
            report = build_auth_failsafe_report(e.reason, e.detail)
            rewrite_readme_block(report)
            sys.exit(0)
        raise


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
