#!/usr/bin/env python3
import re
import time
from pathlib import Path

README = Path("README.md")

if not README.exists():
    raise SystemExit("README.md not found")

md = README.read_text(encoding="utf-8")

# Busca spotify_now.svg?v=123 y lo reemplaza por un número nuevo
v = str(int(time.time()))
pattern = re.compile(r"(images/spotify_now\.svg\?v=)(\d+)")
if not pattern.search(md):
    # Si no existe, no rompas nada; solo sal.
    raise SystemExit("No spotify_now.svg?v=... reference found in README (nothing to bump).")

md2 = pattern.sub(r"\g<1>" + v, md)

README.write_text(md2, encoding="utf-8")
print(f"OK: bumped spotify cache-bust v={v}")
