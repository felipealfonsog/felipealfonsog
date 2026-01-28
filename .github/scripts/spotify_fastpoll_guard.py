#!/usr/bin/env python3
import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

AUTH_URL = "https://accounts.spotify.com/api/token"
CURRENTLY_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"
PLAYER_URL = "https://api.spotify.com/v1/me/player"

def utc_now_s():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def http_json(url, headers=None, data=None, method=None, timeout=20):
    headers = headers or {}
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace").strip()
            if r.status == 204 or not raw:
                return r.status, None
            return r.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return 204, None
        try:
            raw = e.read().decode("utf-8", "replace").strip()
            payload = json.loads(raw) if raw else None
        except Exception:
            payload = None
        return e.code, payload
    except Exception:
        return -1, None

def refresh_access_token(cid, csec, rt):
    auth = base64.b64encode(f"{cid}:{csec}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": rt,
    }).encode("utf-8")

    code, payload = http_json(
        AUTH_URL,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=body,
        method="POST",
        timeout=20
    )
    if code != 200 or not isinstance(payload, dict):
        return None
    return payload.get("access_token")

def detect_playing(token):
    """
    Robust playback detection:
    1) /currently-playing (best for "is it playing NOW?")
    2) fallback /me/player
    """
    h = {"Authorization": f"Bearer {token}"}

    c_code, c_data = http_json(CURRENTLY_PLAYING_URL, headers=h, timeout=20)
    if c_code == 200 and isinstance(c_data, dict):
        return bool(c_data.get("is_playing")), "currently_playing"
    if c_code == 204:
        # fallback
        p_code, p_data = http_json(PLAYER_URL, headers=h, timeout=20)
        if p_code == 200 and isinstance(p_data, dict):
            return bool(p_data.get("is_playing")), "player_fallback"
        if p_code == 204:
            return False, "no_active_player"
        return False, f"player_http_{p_code}"
    return False, f"currently_http_{c_code}"

def load_latch(path):
    # default: armed=true
    obj = {"armed": True, "updated_utc": None, "last_trigger_epoch": 0}
    try:
        with open(path, "r", encoding="utf-8") as f:
            x = json.load(f)
        if isinstance(x, dict):
            obj["armed"] = bool(x.get("armed", True))
            obj["updated_utc"] = x.get("updated_utc", None)
            obj["last_trigger_epoch"] = int(x.get("last_trigger_epoch", 0) or 0)
    except Exception:
        pass
    return obj

def save_latch(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

def main():
    enable = (os.getenv("ENABLE_FAST_POLL", "false") or "false").strip().lower()
    mode = (os.getenv("FAST_POLL_MODE", "PLAYING_ONLY") or "PLAYING_ONLY").strip().upper()
    latch_file = (os.getenv("LATCH_FILE") or ".github/state/spotify_fastpoll_latch.json").strip()
    cooldown_min = int((os.getenv("LATCH_COOLDOWN_MINUTES", "20") or "20").strip())

    # Output contract for GitHub Actions: print should_run=...
    # Always be deterministic.
    if enable != "true":
        print("should_run=false")
        print("reason=fast_poll_disabled")
        print("changed_latch=false")
        return 0

    cid = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    csec = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    rt = os.getenv("SPOTIFY_REFRESH_TOKEN", "").strip()
    if not (cid and csec and rt):
        print("should_run=false")
        print("reason=missing_secrets")
        print("changed_latch=false")
        return 0

    tok = refresh_access_token(cid, csec, rt)
    if not tok:
        print("should_run=false")
        print("reason=token_refresh_failed")
        print("changed_latch=false")
        return 0

    playing, source = detect_playing(tok)

    # ANY_SESSION mode: treat "player exists" as "playing" is not correct.
    # You asked for ANY_SESSION earlier, but "currently-playing" is about playing.
    # We'll interpret ANY_SESSION as: if /me/player says device exists (and not 204).
    if mode == "ANY_SESSION" and not playing:
        p_code, p_data = http_json(PLAYER_URL, headers={"Authorization": f"Bearer {tok}"}, timeout=20)
        if p_code == 200 and isinstance(p_data, dict) and isinstance(p_data.get("device"), dict) and bool(p_data.get("device")):
            playing = True
            source = "any_session_device"

    latch = load_latch(latch_file)
    armed = bool(latch.get("armed", True))
    last_trigger_epoch = int(latch.get("last_trigger_epoch", 0) or 0)
    now_epoch = int(time.time())

    # Cooldown re-arm (anti “stuck false forever”)
    cooldown_s = cooldown_min * 60
    if (not armed) and last_trigger_epoch > 0 and (now_epoch - last_trigger_epoch) >= cooldown_s:
        armed = True

    changed = False
    should_run = False
    reason = "unknown"

    if not playing:
        # Not playing => re-arm
        if not armed:
            armed = True
            changed = True
        latch_out = {"armed": True, "updated_utc": utc_now_s(), "last_trigger_epoch": last_trigger_epoch}
        save_latch(latch_file, latch_out)
        print("should_run=false")
        print(f"reason=not_playing_{source}")
        print(f"changed_latch={'true' if changed else 'false'}")
        return 0

    # Playing:
    if armed:
        # First trigger => run and disarm
        should_run = True
        reason = f"triggered_{source}"
        latch_out = {"armed": False, "updated_utc": utc_now_s(), "last_trigger_epoch": now_epoch}
        save_latch(latch_file, latch_out)
        changed = True
    else:
        should_run = False
        reason = f"already_triggered_{source}"
        latch_out = {"armed": False, "updated_utc": utc_now_s(), "last_trigger_epoch": last_trigger_epoch}
        save_latch(latch_file, latch_out)

    print(f"should_run={'true' if should_run else 'false'}")
    print(f"reason={reason}")
    print(f"changed_latch={'true' if changed else 'false'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
