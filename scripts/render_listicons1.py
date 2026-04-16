from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import config_listicons1 as cfg


ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / cfg.README_PATH
LINKS_JSON_PATH = ROOT / cfg.LINKS_JSON_PATH

VALID_RENDER_MODES = {
    "links_listicons1_svg_gnlz",
    "links_listicons1_svg_github",
    "full_image",
    "none",
}


def gnlz_is_alive() -> bool:
    if not cfg.HEALTHCHECK_ENABLED:
        return True

    request = Request(
        cfg.HEALTHCHECK_URL,
        headers={"User-Agent": cfg.HEALTHCHECK_USER_AGENT},
    )

    try:
        with urlopen(request, timeout=cfg.HEALTHCHECK_TIMEOUT) as response:
            status = getattr(response, "status", 200)
            if status < 200 or status >= 400:
                return False
            chunk = response.read(512)
            return len(chunk) > 0
    except (HTTPError, URLError, TimeoutError, Exception):
        return False


def normalize_render_mode(value: str) -> str:
    value = (value or "").strip().lower()
    if value in VALID_RENDER_MODES:
        return value
    return "none"


def load_links_json() -> list[dict]:
    with LINKS_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("list-icons1-links.json must contain a JSON array.")

    return data


def render_links_mode() -> str:
    items = load_links_json()
    html_parts: list[str] = []

    for item in items:
        href = str(item.get("href", "")).strip()

        if cfg.SKIP_HASH_LINKS and href == "#":
            continue

        src = str(item.get("src", "")).strip()
        if not src:
            continue

        alt = str(item.get("alt", "")).strip()
        width = int(item.get("width", cfg.DEFAULT_ICON_WIDTH))
        height = int(item.get("height", cfg.DEFAULT_ICON_HEIGHT))

        target_attr = ' target="_blank"' if cfg.OPEN_LINKS_IN_NEW_TAB else ""

        html_parts.append(
            f'<a href="{href}"{target_attr}>'
            f'<img src="{src}" alt="{alt}" width="{width}" height="{height}"/></a>'
        )

    return cfg.LINKS_JOIN_WITH.join(html_parts)


def render_full_image_mode() -> str:
    return f'<img src="{cfg.FULL_IMAGE_URL}" alt="List-icons1 inline strip" />'


def build_block() -> str:
    mode = normalize_render_mode(cfg.RENDER_MODE)

    if cfg.FORCE_EMPTY_IF_GNLZ_DOWN and not gnlz_is_alive():
        return ""

    if mode == "none":
        return ""

    if mode == "full_image":
        return render_full_image_mode()

    if mode in {"links_listicons1_svg_gnlz", "links_listicons1_svg_github"}:
        return render_links_mode()

    return ""


def replace_between_markers(readme_text: str, new_content: str) -> str:
    start = readme_text.find(cfg.README_START_MARKER)
    end = readme_text.find(cfg.README_END_MARKER)

    if start == -1 or end == -1 or end < start:
        raise RuntimeError("README markers for List-icons1 not found or invalid.")

    insert_at = start + len(cfg.README_START_MARKER)
    return readme_text[:insert_at] + "\n" + new_content + "\n" + readme_text[end:]


def main() -> int:
    if not README_PATH.exists():
        print(f"{cfg.README_PATH} not found.", file=sys.stderr)
        return 1

    if not LINKS_JSON_PATH.exists():
        print(f"{cfg.LINKS_JSON_PATH} not found.", file=sys.stderr)
        return 1

    original = README_PATH.read_text(encoding="utf-8")
    block = build_block()
    updated = replace_between_markers(original, block)

    if updated != original:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README updated for List-icons1.")
    else:
        print("No changes needed for List-icons1.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
