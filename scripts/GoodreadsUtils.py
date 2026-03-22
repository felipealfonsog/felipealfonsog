import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_now_human() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, data: dict[str, Any], indent: int = 2, sort_keys: bool = False) -> None:
    text = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=sort_keys) + "\n"
    path.write_text(text, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_if_changed(path: Path, content: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def sanitize_text(text: str) -> str:
    text = html.unescape(text or "")
    text = strip_html_tags(text)
    text = collapse_ws(text)
    return text


def truncate(text: str, max_len: int) -> str:
    if max_len <= 0:
        return text
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1].rstrip() + "…"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(data: Any) -> str:
    normalized = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_text(normalized)


def unique_books_by_identity(books: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for book in books:
        key = (
            (book.get("title") or "").strip().lower(),
            (book.get("author") or "").strip().lower(),
            (book.get("link") or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(book)
    return result


def duplicate_ratio(original: list[dict[str, Any]], deduped: list[dict[str, Any]]) -> float:
    if not original:
        return 0.0
    return max(0.0, (len(original) - len(deduped)) / len(original))


def validate_book(
    book: dict[str, Any],
    allow_empty_cover: bool,
    allow_empty_link: bool,
    allow_empty_author: bool,
) -> bool:
    title = (book.get("title") or "").strip()
    author = (book.get("author") or "").strip()
    link = (book.get("link") or "").strip()
    cover = (book.get("cover") or "").strip()

    if not title:
        return False
    if not allow_empty_author and not author:
        return False
    if not allow_empty_link and not link:
        return False
    if not allow_empty_cover and not cover:
        return False
    return True


def validate_snapshot(
    books: list[dict[str, Any]],
    min_valid_books: int,
    max_duplicate_ratio: float,
) -> tuple[bool, str]:
    if not books:
        return False, "snapshot_has_no_books"

    deduped = unique_books_by_identity(books)
    d_ratio = duplicate_ratio(books, deduped)

    if len(deduped) < min_valid_books:
        return False, "snapshot_below_min_valid_books"

    if d_ratio > max_duplicate_ratio:
        return False, "snapshot_duplicate_ratio_too_high"

    return True, "ok"


def replace_between_markers(
    text: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
) -> str:
    if start_marker not in text or end_marker not in text:
        raise RuntimeError(f"README markers not found: {start_marker} / {end_marker}")

    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    new_block = f"{start_marker}\n{replacement.rstrip()}\n{end_marker}"
    return pattern.sub(new_block, text, count=1)


def html_escape(text: str) -> str:
    return html.escape(text or "", quote=True)


def md_escape_inline(text: str) -> str:
    text = text or ""
    for ch in ["\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!"]:
        text = text.replace(ch, "\\" + ch)
    return text
