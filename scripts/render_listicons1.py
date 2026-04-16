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


VALID_MODES = {"none", "links", "full_image"}


def source_is_alive(url: str, timeout: int) -> bool:
    req = Request(
        url,
        headers={"User-Agent": cfg.USER_AGENT},
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status < 200 or status >= 400:
                return False
            chunk = response.read(512)
            return len(chunk) > 0
    except (HTTPError, URLError, TimeoutError, Exception):
        return False


def normalize_mode(value: str) -> str:
    value = (value or "").strip().lower()
    if value in VALID_MODES:
        return value
    return cfg.SAFE_DEFAULT_MODE


def resolve_mode() -> str:
    primary_mode = normalize_mode(cfg.PRIMARY_MODE)
    fallback_mode = normalize_mode(cfg.FALLBACK_MODE)

    if cfg.IGNORE_SOURCE_HEALTH:
        return primary_mode

    if not cfg.CHECK_SOURCE_HEALTH:
        return primary_mode

    alive = source_is_alive(cfg.SOURCE_URL, cfg.REQUEST_TIMEOUT)

    if alive:
        return primary_mode

    if cfg.USE_FALLBACK_WHEN_SOURCE_DOWN:
        return fallback_mode

    return cfg.SAFE_DEFAULT_MODE


def load_links() -> list[dict]:
    with LINKS_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("list-icons1-links.json must contain a JSON array.")

    return data


def should_skip_item(item: dict) -> bool:
    href = str(item.get("href", "")).strip()
    if cfg.SKIP_PLACEHOLDER_LINKS and (href == "" or href == "#"):
        return True
    return False


def render_links(items: list[dict]) -> str:
    html_parts: list[str] = []

    for item in items:
        if should_skip_item(item):
            continue

        href = str(item["href"]).strip()
        src = str(item["src"]).strip()
        alt = str(item.get("alt", "")).strip()

        width = int(item.get("width", cfg.DEFAULT_ICON_WIDTH))
        height = int(item.get("height", cfg.DEFAULT_ICON_HEIGHT))

        target_attr = ' target="_blank"' if cfg.OPEN_LINKS_IN_NEW_TAB else ""

        html_parts.append(
            f'<a href="{href}"{target_attr}>'
            f'<img src="{src}" alt="{alt}" width="{width}" height="{height}"/></a>'
        )

    if cfg.RENDER_COMPACT_INLINE:
        return "".join(html_parts)

    return cfg.INLINE_SEPARATOR.join(html_parts)


def render_full_image() -> str:
    return f'<img src="{cfg.FULL_IMAGE_URL}" alt="List-icons1 inline strip" />'


def build_block() -> str:
    mode = resolve_mode()

    if mode == "none":
        return ""

    if mode == "links":
        items = load_links()
        return render_links(items)

    if mode == "full_image":
        return render_full_image()

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
