from typing import Any

import GoodreadsConfig as config
from GoodreadsUtils import (
    ensure_dir,
    html_escape,
    read_json,
    read_text,
    replace_between_markers,
    sha256_json,
    truncate,
    utc_now_iso,
    write_json,
    write_text_if_changed,
)


def resolve_section_limit_from_snapshot(section: dict[str, Any], fallback_name: str) -> int:
    value = section.get("limit")
    if isinstance(value, int) and value > 0:
        return value

    if config.USE_GLOBAL_SECTION_LIMIT:
        return config.GLOBAL_SECTION_LIMIT

    if fallback_name == "currently_reading":
        return config.CURRENTLY_READING_LIMIT

    if fallback_name == "recent_read":
        return config.RECENT_READ_LIMIT

    return config.GLOBAL_SECTION_LIMIT


def build_last_update_utc(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    attempted = str(meta.get("last_attempted_sync", "")).strip()
    if attempted:
        return attempted

    successful = str(meta.get("last_successful_sync", "")).strip()
    if successful:
        return successful

    return utc_now_iso()


def build_visual_meta_line(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    parts = []

    if config.SHOW_STATUS:
        parts.append(f"status: {html_escape(str(meta.get('status', '')))}")

    if config.SHOW_FETCH_MODE:
        parts.append(f"mode: {html_escape(str(meta.get('fetch_mode', '')))}")

    if config.SHOW_LAST_SYNC:
        sync = str(meta.get("last_successful_sync", "")).strip()
        if sync:
            parts.append(f"sync: {html_escape(sync)}")

    if config.SHOW_LAST_UPDATE:
        parts.append(f"last update: {html_escape(build_last_update_utc(snapshot))}")

    if config.SHOW_SOURCE:
        parts.append(f"source: {html_escape(str(meta.get('source', '')))}")

    return " • ".join(parts)


def render_visual_title(title: str, link: str) -> str:
    safe_title = html_escape(truncate(title, config.VISUAL_CAPTION_MAX_TITLE_LENGTH))
    if config.VISUAL_CAPTION_TITLE_IS_LINK and config.SHOW_LINK and link:
        return f'<div><sub><a href="{html_escape(link)}">{safe_title}</a></sub></div>'
    return f"<div><sub>{safe_title}</sub></div>"


def render_visual_author(author: str) -> str:
    safe_author = html_escape(truncate(author, config.VISUAL_CAPTION_MAX_AUTHOR_LENGTH))
    return f'<div style="margin-top:{config.VISUAL_AUTHOR_TOP_MARGIN_PX}px;"><sub>{safe_author}</sub></div>'


def render_visual_book_card(book: dict[str, Any]) -> str:
    title = str(book.get("title", "") or "")
    author = str(book.get("author", "") or "")
    link = str(book.get("link", "") or "")
    cover = str(book.get("cover", "") or "")

    alt_parts = []
    if config.SHOW_TITLE and title:
        alt_parts.append(title)
    if config.SHOW_AUTHOR and author:
        alt_parts.append(author)
    alt = " — ".join(alt_parts) if alt_parts else "Book cover"

    border_style = ""
    if config.VISUAL_ENABLE_IMAGE_BORDER:
        border_style = f"border:1px solid {config.VISUAL_IMAGE_BORDER_COLOR};"

    if config.SHOW_COVER and cover:
        image_html = (
            f'<img src="{html_escape(cover)}" '
            f'width="{config.VISUAL_COVER_WIDTH}" '
            f'height="{config.VISUAL_COVER_HEIGHT}" '
            f'alt="{html_escape(alt)}" '
            f'style="display:block;object-fit:cover;'
            f'border-radius:{config.VISUAL_IMAGE_BORDER_RADIUS_PX}px;'
            f'margin:0 auto;{border_style}" />'
        )
    else:
        image_html = (
            f'<div style="display:flex;align-items:center;justify-content:center;'
            f'width:{config.VISUAL_COVER_WIDTH}px;'
            f'height:{config.VISUAL_COVER_HEIGHT}px;'
            f'background:{config.VISUAL_FALLBACK_BG};'
            f'color:{config.VISUAL_FALLBACK_TEXT_COLOR};'
            f'border-radius:{config.VISUAL_IMAGE_BORDER_RADIUS_PX}px;'
            f'margin:0 auto;font-size:9px;text-align:center;padding:4px;{border_style}">'
            f'{html_escape(truncate(title or "Untitled", 14))}</div>'
        )

    if config.SHOW_LINK and link:
        image_html = f'<a href="{html_escape(link)}">{image_html}</a>'

    caption_parts: list[str] = []

    if config.VISUAL_SHOW_CAPTION:
        if config.VISUAL_CAPTION_SHOW_TITLE and config.SHOW_TITLE and title:
            caption_parts.append(render_visual_title(title, link))

        if config.VISUAL_CAPTION_SHOW_AUTHOR and config.SHOW_AUTHOR and author:
            caption_parts.append(render_visual_author(author))

    caption_html = "".join(caption_parts)

    return (
        f'<span style="display:{config.VISUAL_CARD_DISPLAY};'
        f'vertical-align:{config.VISUAL_CARD_VERTICAL_ALIGN};'
        f'width:{config.VISUAL_CARD_WIDTH_PX}px;'
        f'margin-right:{config.VISUAL_CARD_MARGIN_RIGHT_PX}px;'
        f'margin-bottom:{config.VISUAL_CARD_MARGIN_BOTTOM_PX}px;'
        f'text-align:{config.VISUAL_CARD_TEXT_ALIGN};'
        f'background:transparent;">'
        f'{image_html}'
        f'<div style="margin-top:{config.VISUAL_CAPTION_TOP_MARGIN_PX}px;">{caption_html}</div>'
        f'</span>'
    )


def render_visual_section(section: dict[str, Any], section_name: str, section_title: str) -> str:
    books = section.get("books", [])
    if not section.get("enabled", False):
        return ""

    header = (
        f'<div align="{html_escape(config.VISUAL_SECTION_HEADER_ALIGN)}">'
        f'<sub><strong>{html_escape(section_title)}</strong></sub>'
        f'</div>'
    )

    if not books:
        return (
            f"{header}"
            f'<div style="height:{config.VISUAL_SECTION_SPACER_PX}px;"></div>'
            f'<div align="{html_escape(config.VISUAL_SECTION_HEADER_ALIGN)}">'
            f'<sub>{html_escape(config.VISUAL_EMPTY_MESSAGE)}</sub>'
            f"</div>"
            f'<div style="height:{config.VISUAL_SECTION_BOTTOM_SPACER_PX}px;"></div>'
        )

    cards_html = "".join(render_visual_book_card(book) for book in books)

    return (
        f"{header}"
        f'<div style="height:{config.VISUAL_SECTION_SPACER_PX}px;"></div>'
        f'<div align="{html_escape(config.VISUAL_SECTION_GRID_ALIGN)}" style="background:transparent;">'
        f"{cards_html}"
        f"</div>"
        f'<div style="height:{config.VISUAL_SECTION_BOTTOM_SPACER_PX}px;"></div>'
    )


def render_visual_block(snapshot: dict[str, Any]) -> str:
    sections = snapshot.get("sections", {})
    current_section = sections.get("currently_reading", {})
    recent_section = sections.get("recent_read", {})

    lines: list[str] = []

    if config.VISUAL_TITLE_USE_SMALL:
        lines.append(f'<sub><strong>{html_escape(config.VISUAL_BLOCK_TITLE)}</strong></sub>')
    else:
        lines.append(f"### {html_escape(config.VISUAL_BLOCK_TITLE)}")

    if config.VISUAL_SHOW_DESCRIPTION and config.VISUAL_BLOCK_DESCRIPTION.strip():
        lines.append(f'<sub>{html_escape(config.VISUAL_BLOCK_DESCRIPTION)}</sub>')

    if config.VISUAL_META_AS_SUBTEXT:
        meta_line = build_visual_meta_line(snapshot)
        if meta_line:
            lines.append(f'<sub>{meta_line}</sub>')

    current_html = ""
    recent_html = ""

    if config.SHOW_CURRENTLY_READING_SECTION:
        current_html = render_visual_section(
            current_section,
            "currently_reading",
            config.VISUAL_CURRENTLY_READING_TITLE,
        )

    if config.SHOW_RECENT_READ_SECTION:
        recent_html = render_visual_section(
            recent_section,
            "recent_read",
            config.VISUAL_RECENT_READ_TITLE,
        )

    if current_html:
        lines.append("")
        lines.append(current_html)

    if recent_html:
        lines.append("")
        lines.append(recent_html)

    if not current_html and not recent_html:
        lines.append(config.VISUAL_EMPTY_MESSAGE)

    return "\n".join(lines)


def render_cli_section(section: dict[str, Any], section_name: str, label: str) -> list[str]:
    lines: list[str] = []

    if not section.get("enabled", False):
        return lines

    books = section.get("books", [])
    shelf = str(section.get("shelf", ""))
    limit = resolve_section_limit_from_snapshot(section, section_name)

    if config.CLI_SHOW_SECTION_HEADERS:
        header_parts = [f"[{label}]"]

        if config.CLI_SHOW_SECTION_SHELF:
            header_parts.append(f"shelf={shelf}")

        if config.CLI_SHOW_SECTION_BOOK_COUNT:
            header_parts.append(f"books={len(books)}")

        if config.CLI_SHOW_SECTION_LIMIT:
            header_parts.append(f"limit={limit}")

        lines.append(" ".join(header_parts))

    if not books:
        lines.append("no data available")
        lines.append("")
        return lines

    for idx, book in enumerate(books, start=1):
        title = str(book.get("title", "") or "Untitled")
        author = str(book.get("author", "") or "")

        if config.CLI_MAX_TITLE_LENGTH > 0:
            title = truncate(title, config.CLI_MAX_TITLE_LENGTH)

        if config.CLI_MAX_AUTHOR_LENGTH > 0 and author:
            author = truncate(author, config.CLI_MAX_AUTHOR_LENGTH)

        line = f"{str(idx).zfill(config.CLI_BOOK_INDEX_PAD)}. {title}"
        if config.SHOW_AUTHOR and author:
            line += f" — {author}"

        if config.CLI_SHOW_LINKS_INLINE and config.SHOW_LINK:
            link = str(book.get("link", "") or "")
            if link:
                line += f" [{link}]"

        lines.append(line)

    lines.append("")
    return lines


def render_cli_block(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    sections = snapshot.get("sections", {})

    lines: list[str] = []
    lines.append(f"```{config.CLI_CODE_FENCE_LANGUAGE}")
    lines.append(f"# {config.CLI_BLOCK_TITLE}")

    if config.CLI_DESCRIPTION.strip():
        lines.append(f"# {config.CLI_DESCRIPTION}")

    meta_parts = []

    if config.SHOW_STATUS:
        meta_parts.append(f"status={meta.get('status', '')}")
    if config.SHOW_FETCH_MODE:
        meta_parts.append(f"mode={meta.get('fetch_mode', '')}")
    if config.SHOW_LAST_SYNC:
        meta_parts.append(f"sync={meta.get('last_successful_sync', '')}")
    if config.SHOW_LAST_UPDATE:
        meta_parts.append(f"{config.CLI_LABEL_LAST_UPDATE}={build_last_update_utc(snapshot)}")
    if config.SHOW_SOURCE:
        meta_parts.append(f"source={meta.get('source', '')}")

    if meta_parts:
        if config.CLI_COMPACT_META:
            lines.append("# " + " | ".join(meta_parts))
        else:
            for part in meta_parts:
                lines.append(f"# {part}")

    if config.CLI_DIVIDER:
        lines.append("")

    if config.SHOW_CURRENTLY_READING_SECTION:
        lines.extend(
            render_cli_section(
                sections.get("currently_reading", {}),
                "currently_reading",
                "currently_reading",
            )
        )

    if config.SHOW_RECENT_READ_SECTION:
        lines.extend(
            render_cli_section(
                sections.get("recent_read", {}),
                "recent_read",
                "recent_read",
            )
        )

    if len(lines) <= 4:
        lines.append(config.CLI_EMPTY_MESSAGE)

    lines.append("```")
    return "\n".join(lines)


def write_render_metadata(
    snapshot: dict[str, Any],
    readme_changed: bool,
    rendered_visual: bool,
    rendered_cli: bool,
) -> None:
    payload = {
        "meta": {
            "rendered_at": utc_now_iso(),
            "render_mode": config.RENDER_MODE,
            "rendered_visual": rendered_visual,
            "rendered_cli": rendered_cli,
            "readme_changed": readme_changed,
            "snapshot_hash": sha256_json(snapshot),
        }
    }

    write_json(
        config.LAST_RENDER_PATH,
        payload,
        indent=config.JSON_INDENT,
        sort_keys=config.JSON_SORT_KEYS,
    )


def main() -> int:
    ensure_dir(config.DATA_DIR)

    snapshot = read_json(config.CACHE_PATH)
    if snapshot is None:
        snapshot = {
            "meta": {
                "source": config.SOURCE_LABEL,
                "status": "no_snapshot",
                "fetch_mode": "none",
                "last_attempted_sync": "",
                "last_successful_sync": "",
                "error_message": "No cache file present.",
            },
            "sections": {
                "currently_reading": {
                    "enabled": config.SHOW_CURRENTLY_READING_SECTION,
                    "title": config.VISUAL_CURRENTLY_READING_TITLE,
                    "shelf": config.CURRENTLY_READING_SHELF,
                    "limit": config.GLOBAL_SECTION_LIMIT if config.USE_GLOBAL_SECTION_LIMIT else config.CURRENTLY_READING_LIMIT,
                    "item_count": 0,
                    "books": [],
                },
                "recent_read": {
                    "enabled": config.SHOW_RECENT_READ_SECTION,
                    "title": config.VISUAL_RECENT_READ_TITLE,
                    "shelf": config.RECENT_READ_SHELF,
                    "limit": config.GLOBAL_SECTION_LIMIT if config.USE_GLOBAL_SECTION_LIMIT else config.RECENT_READ_LIMIT,
                    "item_count": 0,
                    "books": [],
                },
            },
        }

    readme = read_text(config.README_PATH)

    render_visual = config.RENDER_MODE in ("visual", "both")
    render_cli = config.RENDER_MODE in ("cli", "both")

    if render_visual:
        visual_block = render_visual_block(snapshot)
        readme = replace_between_markers(
            readme,
            config.README_MARKER_VISUAL_START,
            config.README_MARKER_VISUAL_END,
            visual_block,
        )
    elif not config.PRESERVE_UNUSED_BLOCKS:
        readme = replace_between_markers(
            readme,
            config.README_MARKER_VISUAL_START,
            config.README_MARKER_VISUAL_END,
            "",
        )

    if render_cli:
        cli_block = render_cli_block(snapshot)
        readme = replace_between_markers(
            readme,
            config.README_MARKER_CLI_START,
            config.README_MARKER_CLI_END,
            cli_block,
        )
    elif not config.PRESERVE_UNUSED_BLOCKS:
        readme = replace_between_markers(
            readme,
            config.README_MARKER_CLI_START,
            config.README_MARKER_CLI_END,
            "",
        )

    changed = write_text_if_changed(config.README_PATH, readme)
    write_render_metadata(snapshot, changed, render_visual, render_cli)

    print(f"Goodreads render completed. README changed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
