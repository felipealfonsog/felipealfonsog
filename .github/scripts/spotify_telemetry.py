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

AUTH_URL   = "https://accounts.spotify.com/api/token"
RECENT_URL = "https://api.spotify.com/v1/me/player/recently-played"
CURRENT_URL= "https://api.spotify.com/v1/me/player/currently-playing"

CACHE_DIR = ".cache"
OUT_TXT   = os.path.join(CACHE_DIR, "spotify_telemetry.txt")
STATE_JSON= os.path.join(CACHE_DIR, "spotify_state.json")
README    = "README.md"

MARK_START = "<!-- SPOTIFY_TEL:START -->"
MARK_END   = "<!-- SPOTIFY_TEL:END -->"

def env_bool(name: str, default: bool = True) -> bool:
    v = os.environ.get(name, "").strip()
    if v == "":
        return default
    return v not in ("0", "false", "False", "no", "NO")

def env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    if not v:
        return default
    try:
        return int(v)
    except Exception:
        return default

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def fmt_utc(dt: datetime | None) -> str:
    if not dt:
        return "N/A"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def fmt_hms(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

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

    code, headers, payload = http_json(
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

def current_status(access_token: str) -> tuple[str, str, str]:
    """
    Returns: (status, playback_state, api_class)
      status: PLAYING / IDLE / UNKNOWN
      playback_state: ONLINE / OFFLINE / UNKNOWN (human readable)
      api_class: "200 OK" / "204 NO CONTENT" / "401" etc
    """
    req = urllib.request.Request(
        CURRENT_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            api_class = f"{r.status} {'OK' if r.status==200 else ('NO CONTENT' if r.status==204 else '')}".strip()
            if r.status == 204:
                return "IDLE", "OFFLINE (no active session)", api_class
            if r.status == 200:
                raw = r.read().decode("utf-8", "replace").strip()
                if not raw:
                    return "IDLE", "OFFLINE (no active session)", api_class
                data = json.loads(raw)
                if data.get("is_playing") is True:
                    return "PLAYING", "ONLINE (active session)", api_class
                return "IDLE", "OFFLINE (no active session)", api_class
            return "UNKNOWN", "UNKNOWN", api_class
    except urllib.error.HTTPError as e:
        return "UNKNOWN", "UNKNOWN", f"{e.code}"
    except Exception:
        return "UNKNOWN", "UNKNOWN", "NETWORK/UNKNOWN"

def fetch_recent(access_token: str, limit: int) -> list[dict]:
    url = RECENT_URL + "?" + urllib.parse.urlencode({"limit": str(limit)})
    code, _, payload = http_json(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=25)
    if code >= 400 or not isinstance(payload, dict):
        raise RuntimeError(f"Spotify API error (recently-played) HTTP {code}.")
    return payload.get("items") or []

def track_line(item: dict) -> tuple[str, str, datetime | None]:
    track = item.get("track") or {}
    artists = track.get("artists") or []
    artist = ", ".join([a.get("name", "") for a in artists if a.get("name")]) or "Unknown artist"
    title = track.get("name") or "Unknown track"
    played_at = item.get("played_at") or ""
    dt = None
    try:
        dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
    except Exception:
        dt = None
    return artist, title, dt

def short_fingerprint(artist: str, title: str) -> str:
    import hashlib
    h = hashlib.sha256((artist + "—" + title).encode("utf-8", "replace")).hexdigest()
    return h[:8]

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
    # Simple, stable mapping:
    # - GREEN if playing and api normal
    # - AMBER if idle but healthy
    # - RED if unknown/degraded or integrity bad
    if integrity != "OK":
        return "RED"
    if api_condition != "NORMAL":
        return "AMBER" if status in ("PLAYING", "IDLE") else "RED"
    return "GREEN" if status == "PLAYING" else "AMBER" if status == "IDLE" else "RED"

def api_condition_from(api_class: str, token_ok: bool) -> str:
    if not token_ok:
        return "DEGRADED"
    if api_class.startswith("200") or api_class.startswith("204"):
        return "NORMAL"
    if api_class in ("NETWORK/UNKNOWN", "UNKNOWN"):
        return "DEGRADED"
    return "DEGRADED"

def confidence_level(telemetry_age_s: int, api_condition: str, integrity: str) -> str:
    if integrity != "OK":
        return "LOW"
    if api_condition != "NORMAL":
        return "MEDIUM"
    if telemetry_age_s <= 30*60:
        return "HIGH"
    if telemetry_age_s <= 3*60*60:
        return "MEDIUM"
    return "LOW"

def cadence_label(count_24h: int) -> str:
    if count_24h >= 25:
        return "HIGH"
    if count_24h >= 8:
        return "MODERATE"
    return "LOW"

def listening_pattern(count_3h: int, status: str) -> str:
    if status == "PLAYING":
        return "LIVE"
    if count_3h >= 6:
        return "FOCUSED"
    if count_3h >= 2:
        return "CASUAL"
    return "QUIET"

def build_report(access: str, scope: str, apply_only: bool = False) -> str:
    now = utc_now()

    show_header   = env_bool("SPOTIFY_SHOW_HEADER", True)
    show_core     = env_bool("SPOTIFY_SHOW_CORE_STATUS", True)
    show_deltas   = env_bool("SPOTIFY_SHOW_DELTAS", True)
    show_timing   = env_bool("SPOTIFY_SHOW_TIMING", True)
    show_api      = env_bool("SPOTIFY_SHOW_API_HEALTH", True)
    show_integr   = env_bool("SPOTIFY_SHOW_INTEGRITY", True)
    show_daily    = env_bool("SPOTIFY_SHOW_DAILY_SITREP", True)
    show_weekly   = env_bool("SPOTIFY_SHOW_WEEKLY_SUMMARY", True)

    obs_min       = env_int("SPOTIFY_OBS_WINDOW_MIN", 30)
    daily_h       = env_int("SPOTIFY_DAILY_WINDOW_H", 24)
    weekly_days   = env_int("SPOTIFY_WEEKLY_DAYS", 7)
    max_recent    = env_int("SPOTIFY_MAX_RECENT", 50)
    tz_label      = os.environ.get("SPOTIFY_TZ_LABEL", "UTC").strip() or "UTC"

    # If apply-only, we do not hit APIs; we just use last cached OUT_TXT.
    if apply_only:
        try:
            with open(OUT_TXT, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            # fallback minimal
            return (
                "SPOTIFY TELEMETRY — CLI FEED (Spotify ©)\n"
                "------------------------------------------------------------\n"
                "Status                    : UNKNOWN\n"
                f"Report generated ({tz_label})   : {fmt_utc(now)}\n"
            )

    state = load_state()

    # Status (currently-playing)
    token_ok = True
    try:
        status, playback_state, api_class = current_status(access)
    except Exception:
        status, playback_state, api_class = "UNKNOWN", "UNKNOWN", "NETWORK/UNKNOWN"

    api_condition = api_condition_from(api_class, token_ok)

    # Recently played
    items = fetch_recent(access, max_recent)
    if not items:
        raise RuntimeError("Spotify returned empty recently-played feed (items=0).")

    last_artist, last_title, last_played_dt = track_line(items[0])
    last_played_s = fmt_utc(last_played_dt)

    # Now playing line (best effort): if playing, use current item when available
    now_playing_line = "-"
    last_activity_type = "TRACK_END"  # default heuristic
    if status == "PLAYING":
        # In currently-playing, we didn't capture track details; keep it conservative:
        now_playing_line = "(LIVE) — See track in card/UI"
        last_activity_type = "PLAYBACK_ACTIVE"

    # Timing
    telemetry_age_s = 0
    if last_played_dt:
        telemetry_age_s = int((now - last_played_dt).total_seconds())
    telemetry_age_s = max(0, telemetry_age_s)

    # Observation window note / cache
    obs_window_s = obs_min * 60

    # Deltas vs last report
    prev = state.get("prev") or {}
    prev_status = prev.get("status")
    prev_last_played = prev.get("last_played_utc")
    prev_fingerprint = prev.get("track_fp")

    track_fp = short_fingerprint(last_artist, last_title)

    if not prev:
        delta_track = "N/A (first report)"
        delta_last  = "N/A (first report)"
        delta_stat  = "N/A (first report)"
        delta_dist  = "N/A (first report)"
    else:
        delta_track = "UNCHANGED" if prev_fingerprint == track_fp else "CHANGED"
        if prev_last_played == last_played_s:
            delta_last = "UNCHANGED"
        else:
            delta_last = "UPDATED"
        delta_stat = "UNCHANGED" if prev_status == status else f"{prev_status} → {status}"
        # time since last report
        try:
            prev_gen = datetime.fromisoformat(prev.get("report_generated_utc").replace("Z", "+00:00"))
            delta_dist = fmt_hms(int((now - prev_gen).total_seconds()))
        except Exception:
            delta_dist = "UNKNOWN"

    # Daily / weekly aggregations from recently-played timestamps
    # Rolling windows (UTC)
    daily_cut = now - timedelta(hours=daily_h)
    weekly_cut = now - timedelta(days=weekly_days)
    last3h_cut = now - timedelta(hours=3)

    count_24h = 0
    count_7d  = 0
    count_3h  = 0
    sec_24h   = 0
    sec_7d    = 0
    artist_counts_24h = {}
    artist_counts_7d = {}

    def inc(d, k):
        d[k] = d.get(k, 0) + 1

    for it in items:
        a, t, dt = track_line(it)
        if not dt:
            continue
        # Spotify “recently-played” doesn’t include track duration reliably in this endpoint payload across all shapes;
        # so we count plays as cadence telemetry; time totals are best-effort "N/A" unless you later enrich via another endpoint.
        if dt >= daily_cut:
            count_24h += 1
            inc(artist_counts_24h, a)
        if dt >= weekly_cut:
            count_7d += 1
            inc(artist_counts_7d, a)
        if dt >= last3h_cut:
            count_3h += 1

    dominant_artist_24h = max(artist_counts_24h, key=artist_counts_24h.get) if artist_counts_24h else "N/A"
    dominant_artist_7d  = max(artist_counts_7d,  key=artist_counts_7d.get)  if artist_counts_7d  else "N/A"

    daily_pattern = listening_pattern(count_3h, status)
    daily_activity_status = cadence_label(count_24h)
    weekly_cadence = cadence_label(count_7d)

    integrity = "OK" if (last_artist and last_title and last_played_dt) else "PARTIAL"
    sitrep = sitrep_from(status, api_condition, integrity)
    confidence = confidence_level(telemetry_age_s, api_condition, integrity)

    # Render report
    out = []
    out.append("SPOTIFY TELEMETRY — CLI FEED (Spotify ©)")
    out.append("------------------------------------------------------------")

    if show_header:
        out.append(f"Telemetry source          : Spotify Web API")
        out.append(f"Acquisition mode          : OAuth2 / automated workflow")
        out.append(f"Snapshot type             : Last-known playback state")
        out.append(f"Observation window        : {fmt_hms(obs_window_s)}")
        out.append("------------------------------------------------------------")

    if show_core:
        out.append(f"Status                    : {status}")
        out.append(f"Playback state            : {playback_state}")
        out.append(f"SITREP                    : {sitrep}")
        out.append("------------------------------------------------------------")

    out.append(f"Now playing               : {now_playing_line}")
    out.append(f"Last played               : {last_artist} — {last_title}")
    out.append(f"Last played ({tz_label})        : {last_played_s}")
    out.append(f"Last activity type        : {last_activity_type}")
    out.append("------------------------------------------------------------")

    if show_deltas:
        out.append(f"Δ track (since last)      : {delta_track}")
        out.append(f"Δ last played (since last): {delta_last}")
        out.append(f"Δ status (since last)     : {delta_stat}")
        out.append("------------------------------------------------------------")

    if show_timing:
        out.append(f"Time since last play      : {fmt_hms(telemetry_age_s)}")
        out.append(f"Telemetry age             : {fmt_hms(telemetry_age_s)}")
        if prev:
            out.append(f"Δ time (since last report): {delta_dist}")
        else:
            out.append(f"Δ time (since last report): N/A (first report)")
        out.append("------------------------------------------------------------")

    if show_api:
        out.append(f"API response class        : {api_class}")
        out.append(f"API condition             : {api_condition}")
        out.append(f"Auth scope                : {scope or 'N/A'}")
        out.append("------------------------------------------------------------")

    if show_integr:
        out.append(f"Data integrity            : {integrity}")
        out.append(f"Confidence level          : {confidence}")
        out.append("------------------------------------------------------------")

    if show_daily:
        out.append("DAILY SPOTIFY SITREP")
        out.append("------------------------------------------------------------")
        out.append(f"Tracks played (last {daily_h}h)   : {count_24h}")
        out.append(f"Dominant artist           : {dominant_artist_24h}")
        out.append(f"Listening pattern         : {daily_pattern}")
        out.append(f"Daily activity status     : {daily_activity_status}")
        out.append("------------------------------------------------------------")

    if show_weekly:
        out.append("WEEKLY CADENCE SUMMARY")
        out.append("------------------------------------------------------------")
        out.append(f"Week window ({tz_label})         : {fmt_utc(weekly_cut)} → {fmt_utc(now)}")
        out.append(f"Total tracks played       : {count_7d}")
        out.append(f"Dominant artist           : {dominant_artist_7d}")
        out.append(f"Cadence classification    : {weekly_cadence}")
        out.append("------------------------------------------------------------")

    out.append(f"Report generated ({tz_label})   : {fmt_utc(now)}")

    report = "\n".join(out).rstrip() + "\n"

    # Save state for next run
    state["prev"] = {
        "status": status,
        "last_played_utc": last_played_s,
        "track_fp": track_fp,
        "report_generated_utc": fmt_utc(now),
    }
    save_state(state)

    # Save cached text
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(report)

    return report

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-only", action="store_true", help="Do not hit Spotify; apply cached telemetry text to README.")
    args = ap.parse_args()

    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

    if args.apply_only:
        report = build_report(access="", scope="", apply_only=True)
        apply_to_readme(report)
        return

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
