#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime, timezone

README = Path("README.md")

if not README.exists():
    raise SystemExit("README.md not found")

md = README.read_text(encoding="utf-8")

# Busca spotify_now.svg con o sin ?v=
pattern = re.compile(
    r"(spotify_now\.svg)(\?v=\d+)?"
)

# Nuevo valor de cache-bust: timestamp UTC
new_v = int(datetime.now(timezone.utc).timestamp())

def repl(m):
    return f"{m.group(1)}?v={new_v}"

new_md, n = pattern.subn(repl, md, count=1)

# Si no encontró nada, no hace nada (importante)
if n == 0:
    print("No spotify_now.svg reference found in README (nothing to bump).")
else:
    README.write_text(new_md, encoding="utf-8")
    print(f"Updated cache-bust to ?v={new_v}")
