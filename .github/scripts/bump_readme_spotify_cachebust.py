#!/usr/bin/env python3
import re
from pathlib import Path

README = Path("README.md")

def main():
    if not README.exists():
        return

    md = README.read_text(encoding="utf-8")

    # looks for spotify_now.svg?v=NUMBER
    pat = re.compile(r"(spotify_now\.svg\?v=)(\d+)")
    m = pat.search(md)
    if not m:
        return

    cur = int(m.group(2))
    nxt = cur + 1
    md2 = pat.sub(rf"\g<1>{nxt}", md, count=1)

    if md2 != md:
        README.write_text(md2, encoding="utf-8")

if __name__ == "__main__":
    main()
