#!/usr/bin/env python3
import re
import time

README = "README.md"

with open(README, "r", encoding="utf-8") as f:
    md = f.read()

# expects a reference like: images/spotify_now.svg?v=123
pattern = re.compile(r"(images/spotify_now\.svg\?v=)(\d+)")
if not pattern.search(md):
    # If not found, do nothing (keeps your README intact).
    raise SystemExit(0)

md2 = pattern.sub(rf"\g<1>{int(time.time())}", md)

if md2 != md:
    with open(README, "w", encoding="utf-8") as f:
        f.write(md2)
