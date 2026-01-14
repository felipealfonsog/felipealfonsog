#### WATCHOPS / TIMEOPS — HOWTO (UTC(NIST) TIME DISCIPLINE)
======================================================

Author: Felipe Alfonso González - f.alfonso@res-ear.ch
Purpose: Maintain wristwatch time discipline synchronized to UTC(NIST),
         publish status telemetry on GitHub Profile README.

This guide explains:
- What the "TIME DISCIPLINE / SITREP" block means
- How to measure (calibrate) your watch offset vs UTC(NIST)
- How to keep status GREEN reliably
- Best practices for drift measurement and correction


0) DEFINITIONS (READ THIS FIRST)
--------------------------------

UTC(NIST)
  Atomic time reference maintained by NIST (USA) and served over NTP.

Offset (seconds)
  The difference between your watch and UTC(NIST), expressed in seconds.

  OFFSET DEFINITION (IMPORTANT):
    offset_s = (watch_time) - (UTC(NIST)_time)

  Meaning:
    + offset  => watch is AHEAD (fast)
    - offset  => watch is BEHIND (slow)

Drift (seconds/day)
  The daily rate at which your watch gains or loses time.

Tolerance
  The allowed offset range considered "in sync".
  Default: ±5 seconds


1) WHAT YOU SEE ON GITHUB (THE SITREP BLOCK)
-------------------------------------------

Example:

TIME DISCIPLINE / SITREP
────────────────────────────────────────────────────────
REFERENCE: UTC(NIST) via NTP (time.nist.gov)
UTC(NIST):   2026-01-14 21:46:33Z
LOCAL:       2026-01-14 18:46:33 -0300 (America/Santiago)

RUNNER vs NIST (ref-midpoint): +0.045233 s
NETWORK RTT:                0.097788 s

- Watch: Festina
- Drift (estimated): +0.6000 s/day
- Offset vs UTC(NIST) (estimated now): +2.30 s
- Calibration age: 0.15 days | Samples: 5

STATUS: GREEN ✅ TIME DISCIPLINE: NOMINAL
────────────────────────────────────────────────────────
Last update: 2026-01-14 21:46:33Z

What each field means:

A) REFERENCE
  The authoritative time reference: UTC(NIST), queried over NTP.

B) UTC(NIST)
  Current atomic reference time (UTC / Zulu time).

C) LOCAL
  Same moment in local time: America/Santiago.

D) RUNNER vs NIST (ref-midpoint)
  This is the GitHub Actions machine clock vs NIST (informational).
  It is NOT your Festina.

E) NETWORK RTT
  Network latency to the NIST server (informational).

F) Watch: Festina
  The tracked watch identity label. Generic (no model info).

G) Drift (estimated)
  Watch speed error in seconds per day (s/day).

H) Offset vs UTC(NIST)
  Estimated current difference between Festina and atomic reference.

I) Calibration age / Samples
  Age: how old the latest measurement is.
  Samples: number of measurements used.

J) STATUS
  Operational condition:
    GREEN ✅  : within tolerance
    YELLOW ⚠️ : degraded
    RED 🛑    : out of tolerance
    AMBER 🟠  : calibration stale (too old)
    BLUE ℹ️   : no measurements / awaiting calibration


2) WHY YOU MUST WRITE +2.3 OR -2.3 (AND WHY IT MATTERS)
-------------------------------------------------------

Your GitHub Action cannot read your physical watch.
So the system depends on YOU entering the offset.

The offset is the only way WatchOps can know:

- If your watch is ahead or behind
- By how many seconds
- How it changes over time (drift)

If you enter the wrong sign (+ instead of -), the model will be wrong.

This is why you must enter:
  -2.0, -1.0, +2.0, +3.0, etc.
instead of only "2.0" or "3.0".


3) UNDERSTANDING THE SIGN: WHEN TO WRITE "-" VS "+"
----------------------------------------------------

Offset definition again:

  offset_s = watch_time - reference_time

So:

A) When to write POSITIVE (+)
-----------------------------
Write a POSITIVE number when your Festina is AHEAD of UTC(NIST).

Example:
  UTC(NIST):  12:00:00
  Festina:    12:00:02
  offset = +2

You write:
  +2.0

Meaning:
  "My Festina is 2 seconds fast."

More examples:
  Festina shows 1 second ahead   => +1.0
  Festina shows 3 seconds ahead  => +3.0
  Festina shows 0.5 sec ahead    => +0.5


B) When to write NEGATIVE (-)
-----------------------------
Write a NEGATIVE number when your Festina is BEHIND UTC(NIST).

Example:
  UTC(NIST):  12:00:00
  Festina:    11:59:58
  offset = -2

You write:
  -2.0

Meaning:
  "My Festina is 2 seconds slow."

More examples:
  Festina shows 1 sec behind  => -1.0
  Festina shows 3 sec behind  => -3.0
  Festina shows 0.4 behind    => -0.4


4) WHY SOMETIMES YOU WRITE -1, THEN -2, THEN -3 (OR +1 → +2 → +3)
------------------------------------------------------------------

This happens because watches DRIFT over time.

Let’s assume your Festina is running slow:

Day 1:
  Festina is 1 second behind
  => -1.0

Day 2:
  Festina is now 2 seconds behind
  => -2.0

Day 3:
  Festina is now 3 seconds behind
  => -3.0

This shows the watch is consistently losing time.

If instead it runs fast:

Day 1:
  +1.0
Day 2:
  +2.0
Day 3:
  +3.0

This shows it is gaining time.

This series is exactly what allows WatchOps to compute drift.

Example drift computation:
- Day 1 offset: -1.0
- Day 3 offset: -3.0
Change = -3.0 - (-1.0) = -2.0 seconds
Time = 2 days
Drift = -2.0 / 2 = -1.0 s/day

Meaning:
  watch loses 1 second per day.


5) MOST COMMON OFFSET PATTERNS (HOW TO INTERPRET THEM)
------------------------------------------------------

Pattern A: offsets increase (+2 → +3 → +4)
  - Watch is fast (ahead)
  - It gains time each day
  - Drift is positive

Pattern B: offsets decrease (-1 → -2 → -3)
  - Watch is slow (behind)
  - It loses time each day
  - Drift is negative

Pattern C: offsets stay stable (+2.1 → +2.2 → +2.1)
  - Watch is stable
  - Drift is near zero
  - Excellent time discipline

Pattern D: sign flips (+2 → -1)
  - Usually means: you corrected the watch (set time)
  - Or you logged wrong sign by mistake
  - Make sure to add notes like "corrected"


6) WHERE YOU WRITE CALIBRATION DATA
-----------------------------------

File:
  watchops/measurements.csv

Header must be exactly:
  epoch,watch,offset_s,source,notes


7) HOW TO CALIBRATE (MEASURE OFFSET) STEP-BY-STEP
-------------------------------------------------

Tools (atomic reference):
- Preferred: https://time.gov/
- Acceptable: https://time.is/

Procedure:

STEP 1) Open the reference clock
  - Open time.gov or time.is
  - Ensure seconds are visible

STEP 2) Watch the reference seconds reach a boundary
  - The easiest is when it hits XX:XX:00 (second 00)

STEP 3) Compare your Festina at that exact moment
  - If your Festina already shows 00 earlier than reference -> it is ahead (+)
  - If your Festina reaches 00 after reference -> it is behind (-)

STEP 4) Estimate difference
  - Example: Festina is 2 seconds ahead -> +2.0
  - Example: Festina is 1 second behind -> -1.0

STEP 5) Log it into CSV
  Example:
    NOW,Festina,+2.3,time.gov,manual check


8) WHAT TO WRITE IN measurements.csv (EXACTLY)
----------------------------------------------

Recommended (GitHub-friendly):
Use epoch = NOW

Example:

epoch,watch,offset_s,source,notes
NOW,Festina,+2.3,time.gov,manual check #1
NOW,Festina,+2.9,time.gov,manual check #2


Field explanation:

epoch
  Use NOW.
  Why: no terminal required, GitHub Action resolves timestamp.

watch
  Use Festina (generic label).

offset_s
  The signed offset:
    + means ahead
    - means behind

source
  time.gov (best) or time.is

notes
  Optional comment


9) WHY YOU NEED 2+ MEASUREMENTS
-------------------------------

With 1 measurement:
- The system can show last-known offset
- No drift model

With 2+ measurements:
- Drift is calculated (seconds/day)
- Offset can be predicted and tracked automatically

Best practice:
- 5+ measurements for stability


10) HOW TO CORRECT YOUR WATCH (SET IT TO "SYNCED")
--------------------------------------------------

Goal:
- Keep offset near 0.0 seconds
- Maintain GREEN state

Quartz watch correction:

STEP 1) Pull crown to time-setting position
STEP 2) Wait until reference is near next minute boundary
STEP 3) Set the upcoming minute on your watch
STEP 4) Push crown exactly when reference hits second 00

After correction:
- Log offset near zero

Example:
  NOW,Festina,+0.0,time.gov,corrected


11) HOW TO KEEP STATUS GREEN RELIABLY (OPERATOR RULES)
------------------------------------------------------

Default tolerance is ±5 seconds.

Operational rule:
- Keep Festina within ±2 seconds whenever possible.
- If approaching ±4 seconds, correct immediately.

Recommended routine:
- Add a measurement every 2–7 days
- Always add a measurement after correction


12) RUNNING / TRIGGERING THE WORKFLOW
-------------------------------------

The Action updates your README on schedule.
To update immediately:

GitHub -> Actions -> select workflow -> Run workflow

Expected behavior:
- If README changed -> commit is pushed automatically
- If unchanged -> no commit


13) TROUBLESHOOTING
-------------------

STATUS: BLUE
  - No measurements found
  - Ensure watchops/measurements.csv exists and format is correct

STATUS: AMBER
  - Last calibration too old
  - Add a new NOW measurement

STATUS: RED
  - abs(offset) too large
  - Correct the watch and log new measurement

Drift seems wrong
  - measurements too close together OR wrong sign
  - add measurements spaced 12–24h
  - verify sign (+ ahead / - behind)


END OF DOCUMENT
