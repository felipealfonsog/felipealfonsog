#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime, timezone

README = Path("README.md")
if not README.exists():
    raise SystemExit("README.md not found")

md = README.read_text(encoding="utf-8")

# Only bump the first occurrence to avoid collateral edits.
pattern = re.compile(r"(spotify_now\.svg)(\?v=\d+)?")
new_v = int(datetime.now(timezone.utc).timestamp())

def repl(m):
    return f"{m.group(1)}?v={new_v}"

new_md, n = pattern.subn(repl, md, count=1)

if n == 0:
    print("No spotify_now.svg reference found in README (nothing to bump).")
else:
    README.write_text(new_md, encoding="utf-8")
    print(f"Updated cache-bust to ?v={new_v}")
