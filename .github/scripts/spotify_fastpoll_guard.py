#!/usr/bin/env python3
import base64
import json
import os
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

FAST_CRON = "* * * * *"

def out(key: str, val: str) -> None:
    # GitHub Actions outputs
    p = os.environ.get("GITHUB_OUTPUT", "")
    if not p:
        # fallback (shouldn't happen on Actions)
        print(f"{key}={val}")
        return
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{key}={val}\n")

def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def http_json(url: str, headers=None, data: bytes | None = None, timeout: int = 20):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace").strip()
        payload = json.loads(raw) if raw else None
        return r.status, payload

def spotify_refresh_token(client_id: str, client_secret: str, refresh_token: str) -> str | None:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode("utf-8")

    try:
        status, payload = http_json(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=body,
            timeout=20,
        )
        if status >= 400 or not isinstance(payload, dict):
            return None
        return payload.get("access_token")
    except Exception:
        return None

def spotify_get(url: str, token: str):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8", "replace").strip()
            payload = json.loads(raw) if raw else None
            return r.status, payload
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return 204, None
        try:
            raw = e.read().decode("utf-8", "replace").strip()
            payload = json.loads(raw) if raw else raw
        except Exception:
            payload = None
        return e.code, payload
    except Exception:
        return -1, None

def load_latch(path: Path) -> bool:
    # armed=true by default
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return bool(obj.get("armed", True))
    except Exception:
        return True

def save_latch(path: Path, armed: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    obj = {"armed": bool(armed), "updated_utc": now_utc()}
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main():
    event_name = (os.environ.get("EVENT_NAME") or "").strip()
    schedule = (os.environ.get("SCHEDULE_CRON") or "").strip()

    enable_fast = (os.environ.get("ENABLE_FAST_POLL") or "false").strip().lower() == "true"
    mode = (os.environ.get("FAST_POLL_MODE") or "PLAYING_ONLY").strip().upper()
    latch_file = Path((os.environ.get("LATCH_FILE") or ".github/state/spotify_fastpoll_latch.json").strip())

    cid = (os.environ.get("SPOTIFY_CLIENT_ID") or "").strip()
    csec = (os.environ.get("SPOTIFY_CLIENT_SECRET") or "").strip()
    rt = (os.environ.get("SPOTIFY_REFRESH_TOKEN") or "").strip()

    # ------------------------------------------------------------
    # NORMAL PATH: manual run OR normal 3h cron
    # - Always allow (original behavior)
    # ------------------------------------------------------------
    if not (event_name == "schedule" and schedule == FAST_CRON):
        out("should_run", "true")
        out("reason", "normal_or_manual")
        out("changed_latch", "false")
        return

    # ------------------------------------------------------------
    # FAST POLL PATH: schedule + "* * * * *"
    # ------------------------------------------------------------
    if not enable_fast:
        out("should_run", "false")
        out("reason", "fast_poll_disabled")
        out("changed_latch", "false")
        return

    armed = load_latch(latch_file)

    # No secrets? => can't decide => don't spam.
    if not (cid and csec and rt):
        out("should_run", "false")
        out("reason", "missing_secrets")
        out("changed_latch", "false")
        return

    token = spotify_refresh_token(cid, csec, rt)
    if not token:
        out("should_run", "false")
        out("reason", "token_failed")
        out("changed_latch", "false")
        return

    # Primary: /me/player
    code, data = spotify_get("https://api.spotify.com/v1/me/player", token)

    playing = False
    why = "unknown"

    if code == 200 and isinstance(data, dict):
        if mode == "ANY_SESSION":
            dev = data.get("device")
            playing = isinstance(dev, dict) and bool(dev)
            why = "player_any_session"
        else:
            playing = bool(data.get("is_playing"))
            why = "player_is_playing"
    elif code == 204:
        # Fallback: /currently-playing (sometimes returns 200 when /player is 204)
        c2, d2 = spotify_get("https://api.spotify.com/v1/me/player/currently-playing", token)
        if c2 == 200 and isinstance(d2, dict):
            playing = bool(d2.get("is_playing"))
            why = "currently_playing_fallback"
        else:
            playing = False
            why = "no_active_player"
    else:
        playing = False
        why = f"player_http_{code}"

    changed = False

    # Latch algorithm:
    # - If NOT playing => re-arm latch (armed=true), skip.
    # - If playing:
    #     - If armed=true => trigger once and disarm (armed=false).
    #     - If armed=false => skip.
    if not playing:
        if not armed:
            save_latch(latch_file, True)
            changed = True
        out("should_run", "false")
        out("reason", f"not_playing_{why}")
        out("changed_latch", "true" if changed else "false")
        return

    # playing == True
    if armed:
        save_latch(latch_file, False)
        changed = True
        out("should_run", "true")
        out("reason", f"triggered_{why}")
        out("changed_latch", "true" if changed else "false")
        return

    out("should_run", "false")
    out("reason", f"already_triggered_{why}")
    out("changed_latch", "false")

if __name__ == "__main__":
    main()
