#!/usr/bin/env python3
import argparse
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

AUTH_URL    = "https://accounts.spotify.com/api/token"
RECENT_URL  = "https://api.spotify.com/v1/me/player/recently-played"
CURRENT_URL = "https://api.spotify.com/v1/me/player/currently-playing"

CACHE_DIR  = ".cache"
OUT_TXT    = os.path.join(CACHE_DIR, "spotify_telemetry.txt")
STATE_JSON = os.path.join(CACHE_DIR, "spotify_state.json")
README     = "README.md"

MARK_START = "<!-- SPOTIFY_TEL:START -->"
MARK_END   = "<!-- SPOTIFY_TEL:END -->"

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def fmt_utc(dt: datetime | None) -> str:
    if not dt:
        return "N/A"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def parse_iso_utc(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None

def fmt_hms(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def env_bool(name: str, default: bool = True) -> bool:
    v = (os.environ.get(name, "") or "").strip().lower()
    if not v:
        return default
    return v in ("true", "1", "yes", "y", "on")

def env_int(name: str, default: int) -> int:
    v = (os.environ.get(name, "") or "").strip()
    if not v:
        return default
    try:
        return int(v)
    except Exception:
        return default

def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
        if not raw.strip():
            return r.getcode(), dict(r.headers), None
        return r.getcode(), dict(r.headers), json.loads(raw)

def token_refresh(client_id: str, client_secret: str, refresh_token: str) -> tuple[str, str]:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
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

    if code >= 400 or not isinstance(payload, dict):
        raise RuntimeError(f"Token refresh failed (HTTP {code}).")

    access = payload.get("access_token")
    scope  = payload.get("scope", "")
    if not access:
        raise RuntimeError("Token refresh failed: no access_token.")
    return access, scope

def fetch_current(access_token: str) -> tuple[int, str, dict | None]:
    """
    Returns: (http_status, api_class, payload)
      - 200: payload JSON with item/device/progress_ms/is_playing...
      - 204: no active playback
    """
    req = urllib.request.Request(
        CURRENT_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            status = int(r.status)
            if status == 204:
                return 204, "204 NO CONTENT", None
            raw = r.read().decode("utf-8", "replace").strip()
            if not raw:
                return status, f"{status}", None
            try:
                return status, "200 OK", json.loads(raw)
            except Exception:
                return status, f"{status} PARSE_ERROR", None
    except urllib.error.HTTPError as e:
        return int(e.code), f"{e.code}", None
    except Exception:
        return 0, "NETWORK/UNKNOWN", None

def fetch_recent(access_token: str, limit: int) -> list[dict]:
    url = RECENT_URL + "?" + urllib.parse.urlencode({"limit": str(limit)})
    code, _, payload = http_json(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=25)
    if code >= 400 or not isinstance(payload, dict):
        raise RuntimeError(f"Spotify API error (recently-played) HTTP {code}.")
    return payload.get("items") or []

def extract_track_line(track_obj: dict | None) -> tuple[str, str]:
    t = track_obj or {}
    artists = t.get("artists") or []
    artist = ", ".join([a.get("name","") for a in artists if a.get("name")]) or "Unknown artist"
    title = t.get("name") or "Unknown track"
    return artist, title

def short_fp(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:10]

def load_state() -> dict:
    try:
        with open(STATE_JSON, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def save_state(st: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(STATE_JSON, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)

def sitrep_from(status: str, api_condition: str, integrity: str) -> str:
    if integrity != "OK":
        return "RED"
    if api_condition != "NORMAL":
        return "AMBER" if status in ("PLAYING","IDLE") else "RED"
    return "GREEN" if status == "PLAYING" else "AMBER" if status == "IDLE" else "RED"

def api_condition_from(api_class: str, token_ok: bool) -> str:
    if not token_ok:
        return "DEGRADED"
    if api_class.startswith("200") or api_class.startswith("204"):
        return "NORMAL"
    if api_class in ("NETWORK/UNKNOWN","UNKNOWN","0"):
        return "DEGRADED"
    return "DEGRADED"

def confidence_level(api_condition: str, integrity: str) -> str:
    if integrity != "OK":
        return "LOW"
    if api_condition != "NORMAL":
        return "MEDIUM"
    return "HIGH"

def cadence_label(n: int) -> str:
    if n >= 25:
        return "HIGH"
    if n >= 8:
        return "MODERATE"
    return "LOW"

def apply_to_readme(report: str):
    with open(README, "r", encoding="utf-8") as f:
        md = f.read()

    pat = re.compile(rf"{re.escape(MARK_START)}.*?{re.escape(MARK_END)}", re.S)
    if not pat.search(md):
        raise SystemExit(f"Markers not found: {MARK_START} ... {MARK_END}")

    block = (
        f"{MARK_START}\n"
        "```text\n"
        f"{report}"
        "```\n"
        f"{MARK_END}"
    )
    md2 = pat.sub(block, md)
    with open(README, "w", encoding="utf-8") as f:
        f.write(md2)

def build_report(access: str, scope: str, apply_only: bool = False) -> str:
    now = utc_now()
    tz_label = (os.environ.get("SPOTIFY_TZ_LABEL", "UTC") or "UTC").strip() or "UTC"

    # ===== section toggles =====
    show_header   = env_bool("SPOTIFY_SHOW_HEADER", True)
    show_core     = env_bool("SPOTIFY_SHOW_CORE_STATUS", True)
    show_now_det  = env_bool("SPOTIFY_SHOW_NOW_PLAYING_DETAILS", True)
    show_last     = env_bool("SPOTIFY_SHOW_LAST_PLAYED", True)
    show_deltas   = env_bool("SPOTIFY_SHOW_DELTAS", True)
    show_timing   = env_bool("SPOTIFY_SHOW_TIMING", True)
    show_api      = env_bool("SPOTIFY_SHOW_API_HEALTH", True)
    show_integr   = env_bool("SPOTIFY_SHOW_INTEGRITY", True)
    show_daily    = env_bool("SPOTIFY_SHOW_DAILY_SITREP", True)
    show_weekly   = env_bool("SPOTIFY_SHOW_WEEKLY_SUMMARY", True)

    # ===== subfield toggles =====
    show_device   = env_bool("SPOTIFY_SHOW_DEVICE", True)
    show_volume   = env_bool("SPOTIFY_SHOW_VOLUME", False)
    show_sr       = env_bool("SPOTIFY_SHOW_SHUFFLE_REPEAT", True)
    show_progress = env_bool("SPOTIFY_SHOW_PROGRESS", True)
    show_ids      = env_bool("SPOTIFY_SHOW_IDS", False)

    max_recent  = env_int("SPOTIFY_MAX_RECENT", 50)
    daily_h     = env_int("SPOTIFY_DAILY_WINDOW_H", 24)
    weekly_days = env_int("SPOTIFY_WEEKLY_DAYS", 7)

    if apply_only:
        try:
            with open(OUT_TXT, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return (
                "SPOTIFY TELEMETRY — CLI FEED (Spotify ©)\n"
                "------------------------------------------------------------\n"
                "Status                    : UNKNOWN\n"
                f"Report generated ({tz_label})   : {fmt_utc(now)}\n"
            )

    state = load_state()
    prev = state.get("prev") or {}

    # ===== current playback =====
    token_ok = True
    http_status, api_class, cur = fetch_current(access)
    api_condition = api_condition_from(api_class, token_ok)

    status = "UNKNOWN"
    playback_state = "UNKNOWN"

    now_playing = "-"
    now_artist = ""
    now_title  = ""
    now_album  = ""
    now_device = ""
    now_shuffle = None
    now_repeat = None
    now_progress_ms = None
    now_duration_ms = None
    now_uri = ""
    now_id = ""

    if http_status == 204:
        status = "IDLE"
        playback_state = "OFFLINE (no active session)"
    elif http_status == 200 and isinstance(cur, dict):
        is_playing = cur.get("is_playing")
        status = "PLAYING" if is_playing is True else "IDLE"
        playback_state = "ONLINE (active session)" if is_playing is True else "OFFLINE (no active session)"

        item = cur.get("item") or {}
        now_artist, now_title = extract_track_line(item)
        now_album = (item.get("album") or {}).get("name") or ""
        now_progress_ms = cur.get("progress_ms")
        now_duration_ms = item.get("duration_ms")
        dev = cur.get("device") or {}
        now_device = dev.get("name") or ""
        now_shuffle = cur.get("shuffle_state")
        now_repeat = cur.get("repeat_state")
        now_uri = item.get("uri") or ""
        now_id = item.get("id") or ""

        if status == "PLAYING":
            now_playing = f"{now_artist} — {now_title}"
        else:
            now_playing = "-"
    else:
        status = "UNKNOWN"
        playback_state = "UNKNOWN"

    # ===== recently played (history) =====
    items = fetch_recent(access, max_recent)
    if not items:
        raise RuntimeError("Spotify returned empty recently-played feed (items=0).")

    first = items[0]
    last_track = first.get("track") or {}
    last_artist, last_title = extract_track_line(last_track)
    last_played_dt = parse_iso_utc(first.get("played_at"))
    last_played_s = fmt_utc(last_played_dt)
    last_track_line = f"{last_artist} — {last_title}"

    # ===== integrity =====
    integrity = "OK" if (last_artist and last_title and last_played_dt) else "PARTIAL"
    sitrep = sitrep_from(status, api_condition, integrity)
    confidence = confidence_level(api_condition, integrity)

    # ===== deltas =====
    prev_status = prev.get("status")
    prev_last = prev.get("last_played_utc")
    prev_now = prev.get("now_playing_fp")
    prev_gen = parse_iso_utc(prev.get("report_generated_utc"))

    now_fp = short_fp(now_playing) if now_playing != "-" else "NA"
    last_fp = short_fp(last_track_line)

    if not prev:
        d_track = "N/A (first report)"
        d_last  = "N/A (first report)"
        d_stat  = "N/A (first report)"
        d_time  = "N/A (first report)"
    else:
        d_track = "UNCHANGED" if prev_now == now_fp else "CHANGED"
        d_last  = "UNCHANGED" if prev_last == last_played_s else "UPDATED"
        d_stat  = "UNCHANGED" if prev_status == status else f"{prev_status} → {status}"
        d_time  = fmt_hms(int((now - prev_gen).total_seconds())) if prev_gen else "UNKNOWN"

    # ===== timing semantics (correct) =====
    # If PLAYING: show track position + remaining
    # If IDLE: show time since last played
    time_since_last_play = None
    if last_played_dt:
        time_since_last_play = int((now - last_played_dt).total_seconds())
    time_since_last_play = max(0, time_since_last_play or 0)

    pos_s = rem_s = None
    if status == "PLAYING" and isinstance(now_progress_ms, int) and isinstance(now_duration_ms, int) and now_duration_ms > 0:
        pos_s = now_progress_ms // 1000
        rem_s = max(0, (now_duration_ms - now_progress_ms) // 1000)

    # ===== daily/weekly counts from items timestamps =====
    daily_cut  = now - timedelta(hours=daily_h)
    weekly_cut = now - timedelta(days=weekly_days)

    count_24h = 0
    count_7d = 0
    artist_counts_24h = {}
    artist_counts_7d = {}

    def inc(d, k):
        d[k] = d.get(k, 0) + 1

    for it in items:
        dt = parse_iso_utc(it.get("played_at"))
        if not dt:
            continue
        t = it.get("track") or {}
        a, _ = extract_track_line(t)
        if dt >= daily_cut:
            count_24h += 1
            inc(artist_counts_24h, a)
        if dt >= weekly_cut:
            count_7d += 1
            inc(artist_counts_7d, a)

    dom_24 = max(artist_counts_24h, key=artist_counts_24h.get) if artist_counts_24h else "N/A"
    dom_7d = max(artist_counts_7d, key=artist_counts_7d.get) if artist_counts_7d else "N/A"

    daily_activity = cadence_label(count_24h)
    weekly_cadence = cadence_label(count_7d)

    # ===== render =====
    out = []
    out.append("SPOTIFY TELEMETRY — CLI FEED (Spotify ©)")
    out.append("------------------------------------------------------------")

    if show_header:
        out.append("Telemetry source          : Spotify Web API")
        out.append("Acquisition mode          : OAuth2 / automated workflow")
        out.append("Snapshot type             : Current playback + recent history")
        out.append(f"History window (max)      : {max_recent} events")
        out.append("------------------------------------------------------------")

    if show_core:
        out.append(f"Status                    : {status}")
        out.append(f"Playback state            : {playback_state}")
        out.append(f"SITREP                    : {sitrep}")
        out.append("------------------------------------------------------------")

    # NOW PLAYING (pure data)
    if show_now_det:
        out.append(f"Now playing               : {now_playing}")
        if status == "PLAYING":
            if now_album:
                out.append(f"Album                     : {now_album}")
            if show_device and now_device:
                out.append(f"Device                    : {now_device}")
            if show_sr:
                if now_shuffle is not None:
                    out.append(f"Shuffle                   : {'ON' if now_shuffle else 'OFF'}")
                if now_repeat:
                    out.append(f"Repeat                    : {str(now_repeat).upper()}")
            if show_progress and pos_s is not None and rem_s is not None:
                out.append(f"Track position            : {fmt_hms(pos_s)}")
                out.append(f"Time remaining            : {fmt_hms(rem_s)}")
            if show_volume:
                dev = cur.get("device") if isinstance(cur, dict) else {}
                vol = (dev or {}).get("volume_percent")
                if isinstance(vol, int):
                    out.append(f"Volume                    : {vol}%")
            if show_ids:
                if now_id:
                    out.append(f"Track ID                  : {now_id}")
                if now_uri:
                    out.append(f"Track URI                 : {now_uri}")
        out.append("------------------------------------------------------------")

    if show_last:
        out.append(f"Last played               : {last_track_line}")
        out.append(f"Last played ({tz_label})         : {last_played_s}")
        out.append("------------------------------------------------------------")

    if show_deltas:
        out.append(f"Δ now playing (since last): {d_track}")
        out.append(f"Δ last played (since last): {d_last}")
        out.append(f"Δ status (since last)     : {d_stat}")
        out.append("------------------------------------------------------------")

    if show_timing:
        if status == "PLAYING" and pos_s is not None and rem_s is not None:
            out.append(f"Time since last play      : N/A (live session)")
        else:
            out.append(f"Time since last play      : {fmt_hms(time_since_last_play)}")
        out.append(f"Δ time (since last report): {d_time}")
        out.append("------------------------------------------------------------")

    if show_api:
        out.append(f"API response class        : {api_class}")
        out.append(f"API condition             : {api_condition}")
        def scope_compact(scope_str: str) -> str:
            s = (scope_str or "").split()
            if not s:
                return "N/A"
            m = {
                "user-read-playback-state": "PLAYBACK_STATE",
                "user-read-currently-playing": "NOW_PLAYING",
                "user-read-recently-played": "RECENT",
            }
            mapped = [m.get(x, x) for x in s]
            return ", ".join(mapped)
        
        out.append(f"Auth scope                : {scope_compact(scope)}")
        out.append("------------------------------------------------------------")

    if show_integr:
        out.append(f"Data integrity            : {integrity}")
        out.append(f"Confidence level          : {confidence}")
        out.append("------------------------------------------------------------")

    if show_daily:
        out.append("DAILY SPOTIFY SITREP")
        out.append("------------------------------------------------------------")
        out.append(f"Tracks played (last {daily_h}h)   : {count_24h}")
        out.append(f"Dominant artist           : {dom_24}")
        out.append(f"Daily activity status     : {daily_activity}")
        out.append("------------------------------------------------------------")

    if show_weekly:
        out.append("WEEKLY CADENCE SUMMARY")
        out.append("------------------------------------------------------------")
        out.append(f"Week window ({tz_label})         : {fmt_utc(weekly_cut)} → {fmt_utc(now)}")
        out.append(f"Total tracks played       : {count_7d}")
        out.append(f"Dominant artist           : {dom_7d}")
        out.append(f"Cadence classification    : {weekly_cadence}")
        out.append("------------------------------------------------------------")

    out.append(f"Report generated ({tz_label})    : {fmt_utc(now)}")

    report = "\n".join(out).rstrip() + "\n"

    # Save state for deltas
    state["prev"] = {
        "status": status,
        "last_played_utc": last_played_s,
        "now_playing_fp": now_fp,
        "report_generated_utc": fmt_utc(now),
        "last_track_fp": last_fp,
    }
    save_state(state)

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(report)

    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-only", action="store_true")
    args = ap.parse_args()

    if args.apply_only:
        report = build_report(access="", scope="", apply_only=True)
        apply_to_readme(report)
        return

    client_id = (os.environ.get("SPOTIFY_CLIENT_ID") or "").strip()
    client_secret = (os.environ.get("SPOTIFY_CLIENT_SECRET") or "").strip()
    refresh_token = (os.environ.get("SPOTIFY_REFRESH_TOKEN") or "").strip()

    if not (client_id and client_secret and refresh_token):
        raise SystemExit("Missing Spotify secrets: SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIFY_REFRESH_TOKEN")

    access, scope = token_refresh(client_id, client_secret, refresh_token)
    report = build_report(access=access, scope=scope, apply_only=False)
    apply_to_readme(report)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
