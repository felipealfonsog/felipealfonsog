#!/usr/bin/env python3
import re
from pathlib import Path

README = Path("README.md")

def main():
    if not README.exists():
        return

    md = README.read_text(encoding="utf-8", errors="replace")

    # Match: spotify_now.svg?v=123  (keep same formatting)
    pat = re.compile(r"(spotify_now\.svg\?v=)(\d+)")
    m = pat.search(md)
    if not m:
        return

    current = int(m.group(2))
    new = current + 1

    md2 = pat.sub(rf"\g<1>{new}", md, count=1)
    README.write_text(md2, encoding="utf-8")

if __name__ == "__main__":
    main()
