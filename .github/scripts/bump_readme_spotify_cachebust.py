#!/usr/bin/env python3
import hashlib
import re

README = "README.md"
SVG = "images/spotify_now.svg"

def main():
    with open(SVG, "rb") as f:
        data = f.read()

    h = hashlib.sha256(data).hexdigest()[:10]

    with open(README, "r", encoding="utf-8") as f:
        md = f.read()

    pat = re.compile(r"<!-- SPOTIFY:START -->.*?<!-- SPOTIFY:END -->", re.S)
    m = pat.search(md)
    if not m:
        raise SystemExit("Markers not found: <!-- SPOTIFY:START --> ... <!-- SPOTIFY:END -->")

    block = m.group(0)

    # Replace any spotify_now.svg?v=... inside the block
    block2 = re.sub(r"(images/spotify_now\.svg\?v=)[A-Za-z0-9._-]+", r"\g<1>" + h, block)

    # If the URL had no ?v=, add it
    if "images/spotify_now.svg?v=" not in block2:
        block2 = block2.replace("images/spotify_now.svg", f"images/spotify_now.svg?v={h}")

    md2 = md[:m.start()] + block2 + md[m.end():]

    with open(README, "w", encoding="utf-8") as f:
        f.write(md2)

if __name__ == "__main__":
    main()
