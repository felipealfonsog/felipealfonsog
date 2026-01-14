#!/usr/bin/env python3
import csv
import socket
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

NTP_DELTA = 2208988800
NIST_HOSTS = ["time.nist.gov", "time-a-g.nist.gov", "time-b-g.nist.gov"]  # fallback-ish
LOCAL_TZ = ZoneInfo("America/Santiago")

MEASUREMENTS = Path("watchops/measurements.csv")
WATCH_NAME = "Festina"

@dataclass
class Fit:
    drift_s_per_day: float
    offset_now_s: float
    last_epoch: int
    samples: int

def ntp_query(host: str, timeout: float = 2.5):
    """
    Minimal SNTP query. Returns (unix_time, offset_seconds_est, rtt_seconds)
    offset is runner_clock - NTP_reference (approx), sign consistent for display.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(timeout)
    msg = b"\x1b" + 47 * b"\0"

    t0 = time.time()
    client.sendto(msg, (host, 123))
    data, _ = client.recvfrom(1024)
    t3 = time.time()

    if len(data) < 48:
        raise RuntimeError("Invalid NTP reply")

    # Transmit timestamp in seconds since 1900
    sec, frac = struct.unpack("!II", data[40:48])
    ntp_time = sec + frac / 2**32
    unix_time = ntp_time - NTP_DELTA

    # offset: reference - local midpoint (so positive means local behind)
    midpoint = (t0 + t3) / 2.0
    ref_minus_mid = unix_time - midpoint
    rtt = t3 - t0
    return unix_time, ref_minus_mid, rtt

def pick_nist_time():
    last_err = None
    for h in NIST_HOSTS:
        try:
            return h, *ntp_query(h)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"All NIST queries failed: {last_err}")

def load_measurements():
    if not MEASUREMENTS.exists():
        return []
    rows = []
    with MEASUREMENTS.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row.get("watch") == WATCH_NAME:
                try:
                    rows.append((int(row["epoch"]), float(row["offset_s"])))
                except Exception:
                    pass
    rows.sort(key=lambda x: x[0])
    return rows

def linear_fit(rows, now_epoch: int) -> Fit | None:
    """
    Fit offset = a + b * t_days using least squares.
    Returns drift b (s/day) and predicted offset at now.
    """
    if len(rows) < 2:
        return None

    ts = [e / 86400.0 for e, _ in rows]
    os = [o for _, o in rows]
    n = len(rows)

    sum_t = sum(ts)
    sum_o = sum(os)
    sum_tt = sum(t*t for t in ts)
    sum_to = sum(t*o for t, o in zip(ts, os))

    denom = n * sum_tt - sum_t * sum_t
    if abs(denom) < 1e-12:
        return None

    b = (n * sum_to - sum_t * sum_o) / denom          # s/day
    a = (sum_o - b * sum_t) / n

    t_now = now_epoch / 86400.0
    o_now = a + b * t_now
    last_epoch = rows[-1][0]
    return Fit(drift_s_per_day=b, offset_now_s=o_now, last_epoch=last_epoch, samples=n)

def fmt(ts, tz):
    return datetime.fromtimestamp(ts, tz=tz).strftime("%Y-%m-%d %H:%M:%S")

def status_from_offset(abs_offset, tol=5.0):
    if abs_offset <= tol:
        return "GREEN ✅ TIME DISCIPLINE: NOMINAL"
    if abs_offset <= tol*2:
        return "YELLOW ⚠️ TIME DISCIPLINE: DEGRADED"
    return "RED 🛑 TIME DISCIPLINE: OUT OF TOL"

def main():
    host, unix_time, ref_minus_mid, rtt = pick_nist_time()
    now_epoch = int(unix_time)

    utc_str = fmt(unix_time, timezone.utc) + "Z"
    local_dt = datetime.fromtimestamp(unix_time, tz=LOCAL_TZ)
    local_str = local_dt.strftime("%Y-%m-%d %H:%M:%S %z") + f" ({LOCAL_TZ.key})"

    rows = load_measurements()
    fit = linear_fit(rows, now_epoch)

    if fit is None:
        festina_line = f"- Watch: {WATCH_NAME} (no enough samples for drift model — add ≥2 measurements)"
        drift_line = "- Drift: N/A"
        offset_line = "- Estimated offset now: N/A"
        status_line = "STATUS: BLUE ℹ️ AWAITING CALIBRATION"
    else:
        abs_off = abs(fit.offset_now_s)
        festina_line = f"- Watch: {WATCH_NAME}"
        drift_line = f"- Drift (estimated): {fit.drift_s_per_day:+.4f} s/day"
        offset_line = f"- Offset vs UTC(NIST) (estimated now): {fit.offset_now_s:+.2f} s"
        status_line = f"STATUS: {status_from_offset(abs_off, tol=5.0)}"

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

{status_line}
────────────────────────────────────────────────────────
Last update: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}Z
```"""
    print(block)

if __name__ == "__main__":
    main()
