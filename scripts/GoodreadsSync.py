import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

import GoodreadsConfig as config
from GoodreadsUtils import (
    ensure_dir,
    read_json,
    sanitize_text,
    utc_now_iso,
    validate_book,
    validate_snapshot,
    write_json,
)


def build_rss_url() -> str:
    return config.GOODREADS_RSS_URL_TEMPLATE.format(
        user_id=config.GOODREADS_USER_ID,
        shelf=config.GOODREADS_SHELF,
    )


def http_get(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": config.USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=config.REQUEST_TIMEOUT) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def extract_cover_from_description(description: str) -> str:
    if not description:
        return ""

    patterns = [
        r'<img[^>]+src="([^"]+)"',
        r"<img[^>]+src='([^']+)'",
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def extract_author_from_description(description: str) -> str:
    if not description:
        return ""

    candidates = [
        r"by\s+([^<\n\r]+)",
        r"author:\s*([^<\n\r]+)",
    ]

    for pattern in candidates:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            author = sanitize_text(match.group(1))
            if author:
                return author

    return ""


def parse_rss_items(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    books: list[dict[str, Any]] = []

    for item in channel.findall("item"):
        title = sanitize_text(item.findtext("title", default=""))
        link = sanitize_text(item.findtext("link", default=""))
        description_raw = item.findtext("description", default="") or ""

        author = ""
        for tag in ("author_name", "creator", "{http://purl.org/dc/elements/1.1/}creator", "author"):
            value = item.findtext(tag, default="")
            value = sanitize_text(value)
            if value:
                author = value
                break

        if not author:
            author = extract_author_from_description(description_raw)

        cover = extract_cover_from_description(description_raw)

        guid = sanitize_text(item.findtext("guid", default=""))
        pub_date = sanitize_text(item.findtext("pubDate", default=""))

        book = {
            "title": title,
            "author": author,
            "link": link,
            "cover": cover,
            "guid": guid,
            "pub_date": pub_date,
        }
        books.append(book)

    return books


def normalize_books(books: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for book in books:
        cleaned = {
            "title": sanitize_text(book.get("title", "")),
            "author": sanitize_text(book.get("author", "")),
            "link": sanitize_text(book.get("link", "")),
            "cover": sanitize_text(book.get("cover", "")),
            "guid": sanitize_text(book.get("guid", "")),
            "pub_date": sanitize_text(book.get("pub_date", "")),
        }

        if validate_book(
            cleaned,
            allow_empty_cover=config.ALLOW_EMPTY_COVER,
            allow_empty_link=config.ALLOW_EMPTY_LINK,
            allow_empty_author=config.ALLOW_EMPTY_AUTHOR,
        ):
            normalized.append(cleaned)

    return normalized


def build_snapshot(
    books: list[dict[str, Any]],
    status: str,
    fetch_mode: str,
    source_url: str,
    error_message: str = "",
) -> dict[str, Any]:
    return {
        "meta": {
            "source": config.SOURCE_LABEL,
            "source_url": source_url,
            "shelf": config.GOODREADS_SHELF,
            "status": status,
            "fetch_mode": fetch_mode,
            "last_attempted_sync": utc_now_iso(),
            "last_successful_sync": utc_now_iso() if status == "ok" else "",
            "item_count": len(books),
            "books_limit": config.BOOKS_LIMIT,
            "error_message": error_message,
        },
        "books": books,
    }


def merge_with_previous_success(
    previous_cache: dict[str, Any] | None,
    new_snapshot: dict[str, Any],
) -> dict[str, Any]:
    previous_meta = (previous_cache or {}).get("meta", {})
    if previous_meta.get("last_successful_sync") and not new_snapshot["meta"].get("last_successful_sync"):
        new_snapshot["meta"]["last_successful_sync"] = previous_meta.get("last_successful_sync", "")
    return new_snapshot


def main() -> int:
    ensure_dir(config.DATA_DIR)

    if config.GOODREADS_USER_ID == "YOUR_GOODREADS_USER_ID":
        print("ERROR: Goodreads user id is not configured.")
        return 1

    source_url = build_rss_url()
    previous_cache = read_json(config.CACHE_PATH)

    try:
        xml_text = http_get(source_url)
        parsed_books = parse_rss_items(xml_text)
        normalized_books = normalize_books(parsed_books)
        normalized_books = normalized_books[: config.BOOKS_LIMIT]

        is_valid, validation_reason = validate_snapshot(
            normalized_books,
            min_valid_books=config.MIN_VALID_BOOKS,
            max_duplicate_ratio=config.MAX_DUPLICATE_RATIO,
        )

        if not is_valid and config.STRICT_VALIDATION:
            if config.USE_CACHE_FALLBACK and previous_cache and config.PRESERVE_LAST_GOOD_SNAPSHOT:
                fallback = previous_cache
                fallback_meta = fallback.setdefault("meta", {})
                fallback_meta["status"] = "cached_fallback"
                fallback_meta["fetch_mode"] = "cache"
                fallback_meta["last_attempted_sync"] = utc_now_iso()
                fallback_meta["error_message"] = validation_reason
                write_json(
                    config.CACHE_PATH,
                    fallback,
                    indent=config.JSON_INDENT,
                    sort_keys=config.JSON_SORT_KEYS,
                )
                print(f"Using cache fallback due to validation failure: {validation_reason}")
                return 0

            failed_snapshot = build_snapshot(
                books=[],
                status="invalid_snapshot",
                fetch_mode="network",
                source_url=source_url,
                error_message=validation_reason,
            )
            failed_snapshot = merge_with_previous_success(previous_cache, failed_snapshot)
            write_json(
                config.CACHE_PATH,
                failed_snapshot,
                indent=config.JSON_INDENT,
                sort_keys=config.JSON_SORT_KEYS,
            )
            print(f"Stored invalid snapshot metadata: {validation_reason}")
            return 0

        snapshot = build_snapshot(
            books=normalized_books,
            status="ok",
            fetch_mode="network",
            source_url=source_url,
        )
        snapshot = merge_with_previous_success(previous_cache, snapshot)
        write_json(
            config.CACHE_PATH,
            snapshot,
            indent=config.JSON_INDENT,
            sort_keys=config.JSON_SORT_KEYS,
        )
        print(f"Goodreads sync OK. Books stored: {len(normalized_books)}")
        return 0

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ET.ParseError, ValueError) as exc:
        if config.USE_CACHE_FALLBACK and previous_cache and config.PRESERVE_LAST_GOOD_SNAPSHOT:
            fallback = previous_cache
            fallback_meta = fallback.setdefault("meta", {})
            fallback_meta["status"] = "source_unavailable_using_cache"
            fallback_meta["fetch_mode"] = "cache"
            fallback_meta["last_attempted_sync"] = utc_now_iso()
            fallback_meta["error_message"] = str(exc)
            write_json(
                config.CACHE_PATH,
                fallback,
                indent=config.JSON_INDENT,
                sort_keys=config.JSON_SORT_KEYS,
            )
            print(f"Goodreads fetch failed. Using cache: {exc}")
            return 0

        failed_snapshot = build_snapshot(
            books=[],
            status="source_unavailable_no_cache",
            fetch_mode="none",
            source_url=source_url,
            error_message=str(exc),
        )
        failed_snapshot = merge_with_previous_success(previous_cache, failed_snapshot)
        write_json(
            config.CACHE_PATH,
            failed_snapshot,
            indent=config.JSON_INDENT,
            sort_keys=config.JSON_SORT_KEYS,
        )
        print(f"Goodreads fetch failed and no cache available: {exc}")
        return 0

    except Exception as exc:
        print(f"Unexpected error in GoodreadsSync.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
