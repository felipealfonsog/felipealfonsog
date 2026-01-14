#!/usr/bin/env python3
import csv
import os
import socket
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------
NTP_DELTA = 2208988800

# Fallback list (NIST NTP endpoints; any one is fine)
NIST_HOSTS = [
    "time.nist.gov",
    "time-a-g.nist.gov",
    "time-b-g.nist.gov",
]

LOCAL_TZ = ZoneInfo("America/Santiago")

MEASUREMENTS = Path(os.getenv("WATCHOPS_MEASUREMENTS", "watchops/measurements.csv"))

WATCH_NAME = os.getenv("WATCHOPS_WATCH", "Festina").strip()
TOL_S = float(os.getenv("WATCHOPS_TOL_S", "5"))               # green <= tol
STALE_DAYS = float(os.getenv("WATCHOPS_STALE_DAYS", "7"))     # calibration older than this -> AMBER
NTP_TIMEOUT = float(os.getenv("WATCHOPS_NTP_TIMEOUT", "2.5"))


@dataclass
class Fit:
    drift_s_per_day: float
    offset_now_s: float
    last_epoch: int
    samples: int
    used_model: bool  # True if regression model, False if last-known


# -----------------------------
# NTP query (SNTP minimal)
# -----------------------------
def ntp_query(host: str, timeout: float = 2.5):
    """
    Minimal SNTP query. Returns (unix_time, ref_minus_midpoint, rtt_seconds)
    - unix_time: seconds since 1970 (UTC)
    - ref_minus_midpoint: reference_time - local_midpoint_time (seconds)
    - rtt: round-trip time seconds
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(timeout)

    # LI=0, VN=3, Mode=3 (client)
    msg = b"\x1b" + 47 * b"\0"

    t0 = time.time()
    client.sendto(msg, (host, 123))
    data, _ = client.recvfrom(1024)
    t3 = time.time()

    if len(data) < 48:
        raise RuntimeError("Invalid NTP reply")

    # Transmit timestamp is bytes 40..47 (seconds since 1900, plus fraction)
    sec, frac = struct.unpack("!II", data[40:48])
    ntp_time = sec + frac / 2**32
    unix_time = ntp_time - NTP_DELTA

    midpoint = (t0 + t3) / 2.0
    ref_minus_mid = unix_time - midpoint
    rtt = t3 - t0
    return unix_time, ref_minus_mid, rtt


def pick_nist_time():
    last_err = None
    for h in NIST_HOSTS:
        try:
            unix_time, ref_minus_mid, rtt = ntp_query(h, timeout=NTP_TIMEOUT)
            return h, unix_time, ref_minus_mid, rtt
        except Exception as e:
            last_err = e
    raise RuntimeError(f"All NIST queries failed: {last_err}")


# -----------------------------
# Parsing helpers
# -----------------------------
def parse_epoch(epoch_raw: str, fallback_epoch: int) -> int:
    """
    Accepts:
    - UNIX epoch integer
    - NOW
    - ISO datetime:
        "2026-01-14 18:46:33"
        "2026-01-14T18:46:33-03:00"
        "2026-01-14T21:46:33Z"
    - empty -> fallback_epoch
    """
    s = (epoch_raw or "").strip()
    if not s:
        return fallback_epoch

    if s.upper() == "NOW":
        return fallback_epoch

    # Try integer epoch
    try:
        return int(s)
    except ValueError:
        pass

    # Try ISO parse
    # If no tz is provided, assume LOCAL_TZ.
    try:
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=LOCAL_TZ)
        return int(dt.timestamp())
    except Exception:
        # As a final fallback, use fallback_epoch
        return fallback_epoch


def watch_match(a: str, b: str) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


# -----------------------------
# Measurements
# -----------------------------
def load_measurements(now_epoch: int):
    """
    Reads MEASUREMENTS CSV and returns sorted list of (epoch, offset_s) for WATCH_NAME.
    Supports epoch=NOW / ISO / empty.
    Ensures timestamps are strictly increasing (fixes duplicates).
    """
    if not MEASUREMENTS.exists():
        return []

    rows = []
    with MEASUREMENTS.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if not watch_match(row.get("watch", ""), WATCH_NAME):
                continue

            try:
                off = float(str(row.get("offset_s", "")).strip())
            except Exception:
                continue

            e = parse_epoch(str(row.get("epoch", "")), fallback_epoch=now_epoch)
            rows.append((e, off))

    rows.sort(key=lambda x: x[0])

    # Fix duplicate/non-increasing epochs (common when using NOW twice)
    fixed = []
    last_e = None
    for e, off in rows:
        if last_e is None:
            fixed.append((e, off))
            last_e = e
            continue
        if e <= last_e:
            e = last_e + 1
        fixed.append((e, off))
        last_e = e

    return fixed


# -----------------------------
# Drift model (linear regression)
# -----------------------------
def linear_fit(rows, now_epoch: int) -> Fit | None:
    """
    Fit offset = a + b * t_days via least squares.
    Returns b = drift(s/day), and predicted offset at now.

    If we don't have >=2 points, returns None.
    """
    if len(rows) < 2:
        return None

    ts = [e / 86400.0 for e, _ in rows]
    os_ = [o for _, o in rows]
    n = len(rows)

    sum_t = sum(ts)
    sum_o = sum(os_)
    sum_tt = sum(t * t for t in ts)
    sum_to = sum(t * o for t, o in zip(ts, os_))

    denom = n * sum_tt - sum_t * sum_t
    if abs(denom) < 1e-12:
        return None

    b = (n * sum_to - sum_t * sum_o) / denom  # s/day
    a = (sum_o - b * sum_t) / n

    t_now = now_epoch / 86400.0
    o_now = a + b * t_now
    last_epoch = rows[-1][0]
    return Fit(drift_s_per_day=b, offset_now_s=o_now, last_epoch=last_epoch, samples=n, used_model=True)


# -----------------------------
# Status logic
# -----------------------------
def status_lines(abs_offset: float, age_days: float, has_data: bool, has_model: bool):
    """
    Returns (status_line, note_line)
    """
    if not has_data:
        return "STATUS: BLUE ℹ️ AWAITING CALIBRATION", "NOTE: Add measurements for Festina offset vs UTC(NIST)."

    # Stale calibration takes priority over red/yellow/green to avoid misleading "RED" on old logs.
    if age_days > STALE_DAYS:
        return "STATUS: AMBER 🟠 CALIBRATION STALE", f"NOTE: Last calibration is {age_days:.1f} days old."

    # Fresh calibration: compute tolerance status
    if abs_offset <= TOL_S:
        return "STATUS: GREEN ✅ TIME DISCIPLINE: NOMINAL", "NOTE: Within tolerance."
    if abs_offset <= (2 * TOL_S):
        return "STATUS: YELLOW ⚠️ TIME DISCIPLINE: DEGRADED", "NOTE: Near tolerance boundary."
    return "STATUS: RED 🛑 TIME DISCIPLINE: OUT OF TOL", "NOTE: Requires correction."


# -----------------------------
# Formatting helpers
# -----------------------------
def fmt(ts: float, tz) -> str:
    return datetime.fromtimestamp(ts, tz=tz).strftime("%Y-%m-%d %H:%M:%S")


def main():
    # 1) Query NIST time
    host, unix_time, ref_minus_mid, rtt = pick_nist_time()
    now_epoch = int(unix_time)

    utc_str = fmt(unix_time, timezone.utc) + "Z"
    local_dt = datetime.fromtimestamp(unix_time, tz=LOCAL_TZ)
    local_str = local_dt.strftime("%Y-%m-%d %H:%M:%S %z") + f" ({LOCAL_TZ.key})"

    # 2) Load measurements
    rows = load_measurements(now_epoch)
    has_data = len(rows) >= 1

    # 3) Build model if possible
    fit = linear_fit(rows, now_epoch)

    if fit is None and has_data:
        # last-known mode (no drift model yet)
        last_epoch, last_offset = rows[-1]
        age_days = (now_epoch - last_epoch) / 86400.0

        status, note = status_lines(abs(last_offset), age_days, has_data=True, has_model=False)

        festina_line = f"- Watch: {WATCH_NAME}"
        drift_line = "- Drift (estimated): N/A (need ≥2 samples w/ distinct timestamps)"
        offset_line = f"- Offset vs UTC(NIST) (last known): {last_offset:+.2f} s"
        calib_line = f"- Calibration age: {age_days:.2f} days"
    elif fit is None and not has_data:
        status, note = status_lines(0.0, 0.0, has_data=False, has_model=False)
        festina_line = f"- Watch: {WATCH_NAME} (no measurements yet)"
        drift_line = "- Drift (estimated): N/A"
        offset_line = "- Offset vs UTC(NIST): N/A"
        calib_line = "- Calibration age: N/A"
    else:
        # regression model
        age_days = (now_epoch - fit.last_epoch) / 86400.0
        abs_off = abs(fit.offset_now_s)

        status, note = status_lines(abs_off, age_days, has_data=True, has_model=True)

        festina_line = f"- Watch: {WATCH_NAME}"
        drift_line = f"- Drift (estimated): {fit.drift_s_per_day:+.4f} s/day"
        offset_line = f"- Offset vs UTC(NIST) (estimated now): {fit.offset_now_s:+.2f} s"
        calib_line = f"- Calibration age: {age_days:.2f} days | Samples: {fit.samples}"

    block = f"""```text
TIME DISCIPLINE / SITREP
────────────────────────────────────────────────────────
REFERENCE: UTC(NIST) via NTP ({host})
UTC(NIST):   {utc_str}
LOCAL:       {local_str}

RUNNER vs NIST (ref-midpoint): {ref_minus_mid:+.6f} s
NETWORK RTT:                {rtt:.6f} s

{festina_line}
{drift_line}
{offset_line}
{calib_line}

{status}
{note}
────────────────────────────────────────────────────────
Last update: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}Z
```"""
    print(block)


if __name__ == "__main__":
    main()
