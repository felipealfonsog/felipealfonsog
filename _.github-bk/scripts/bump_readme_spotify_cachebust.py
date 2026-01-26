#!/usr/bin/env python3
import re
import time

README = "README.md"

def main():
    with open(README, "r", encoding="utf-8") as f:
        md = f.read()

    # Replace only the ?v=... on spotify_now.svg
    # examples:
    #   images/spotify_now.svg?v=1
    #   images/spotify_now.svg?v=1700000000
    md2 = re.sub(
        r"(spotify_now\.svg\?v=)([0-9]+)",
        r"\g<1>" + str(int(time.time())),
        md,
        count=1,
    )

    if md2 != md:
        with open(README, "w", encoding="utf-8") as f:
            f.write(md2)

if __name__ == "__main__":
    main()
