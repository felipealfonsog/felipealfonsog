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


# ============================================================
# HELPERS
# ============================================================

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


def build_visual_footer_meta_line(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    parts: list[str] = []

    if config.SHOW_LAST_SYNC:
        sync = str(meta.get("last_successful_sync", "")).strip()
        if sync:
            sync_label = getattr(config, "VISUAL_FOOTER_SYNC_LABEL", "SYNC")
            parts.append(f"{sync_label}: {html_escape(sync)}")

    if config.SHOW_LAST_UPDATE:
        parts.append(f"LAST UPDATE: {html_escape(build_last_update_utc(snapshot))}")

    if config.SHOW_SOURCE:
        parts.append(f"SOURCE: {html_escape(str(meta.get('source', '')))}")

    return " • ".join(parts)


def build_cli_meta_line(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    parts: list[str] = []

    if config.SHOW_STATUS:
        parts.append(f"status={meta.get('status', '')}")

    if config.SHOW_FETCH_MODE:
        parts.append(f"mode={meta.get('fetch_mode', '')}")

    if config.SHOW_LAST_SYNC:
        parts.append(f"sync={meta.get('last_successful_sync', '')}")

    if config.SHOW_LAST_UPDATE:
        parts.append(f"{config.CLI_LABEL_LAST_UPDATE}={build_last_update_utc(snapshot)}")

    if config.SHOW_SOURCE:
        parts.append(f"source={meta.get('source', '')}")

    return " | ".join(parts)


# ============================================================
# OPTION 1: COVERS ONLY
# ============================================================

def render_option1_cover(book: dict[str, Any]) -> str:
    title = str(book.get("title", "") or "")
    author = str(book.get("author", "") or "")
    link = str(book.get("link", "") or "")
    cover = str(book.get("cover", "") or "")

    alt_parts = []
    if title:
        alt_parts.append(title)
    if author:
        alt_parts.append(author)
    alt = " — ".join(alt_parts) if alt_parts else "Book cover"

    border_style = ""
    if config.OPTION1_ENABLE_IMAGE_BORDER:
        border_style = f"border:1px solid {config.OPTION1_IMAGE_BORDER_COLOR};"

    style = (
        f"display:inline-block;"
        f"width:{config.OPTION1_COVER_WIDTH}px;"
        f"height:{config.OPTION1_COVER_HEIGHT}px;"
        f"object-fit:{config.OPTION1_COVER_OBJECT_FIT};"
        f"border-radius:{config.OPTION1_IMAGE_BORDER_RADIUS_PX}px;"
        f"vertical-align:top;"
        f"margin-right:4px;"
        f"{border_style}"
    )

    if config.OPTION1_SHOW_COVERS and cover:
        image_html = (
            f'<img src="{html_escape(cover)}" '
            f'width="{config.OPTION1_COVER_WIDTH}" '
            f'height="{config.OPTION1_COVER_HEIGHT}" '
            f'alt="{html_escape(alt)}" '
            f'style="{style}" />'
            f'<br/>'
        )
    else:
        image_html = (
            f'<div style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:{config.OPTION1_COVER_WIDTH}px;'
            f'height:{config.OPTION1_COVER_HEIGHT}px;'
            f'background:{config.OPTION1_FALLBACK_BG};'
            f'color:{config.OPTION1_FALLBACK_TEXT_COLOR};'
            f'border-radius:{config.OPTION1_IMAGE_BORDER_RADIUS_PX}px;'
            f'font-size:9px;text-align:center;padding:4px;'
            f'vertical-align:top;margin-right:4px;{border_style}">'
            f'No cover'
            f'</div>'
        )

    if link:
        return f'<a href="{html_escape(link)}">{image_html}</a>'

    return image_html


def render_option1_section(section: dict[str, Any], section_name: str, section_title: str) -> str:
    books = section.get("books", [])

    if not section.get("enabled", False):
        return ""

    # Salto simple, no gigante
    header = (
        f'<div align="{html_escape(config.VISUAL_SECTION_HEADER_ALIGN)}">'
        f'<sub><strong>{html_escape(section_title)}</strong></sub>'
        f'</div>'
    )

    if not books:
        return header + f'<sub>{html_escape(config.VISUAL_EMPTY_MESSAGE)}</sub><br/>'

    covers_html = "".join(render_option1_cover(book) for book in books)

    return (
        header
        + covers_html
    )


# ============================================================
# OPTION 2: CARD TABLE (OLD STYLE, OFF BY DEFAULT)
# ============================================================

def render_option2_cover(book: dict[str, Any]) -> str:
    title = str(book.get("title", "") or "")
    author = str(book.get("author", "") or "")
    link = str(book.get("link", "") or "")
    cover = str(book.get("cover", "") or "")

    alt_parts = []
    if title:
        alt_parts.append(title)
    if author:
        alt_parts.append(author)
    alt = " — ".join(alt_parts) if alt_parts else "Book cover"

    border_style = ""
    if config.OPTION2_ENABLE_IMAGE_BORDER:
        border_style = f"border:1px solid {config.OPTION2_IMAGE_BORDER_COLOR};"

    style = (
        f"display:inline-block;"
        f"width:{config.OPTION2_COVER_WIDTH}px;"
        f"height:{config.OPTION2_COVER_HEIGHT}px;"
        f"object-fit:{config.OPTION2_COVER_OBJECT_FIT};"
        f"border-radius:{config.OPTION2_IMAGE_BORDER_RADIUS_PX}px;"
        f"{border_style}"
    )

    if config.OPTION2_SHOW_COVER and cover:
        image_html = (
            f'<img src="{html_escape(cover)}" '
            f'width="{config.OPTION2_COVER_WIDTH}" '
            f'height="{config.OPTION2_COVER_HEIGHT}" '
            f'alt="{html_escape(alt)}" '
            f'style="{style}" />'
        )
    else:
        image_html = (
            f'<div style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:{config.OPTION2_COVER_WIDTH}px;'
            f'height:{config.OPTION2_COVER_HEIGHT}px;'
            f'background:{config.OPTION2_FALLBACK_BG};'
            f'color:{config.OPTION2_FALLBACK_TEXT_COLOR};'
            f'border-radius:{config.OPTION2_IMAGE_BORDER_RADIUS_PX}px;'
            f'font-size:9px;text-align:center;padding:4px;{border_style}">'
            f'No cover'
            f'</div>'
        )

    if config.OPTION2_SHOW_LINK and link:
        return f'<a href="{html_escape(link)}">{image_html}</a>'

    return image_html


def render_option2_cell(book: dict[str, Any]) -> str:
    cover_html = render_option2_cover(book)
    title = truncate(str(book.get("title", "") or ""), config.OPTION2_TITLE_MAX_LENGTH)
    author = truncate(str(book.get("author", "") or ""), config.OPTION2_AUTHOR_MAX_LENGTH)

    return (
        f'<td align="center" valign="top" '
        f'style="border:none !important;outline:none !important;box-shadow:none !important;'
        f'padding:{config.OPTION2_TABLE_CELL_PADDING_PX}px;'
        f'width:{config.OPTION2_TABLE_CELL_WIDTH_PX}px;'
        f'background:transparent;">'
        f'{cover_html}'
        f'<div style="margin-top:{config.OPTION2_CAPTION_TOP_MARGIN_PX}px;"><sub>{html_escape(title)}</sub></div>'
        f'<div style="margin-top:{config.OPTION2_AUTHOR_TOP_MARGIN_PX}px;"><sub>{html_escape(author)}</sub></div>'
        f'</td>'
    )


def render_option2_section(section: dict[str, Any], section_name: str, section_title: str) -> str:
    books = section.get("books", [])

    if not section.get("enabled", False):
        return ""

    header = (
        f'<div align="{html_escape(config.VISUAL_SECTION_HEADER_ALIGN)}">'
        f'<sub><strong>{html_escape(section_title)}</strong></sub>'
        f'</div>'
        f'<br/>'
    )

    if not books:
        return header + f'<sub>{html_escape(config.VISUAL_EMPTY_MESSAGE)}</sub><br/>'

    rows: list[str] = []
    items_per_row = max(1, config.OPTION2_ITEMS_PER_ROW)

    for start in range(0, len(books), items_per_row):
        chunk = books[start:start + items_per_row]
        row_cells = "".join(render_option2_cell(book) for book in chunk)
        rows.append(f"<tr>{row_cells}</tr>")

    table_style = (
        "border-collapse:collapse;"
        "border:none !important;"
        "outline:none !important;"
        "box-shadow:none !important;"
        "background:transparent;"
        "margin:0;"
    )

    if config.OPTION2_FORCE_BORDERLESS_TABLE:
        table_style += "border-spacing:0;"

    table_html = (
        f'<table border="0" cellspacing="0" cellpadding="0" style="{table_style}">'
        f'{"".join(rows)}'
        f'</table>'
    )

    return header + table_html + '<br/>'


# ============================================================
# VISUAL FOOTER
# ============================================================

def render_visual_footer_meta(snapshot: dict[str, Any]) -> str:
    if not config.SHOW_VISUAL_FOOTER_META:
        return ""

    meta_line = build_visual_footer_meta_line(snapshot)
    if not meta_line:
        return ""

    if config.VISUAL_FOOTER_META_USE_SUB:
        meta_line = f"<sub>{meta_line}</sub>"

    # Salto simple antes y después del bloque meta
    return (
        '<br/>'
        + meta_line
        + '<br/><br/>'
    )


# ============================================================
# VISUAL BLOCK
# ============================================================

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

    lines.append('<br/>')

    current_html = ""
    recent_html = ""

    if config.SHOW_CURRENTLY_READING_SECTION:
        if config.OPTION2_CARD_TABLE_ENABLED:
            current_html = render_option2_section(
                current_section,
                "currently_reading",
                config.VISUAL_CURRENTLY_READING_TITLE,
            )
        elif config.OPTION1_COVERS_ONLY_ENABLED:
            current_html = render_option1_section(
                current_section,
                "currently_reading",
                config.VISUAL_CURRENTLY_READING_TITLE,
            )

    if config.SHOW_RECENT_READ_SECTION:
        if config.OPTION2_CARD_TABLE_ENABLED:
            recent_html = render_option2_section(
                recent_section,
                "recent_read",
                config.VISUAL_RECENT_READ_TITLE,
            )
        elif config.OPTION1_COVERS_ONLY_ENABLED:
            recent_html = render_option1_section(
                recent_section,
                "recent_read",
                config.VISUAL_RECENT_READ_TITLE,
            )

    if current_html:
        lines.append(current_html)

    if recent_html:
        lines.append(recent_html)

    if not current_html and not recent_html:
        lines.append(config.VISUAL_EMPTY_MESSAGE)

    footer_meta = render_visual_footer_meta(snapshot)
    if footer_meta:
        lines.append(footer_meta)

    return "\n".join(lines)


# ============================================================
# CLI BLOCK (OPTION 3)
# ============================================================

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
        if author:
            line += f" — {author}"

        if config.CLI_SHOW_LINKS_INLINE:
            link = str(book.get("link", "") or "")
            if link:
                line += f" [{link}]"

        lines.append(line)

    lines.append("")
    return lines


def render_cli_block(snapshot: dict[str, Any]) -> str:
    sections = snapshot.get("sections", {})

    lines: list[str] = []
    lines.append(f"```{config.CLI_CODE_FENCE_LANGUAGE}")
    lines.append(f"# {config.CLI_BLOCK_TITLE}")

    if config.CLI_DESCRIPTION.strip():
        lines.append(f"# {config.CLI_DESCRIPTION}")

    meta_line = build_cli_meta_line(snapshot)
    if meta_line:
        if config.CLI_COMPACT_META:
            lines.append("# " + meta_line)
        else:
            for piece in meta_line.split(" | "):
                lines.append(f"# {piece}")

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


# ============================================================
# RENDER METADATA
# ============================================================

def write_render_metadata(
    snapshot: dict[str, Any],
    readme_changed: bool,
    rendered_visual: bool,
    rendered_cli: bool,
) -> None:
    payload = {
        "meta": {
            "rendered_at": utc_now_iso(),
            "render_mode": (
                f'option1={"on" if config.OPTION1_COVERS_ONLY_ENABLED else "off"}|'
                f'option2={"on" if config.OPTION2_CARD_TABLE_ENABLED else "off"}|'
                f'option3_cli={"on" if config.OPTION3_CLI_ENABLED else "off"}'
            ),
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


# ============================================================
# MAIN
# ============================================================

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
                    "limit": config.CURRENTLY_READING_LIMIT,
                    "item_count": 0,
                    "books": [],
                },
                "recent_read": {
                    "enabled": config.SHOW_RECENT_READ_SECTION,
                    "title": config.VISUAL_RECENT_READ_TITLE,
                    "shelf": config.RECENT_READ_SHELF,
                    "limit": config.RECENT_READ_LIMIT,
                    "item_count": 0,
                    "books": [],
                },
            },
        }

    readme = read_text(config.README_PATH)

    render_visual = config.OPTION1_COVERS_ONLY_ENABLED or config.OPTION2_CARD_TABLE_ENABLED
    render_cli = config.OPTION3_CLI_ENABLED

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
