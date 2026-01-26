---

## 2) Script — `.github/scripts/spotify_cli_report.py`

```python
#!/usr/bin/env python3
import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

README_PATH = "README.md"
STATE_PATH = "data/spotify_last.json"

AUTH_URL = "https://accounts.spotify.com/api/token"
PLAYER_URL = "https://api.spotify.com/v1/me/player"
RECENT_URL = "https://api.spotify.com/v1/me/player/recently-played?limit=1"

MARKER_START = "<!-- SPOTIFYCLI:START -->"
MARKER_END   = "<!-- SPOTIFYCLI:END -->"

def utc_now_s() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 25):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if not raw:
                return r.getcode(), {}, None
            return r.getcode(), dict(r.headers), json.loads(raw.decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raw = e.read() if hasattr(e, "read") else b""
        payload = None
        if raw:
            try:
                payload = json.loads(raw.decode("utf-8", "replace"))
            except Exception:
                payload = {"raw": raw[:500].decode("utf-8", "replace")}
        return e.code, dict(getattr(e, "headers", {}) or {}), payload
    except Exception as e:
        raise RuntimeError(f"HTTP failure: {e}")

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

    if code >= 400:
        raise RuntimeError(f"Token refresh failed (HTTP {code}): {payload}")

    token = (payload or {}).get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in response: {payload}")
    return token

def get_player(access_token: str):
    # 204 => no active device / idle
    req = urllib.request.Request(
        PLAYER_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status == 204:
                return 204, None
            raw = r.read().decode("utf-8", "replace").strip()
            if not raw:
                return r.status, None
            return r.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return 204, None
        raw = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        return e.code, {"error": raw[:500]}
    except Exception as e:
        raise RuntimeError(f"Player fetch failed: {e}")

def get_recent(access_token: str):
    code, _, payload = http_json(
        RECENT_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=25,
    )
    if code >= 400:
        raise RuntimeError(f"Recently-played failed (HTTP {code}): {payload}")

    items = (payload or {}).get("items") or []
    if not items:
        return None

    it = items[0]
    track = it.get("track") or {}
    artists = track.get("artists") or []
    artist = ", ".join([a.get("name", "") for a in artists if a.get("name")]) or "Unknown artist"
    title = track.get("name") or "Unknown track"
    played_at = it.get("played_at") or ""
    track_id = track.get("id") or ""
    track_url = (track.get("external_urls") or {}).get("spotify") or ""

    return {
        "artist": artist,
        "title": title,
        "played_at": played_at,
        "track_id": track_id,
        "track_url": track_url,
    }

def iso_to_dt(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def human_delta_seconds(sec: float) -> str:
    sec = int(round(sec))
    sign = "+" if sec >= 0 else "-"
    sec = abs(sec)
    d = sec // 86400
    h = (sec % 86400) // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if d > 0:
        return f"{sign}{d}d {h:02d}h {m:02d}m"
    if h > 0:
        return f"{sign}{h}h {m:02d}m"
    if m > 0:
        return f"{sign}{m}m {s:02d}s"
    return f"{sign}{s}s"

def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def build_report(player_status: int, player: dict | None, recent: dict | None, prev: dict):
    generated = utc_now_s()

    # NOW PLAYING (if available)
    now_title = "-"
    now_artist = "-"
    device = "-"
    progress = "-"
    status = "UNKNOWN"
    sitrep = "AMBER"

    if player_status == 204 or not player:
        # Idle / no active device
        status = "IDLE"
        sitrep = "AMBER"
    else:
        is_playing = player.get("is_playing")
        item = player.get("item") or {}
        artists = item.get("artists") or []
        now_artist = ", ".join([a.get("name", "") for a in artists if a.get("name")]) or "-"
        now_title = item.get("name") or "-"
        dev = player.get("device") or {}
        device = (dev.get("name") or "-").strip() or "-"
        prog_ms = player.get("progress_ms")
        dur_ms = (item.get("duration_ms") or 0) if item else 0
        if isinstance(prog_ms, int) and dur_ms:
            progress = f"{prog_ms//1000}s / {dur_ms//1000}s"
        elif isinstance(prog_ms, int):
            progress = f"{prog_ms//1000}s"
        else:
            progress = "-"

        if is_playing is True:
            status = "PLAYING"
            sitrep = "GREEN"
        else:
            status = "IDLE"
            sitrep = "AMBER"

    # LAST PLAYED (from recently-played)
    last_line = "-"
    last_played_dt = None
    last_track_id = ""
    if recent:
        last_line = f"{recent['artist']} — {recent['title']}"
        last_played_dt = iso_to_dt(recent.get("played_at", ""))
        last_track_id = recent.get("track_id", "") or ""

    # Δ since last
    delta_lines = []
    if prev and (prev.get("last_track_id") or prev.get("last_played_at") or prev.get("status")):
        prev_track_id = prev.get("last_track_id", "")
        prev_played_dt = iso_to_dt(prev.get("last_played_at", ""))
        prev_status = prev.get("status", "")

        # Track delta
        if last_track_id and prev_track_id:
            if last_track_id == prev_track_id:
                delta_lines.append("Δ track (since last)      : SAME")
            else:
                delta_lines.append("Δ track (since last)      : CHANGED")
        else:
            delta_lines.append("Δ track (since last)      : N/A")

        # Last-played delta
        if last_played_dt and prev_played_dt:
            delta_sec = (last_played_dt - prev_played_dt).total_seconds()
            delta_lines.append(f"Δ last played (since last): {human_delta_seconds(delta_sec)}")
        else:
            delta_lines.append("Δ last played (since last): N/A")

        # Status delta
        if prev_status and status:
            delta_lines.append(f"Δ status (since last)     : {prev_status} -> {status}")
        else:
            delta_lines.append("Δ status (since last)     : N/A")
    else:
        delta_lines.append("Δ track (since last)      : N/A (first report)")
        delta_lines.append("Δ last played (since last): N/A (first report)")
        delta_lines.append("Δ status (since last)     : N/A (first report)")

    # Build CLI text
    out = []
    out.append("SPOTIFY TELEMETRY — CLI FEED (Spotify ©)")
    out.append("------------------------------------------------------------")
    out.append(f"Status                   : {status}")
    out.append(f"SITREP                   : {sitrep}")
    out.append("------------------------------------------------------------")

    if status == "PLAYING":
        out.append(f"Now playing              : {now_artist} — {now_title}")
        out.append(f"Device                   : {device}")
        out.append(f"Progress                 : {progress}")
    else:
        out.append("Now playing              : -")

    out.append(f"Last played              : {last_line}")
    if last_played_dt:
        out.append(f"Last played (UTC)        : {last_played_dt.strftime('%Y-%m-%d %H:%M:%SZ')}")
    else:
        out.append("Last played (UTC)        : -")

    out.append("------------------------------------------------------------")
    out.extend(delta_lines)
    out.append("------------------------------------------------------------")
    out.append(f"Report generated (UTC)   : {generated}")

    return "\n".join(out).rstrip() + "\n", {
        "status": status,
        "sitrep": sitrep,
        "last_track_id": last_track_id,
        "last_played_at": recent.get("played_at", "") if recent else "",
        "generated_utc": generated,
    }

def replace_block(readme: str, cli_text: str) -> str:
    pattern = re.compile(r"<!-- SPOTIFYCLI:START -->.*?<!-- SPOTIFYCLI:END -->", re.S)
    if not pattern.search(readme):
        raise RuntimeError("Markers not found: <!-- SPOTIFYCLI:START --> ... <!-- SPOTIFYCLI:END -->")

    block = (
        "<!-- SPOTIFYCLI:START -->\n"
        "```text\n"
        f"{cli_text}"
        "```\n"
        "<!-- SPOTIFYCLI:END -->"
    )
    return pattern.sub(block, readme)

def main():
    # Fail-safe philosophy:
    # - If token refresh fails => exit nonzero; DO NOT modify README/state.
    # - If recently-played fails => exit nonzero; DO NOT modify README/state.
    # - Player endpoint may be 204 (idle) => still OK; we can render.
    token = get_access_token()

    prev = load_state()

    # Player can fail soft (we still can render from recent)
    try:
        p_status, p_data = get_player(token)
    except Exception:
        p_status, p_data = 0, None  # unknown

    recent = get_recent(token)  # hard requirement for stable output
    if not recent:
        raise RuntimeError("Spotify returned no recently played items (items empty).")

    cli_text, new_state = build_report(p_status, p_data, recent, prev)

    with open(README_PATH, "r", encoding="utf-8") as f:
        md = f.read()

    md2 = replace_block(md, cli_text)

    # Only write after everything succeeded (atomic-ish)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(md2)

    save_state(new_state)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
