from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import config_listicons2 as cfg


ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / cfg.README_PATH
LINKS_JSON_PATH = ROOT / cfg.LINKS_JSON_PATH

VALID_RENDER_MODES = {
    "links_listicons2_svg_gnlz",
    "links_listicons2_svg_github",
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
    if not LINKS_JSON_PATH.exists():
        raise FileNotFoundError(f"JSON file not found: {LINKS_JSON_PATH}")

    raw = LINKS_JSON_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)

    if not isinstance(data, list):
        raise ValueError("list-icons2-links.json must contain a JSON array.")

    return data


def validate_link_item(item: dict, index: int) -> None:
    if not isinstance(item, dict):
        raise ValueError(f"Item #{index} must be an object.")

    required_keys = {"href", "src", "alt"}
    missing = [key for key in required_keys if key not in item]
    if missing:
        raise ValueError(f"Item #{index} is missing keys: {', '.join(missing)}")

    if not isinstance(item["href"], str):
        raise ValueError(f'Item #{index} key "href" must be a string.')

    if not isinstance(item["src"], str):
        raise ValueError(f'Item #{index} key "src" must be a string.')

    if not isinstance(item["alt"], str):
        raise ValueError(f'Item #{index} key "alt" must be a string.')


def render_links_mode() -> str:
    items = load_links_json()
    html_parts: list[str] = []

    for index, item in enumerate(items, start=1):
        validate_link_item(item, index)

        href = item["href"].strip()
        src = item["src"].strip()
        alt = item["alt"].strip()

        if cfg.SKIP_HASH_LINKS and href == "#":
            continue

        if not src:
            continue

        width = int(item.get("width", cfg.DEFAULT_ICON_WIDTH))
        height = int(item.get("height", cfg.DEFAULT_ICON_HEIGHT))

        target_attr = ' target="_blank"' if cfg.OPEN_LINKS_IN_NEW_TAB else ""

        html_parts.append(
            f'<a href="{href}"{target_attr}>'
            f'<img src="{src}" alt="{alt}" width="{width}" height="{height}"/></a>'
        )

    return cfg.LINKS_JOIN_WITH.join(html_parts)


def render_full_image_mode() -> str:
    target_attr = ' target="_blank"' if cfg.FULL_IMAGE_OPEN_IN_NEW_TAB else ""

    return (
        f'<a href="{cfg.FULL_IMAGE_LINK}"{target_attr}>'
        f'<img src="{cfg.FULL_IMAGE_URL}" alt="{cfg.FULL_IMAGE_ALT}" />'
        f'</a>'
    )


def build_block() -> str:
    mode = normalize_render_mode(cfg.RENDER_MODE)

    if cfg.FORCE_EMPTY_IF_GNLZ_DOWN and not gnlz_is_alive():
        return ""

    if mode == "none":
        return ""

    if mode == "full_image":
        return render_full_image_mode()

    if mode in {"links_listicons2_svg_gnlz", "links_listicons2_svg_github"}:
        return render_links_mode()

    return ""


def replace_between_markers(readme_text: str, new_content: str) -> str:
    start = readme_text.find(cfg.README_START_MARKER)
    end = readme_text.find(cfg.README_END_MARKER)

    if start == -1 or end == -1 or end < start:
        raise RuntimeError("README markers for List-icons2 not found or invalid.")

    insert_at = start + len(cfg.README_START_MARKER)
    return readme_text[:insert_at] + "\n" + new_content + "\n" + readme_text[end:]


def main() -> int:
    if not README_PATH.exists():
        print(f"{cfg.README_PATH} not found.", file=sys.stderr)
        return 1

    original = README_PATH.read_text(encoding="utf-8")
    block = build_block()
    updated = replace_between_markers(original, block)

    if updated != original:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README updated for List-icons2.")
    else:
        print("No changes needed for List-icons2.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
