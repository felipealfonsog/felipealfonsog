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
        img_html = (
            f'<img src="{html_escape(cover)}" '
            f'width="{config.VISUAL_COVER_WIDTH}" '
            f'height="{config.VISUAL_COVER_HEIGHT}" '
            f'alt="{html_escape(alt)}" '
            f'style="display:block;object-fit:cover;'
            f'border-radius:{config.VISUAL_IMAGE_BORDER_RADIUS_PX}px;'
            f'margin:0 auto;{border_style}" />'
        )
    else:
        img_html = (
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
        img_html = f'<a href="{html_escape(link)}">{img_html}</a>'

    text_bits: list[str] = []

    if config.VISUAL_SHOW_CAPTION:
        if config.VISUAL_CAPTION_SHOW_TITLE and config.SHOW_TITLE and title:
            text_bits.append(
                f'<div><sub>{html_escape(truncate(title, config.VISUAL_CAPTION_MAX_TITLE_LENGTH))}</sub></div>'
            )
        if config.VISUAL_CAPTION_SHOW_AUTHOR and config.SHOW_AUTHOR and author:
            text_bits.append(
                f'<div><sub>{html_escape(truncate(author, config.VISUAL_CAPTION_MAX_AUTHOR_LENGTH))}</sub></div>'
            )

    if config.SHOW_VISUAL_TEXT_LINK and config.SHOW_LINK and link:
        text_bits.append(
            f'<div><sub><a href="{html_escape(link)}">{html_escape(config.VISUAL_TEXT_LINK_LABEL)}</a></sub></div>'
        )

    text_html = "".join(text_bits)

    return (
        f'<span style="display:inline-block;vertical-align:top;'
        f'width:{config.VISUAL_COVER_WIDTH + 12}px;'
        f'margin:{config.VISUAL_ITEM_MARGIN_PX}px;'
        f'text-align:center;">'
        f'{img_html}'
        f'<div style="margin-top:4px;">{text_html}</div>'
        f'</span>'
    )


def render_visual_section(section: dict[str, Any], section_title: str) -> str:
    books = section.get("books", [])
    if not section.get("enabled", False):
        return ""

    header = f'<div align="left"><sub><strong>{html_escape(section_title)}</strong></sub></div>'

    if not books:
        return (
            f'{header}'
            f'<div align="left"><sub>{html_escape(config.VISUAL_EMPTY_MESSAGE)}</sub></div>'
        )

    items_html = "".join(render_visual_book_card(book) for book in books)

    return (
        f'{header}'
        f'<div align="center" style="margin-top:6px;">'
        f'{items_html}'
        f'</div>'
    )


def render_visual_block(snapshot: dict[str, Any]) -> str:
    sections = snapshot.get("sections", {})

    lines: list[str] = []

    if config.VISUAL_TITLE_USE_SMALL:
        lines.append(f'<sub><strong>{html_escape(config.VISUAL_BLOCK_TITLE)}</strong></sub>')
    else:
        lines.append(f'### {html_escape(config.VISUAL_BLOCK_TITLE)}')

    if config.VISUAL_BLOCK_DESCRIPTION.strip():
        lines.append(f'<sub>{html_escape(config.VISUAL_BLOCK_DESCRIPTION)}</sub>')

    if config.VISUAL_META_AS_SUBTEXT:
        meta_line = build_visual_meta_line(snapshot)
        if meta_line:
            lines.append(f'<sub>{meta_line}</sub>')

    current_html = ""
    recent_html = ""

    if config.SHOW_CURRENTLY_READING_SECTION:
        current_html = render_visual_section(
            sections.get("currently_reading", {}),
            config.VISUAL_CURRENTLY_READING_TITLE,
        )

    if config.SHOW_RECENT_READ_SECTION:
        recent_html = render_visual_section(
            sections.get("recent_read", {}),
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


def render_cli_section(section: dict[str, Any], label: str) -> list[str]:
    lines: list[str] = []

    if not section.get("enabled", False):
        return lines

    books = section.get("books", [])
    shelf = str(section.get("shelf", ""))

    lines.append(f"[{label}] shelf={shelf} | books={len(books)}")

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
            )
        )

    if config.SHOW_RECENT_READ_SECTION:
        lines.extend(
            render_cli_section(
                sections.get("recent_read", {}),
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
                    "item_count": 0,
                    "books": [],
                },
                "recent_read": {
                    "enabled": config.SHOW_RECENT_READ_SECTION,
                    "title": config.VISUAL_RECENT_READ_TITLE,
                    "shelf": config.RECENT_READ_SHELF,
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
