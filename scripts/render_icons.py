from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
ICONS_JSON = ROOT / "data" / "icons_links.json"

SOURCE_URL = os.getenv("SOURCE_URL", "https://gnlz.cl/svg1.html")
DISPLAY_MODE = os.getenv("DISPLAY_MODE", "none").strip().lower()
HIDE_WHEN_SOURCE_DOWN = os.getenv("HIDE_WHEN_SOURCE_DOWN", "true").strip().lower() == "true"
FULL_IMAGE_URL = os.getenv(
    "FULL_IMAGE_URL",
    "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/refs/heads/master/images/icons1inline-full.png",
)

START_MARKER = "<!-- ICONS:START -->"
END_MARKER = "<!-- ICONS:END -->"


def source_is_alive(url: str, timeout: int = 12) -> bool:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; GitHubActionsIconCheck/1.0)"
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            if status < 200 or status >= 400:
                return False
            content = resp.read(512)
            return len(content) > 0
    except (HTTPError, URLError, TimeoutError, Exception):
        return False


def load_icons() -> list[dict]:
    with ICONS_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_links(icons: list[dict]) -> str:
    parts: list[str] = []
    for item in icons:
        href = item["href"]
        src = item["src"]
        alt = item["alt"]
        width = item.get("width", 40)
        height = item.get("height", 40)
        parts.append(
            f'<a href="{href}" target="_blank">'
            f'<img src="{src}" alt="{alt}" width="{width}" height="{height}"/></a>'
        )
    return "".join(parts)


def render_full_image() -> str:
    return (
        f'<img src="{FULL_IMAGE_URL}" alt="Inline icon strip" />'
    )


def build_block() -> str:
    alive = source_is_alive(SOURCE_URL)

    if HIDE_WHEN_SOURCE_DOWN and not alive:
        return ""

    if DISPLAY_MODE == "none":
        return ""

    if DISPLAY_MODE == "links":
        icons = load_icons()
        return render_links(icons)

    if DISPLAY_MODE == "full_image":
        return render_full_image()

    return ""


def replace_between_markers(text: str, new_content: str) -> str:
    start = text.find(START_MARKER)
    end = text.find(END_MARKER)

    if start == -1 or end == -1 or end < start:
        raise RuntimeError("README markers not found or invalid.")

    start_end = start + len(START_MARKER)
    return text[:start_end] + "\n" + new_content + "\n" + text[end:]


def main() -> int:
    if not README.exists():
        print("README.md not found.", file=sys.stderr)
        return 1

    original = README.read_text(encoding="utf-8")
    rendered = build_block()
    updated = replace_between_markers(original, rendered)

    if updated != original:
        README.write_text(updated, encoding="utf-8")
        print("README updated.")
    else:
        print("No changes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
ICONS_JSON = ROOT / "data" / "icons_links
