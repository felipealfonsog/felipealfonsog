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
    strip_html_tags,
    utc_now_iso,
    validate_book,
    write_json,
)


def resolve_section_limit(section_name: str) -> int:
    if config.USE_GLOBAL_SECTION_LIMIT:
        return config.GLOBAL_SECTION_LIMIT

    if section_name == "currently_reading":
        return config.CURRENTLY_READING_LIMIT

    if section_name == "recent_read":
        return config.RECENT_READ_LIMIT

    return config.GLOBAL_SECTION_LIMIT


def build_rss_url(shelf: str) -> str:
    return config.GOODREADS_RSS_URL_TEMPLATE.format(
        user_id=config.GOODREADS_USER_ID,
        shelf=shelf,
    )


def http_get(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": config.USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=config.REQUEST_TIMEOUT) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


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

    patterns = [
        r"by\s+([^<\n\r]+)",
        r"author:\s*([^<\n\r]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            author = sanitize_text(match.group(1))
            if author:
                return author

    return ""


def extract_summary_from_description(description: str) -> str:
    if not description:
        return ""

    text = re.sub(r"<img[^>]*>", " ", description, flags=re.IGNORECASE)
    text = re.sub(
        r"</?(br|p|div|span|a|b|strong|em|i)[^>]*>",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = strip_html_tags(text)
    text = sanitize_text(text)

    noise_patterns = [
        r"^rated.*?$",
        r"^is currently reading.*?$",
        r"^added.*?$",
        r"^reviewed.*?$",
        r"^by\s+[^.]+",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    text = sanitize_text(text)

    if len(text) < 20:
        return ""

    return text


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
        for tag in (
            "author_name",
            "creator",
            "{http://purl.org/dc/elements/1.1/}creator",
            "author",
        ):
            value = sanitize_text(item.findtext(tag, default=""))
            if value:
                author = value
                break

        if not author:
            author = extract_author_from_description(description_raw)

        cover = extract_cover_from_description(description_raw)
        summary = extract_summary_from_description(description_raw)
        guid = sanitize_text(item.findtext("guid", default=""))
        pub_date = sanitize_text(item.findtext("pubDate", default=""))

        books.append(
            {
                "title": title,
                "author": author,
                "link": link,
                "cover": cover,
                "summary": summary,
                "guid": guid,
                "pub_date": pub_date,
            }
        )

    return books


def normalize_books(books: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for book in books:
        cleaned = {
            "title": sanitize_text(book.get("title", "")),
            "author": sanitize_text(book.get("author", "")),
            "link": sanitize_text(book.get("link", "")),
            "cover": sanitize_text(book.get("cover", "")),
            "summary": sanitize_text(book.get("summary", "")),
            "guid": sanitize_text(book.get("guid", "")),
            "pub_date": sanitize_text(book.get("pub_date", "")),
        }

        if not validate_book(
            cleaned,
            allow_empty_cover=config.ALLOW_EMPTY_COVER,
            allow_empty_link=config.ALLOW_EMPTY_LINK,
            allow_empty_author=config.ALLOW_EMPTY_AUTHOR,
        ):
            continue

        key = (
            cleaned["title"].lower(),
            cleaned["author"].lower(),
            cleaned["link"].lower(),
        )
        if key in seen:
            continue
        seen.add(key)

        normalized.append(cleaned)

        if len(normalized) >= limit:
            break

    return normalized


def fetch_section(section_name: str, shelf: str) -> dict[str, Any]:
    limit = resolve_section_limit(section_name)
    url = build_rss_url(shelf)
    xml_text = http_get(url)
    parsed_items = parse_rss_items(xml_text)
    books = normalize_books(parsed_items, limit)

    return {
        "shelf": shelf,
        "source_url": url,
        "limit": limit,
        "item_count": len(books),
        "books": books,
    }


def build_empty_sections_snapshot() -> dict[str, Any]:
    return {
        "currently_reading": {
            "enabled": config.SHOW_CURRENTLY_READING_SECTION,
            "title": config.VISUAL_CURRENTLY_READING_TITLE,
            "shelf": config.CURRENTLY_READING_SHELF,
            "source_url": "",
            "limit": resolve_section_limit("currently_reading"),
            "item_count": 0,
            "books": [],
        },
        "recent_read": {
            "enabled": config.SHOW_RECENT_READ_SECTION,
            "title": config.VISUAL_RECENT_READ_TITLE,
            "shelf": config.RECENT_READ_SHELF,
            "source_url": "",
            "limit": resolve_section_limit("recent_read"),
            "item_count": 0,
            "books": [],
        },
    }


def build_failure_snapshot(previous_cache: dict[str, Any] | None, error_message: str) -> dict[str, Any]:
    if previous_cache and config.USE_CACHE_FALLBACK and config.PRESERVE_LAST_GOOD_SNAPSHOT:
        cache = previous_cache
        meta = cache.setdefault("meta", {})
        meta["status"] = "source_unavailable_using_cache"
        meta["fetch_mode"] = "cache"
        meta["last_attempted_sync"] = utc_now_iso()
        meta["error_message"] = error_message
        return cache

    return {
        "meta": {
            "source": config.SOURCE_LABEL,
            "status": "source_unavailable_no_cache",
            "fetch_mode": "none",
            "last_attempted_sync": utc_now_iso(),
            "last_successful_sync": "",
            "error_message": error_message,
        },
        "sections": build_empty_sections_snapshot(),
    }


def main() -> int:
    ensure_dir(config.DATA_DIR)

    if not str(config.GOODREADS_USER_ID).strip():
        print("ERROR: Goodreads user id is not configured.", file=sys.stderr)
        return 1

    previous_cache = read_json(config.CACHE_PATH)

    try:
        sections: dict[str, Any] = {}

        if config.SHOW_CURRENTLY_READING_SECTION:
            current = fetch_section(
                section_name="currently_reading",
                shelf=config.CURRENTLY_READING_SHELF,
            )
            sections["currently_reading"] = {
                "enabled": True,
                "title": config.VISUAL_CURRENTLY_READING_TITLE,
                **current,
            }
        else:
            sections["currently_reading"] = {
                "enabled": False,
                "title": config.VISUAL_CURRENTLY_READING_TITLE,
                "shelf": config.CURRENTLY_READING_SHELF,
                "source_url": "",
                "limit": resolve_section_limit("currently_reading"),
                "item_count": 0,
                "books": [],
            }

        if config.SHOW_RECENT_READ_SECTION:
            recent = fetch_section(
                section_name="recent_read",
                shelf=config.RECENT_READ_SHELF,
            )
            sections["recent_read"] = {
                "enabled": True,
                "title": config.VISUAL_RECENT_READ_TITLE,
                **recent,
            }
        else:
            sections["recent_read"] = {
                "enabled": False,
                "title": config.VISUAL_RECENT_READ_TITLE,
                "shelf": config.RECENT_READ_SHELF,
                "source_url": "",
                "limit": resolve_section_limit("recent_read"),
                "item_count": 0,
                "books": [],
            }

        valid_count = 0
        required_enabled_sections = 0

        for section in sections.values():
            if section["enabled"]:
                required_enabled_sections += 1
                if section["item_count"] >= config.MIN_VALID_BOOKS_PER_SECTION:
                    valid_count += 1

        if config.STRICT_VALIDATION and required_enabled_sections > 0 and valid_count == 0:
            snapshot = build_failure_snapshot(
                previous_cache,
                "all_enabled_sections_invalid_or_empty",
            )
            write_json(
                config.CACHE_PATH,
                snapshot,
                indent=config.JSON_INDENT,
                sort_keys=config.JSON_SORT_KEYS,
            )
            print("Goodreads sync fallback: all enabled sections invalid or empty.")
            return 0

        previous_success = ""
        if previous_cache:
            previous_success = str(
                previous_cache.get("meta", {}).get("last_successful_sync", "")
            ).strip()

        now_utc = utc_now_iso()

        snapshot = {
            "meta": {
                "source": config.SOURCE_LABEL,
                "status": "ok",
                "fetch_mode": "network",
                "last_attempted_sync": now_utc,
                "last_successful_sync": now_utc or previous_success,
                "error_message": "",
            },
            "sections": sections,
        }

        write_json(
            config.CACHE_PATH,
            snapshot,
            indent=config.JSON_INDENT,
            sort_keys=config.JSON_SORT_KEYS,
        )
        print("Goodreads sync OK.")
        return 0

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        ET.ParseError,
        ValueError,
    ) as exc:
        snapshot = build_failure_snapshot(previous_cache, str(exc))
        write_json(
            config.CACHE_PATH,
            snapshot,
            indent=config.JSON_INDENT,
            sort_keys=config.JSON_SORT_KEYS,
        )
        print(f"Goodreads sync fallback due to fetch/parse error: {exc}")
        return 0

    except Exception as exc:
        print(f"Unexpected error in GoodreadsSync.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())