from typing import Any

import GoodreadsConfig as config
from GoodreadsUtils import (
    ensure_dir,
    html_escape,
    md_escape_inline,
    read_json,
    read_text,
    replace_between_markers,
    sha256_json,
    truncate,
    utc_now_iso,
    write_json,
    write_text_if_changed,
)


def format_meta_lines(meta: dict[str, Any]) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []

    if config.SHOW_SHELF:
        lines.append(("shelf", str(meta.get("shelf", ""))))
    if config.SHOW_ITEM_COUNT:
        lines.append(("books_loaded", str(meta.get("item_count", 0))))
    if config.SHOW_STATUS:
        lines.append(("status", str(meta.get("status", ""))))
    if config.SHOW_FETCH_MODE:
        lines.append(("fetch_mode", str(meta.get("fetch_mode", ""))))
    if config.SHOW_LAST_SYNC:
        lines.append(("last_sync", str(meta.get("last_successful_sync", ""))))
    if config.SHOW_SOURCE:
        lines.append(("source", str(meta.get("source", ""))))

    return lines


def render_cli_block(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    books = snapshot.get("books", [])[: config.BOOKS_LIMIT]

    lines: list[str] = []
    lines.append("```text")
    lines.append(f"[{config.CLI_BLOCK_TITLE}]")

    if config.CLI_DIVIDER:
        lines.append("")

    meta_lines = format_meta_lines(meta)
    key_width = config.CLI_META_KEY_WIDTH if config.CLI_ALIGN_KEYS else 0

    for key, value in meta_lines:
        if config.CLI_ALIGN_KEYS:
            lines.append(f"{key.ljust(key_width)} : {value}")
        else:
            lines.append(f"{key}: {value}")

    if books:
        lines.append("")
        for idx, book in enumerate(books, start=1):
            key = f"{config.CLI_BOOK_KEY_PREFIX}_{str(idx).zfill(config.CLI_BOOK_INDEX_PAD)}"
            title = book.get("title", "")
            author = book.get("author", "")
            link = book.get("link", "")

            parts = []
            if config.SHOW_TITLE and title:
                parts.append(title)
            if config.SHOW_AUTHOR and author:
                parts.append(author)

            value = " — ".join(parts) if parts else title or author or "Untitled"

            if config.SHOW_LINK and link:
                value = f"{value} | {link}"

            if config.CLI_ALIGN_KEYS:
                lines.append(f"{key.ljust(key_width)} : {value}")
            else:
                lines.append(f"{key}: {value}")
    else:
        lines.append("")
        lines.append(config.CLI_EMPTY_MESSAGE)

    lines.append("```")
    return "\n".join(lines)


def render_visual_caption(book: dict[str, Any]) -> str:
    caption_parts = []

    if config.VISUAL_CAPTION_SHOW_TITLE and config.SHOW_TITLE:
        title = truncate(book.get("title", ""), config.VISUAL_CAPTION_MAX_TITLE_LENGTH)
        if title:
            caption_parts.append(html_escape(title))

    if config.VISUAL_CAPTION_SHOW_AUTHOR and config.SHOW_AUTHOR:
        author = truncate(book.get("author", ""), config.VISUAL_CAPTION_MAX_AUTHOR_LENGTH)
        if author:
            caption_parts.append(html_escape(author))

    return "<br/>".join(caption_parts)


def render_visual_item(book: dict[str, Any]) -> str:
    title = book.get("title", "")
    author = book.get("author", "")
    link = book.get("link", "")
    cover = book.get("cover", "")

    alt_parts = []
    if config.SHOW_TITLE and title:
        alt_parts.append(title)
    if config.SHOW_AUTHOR and author:
        alt_parts.append(author)
    alt = " — ".join(alt_parts) if alt_parts else "Book cover"

    image_html = ""
    if config.SHOW_COVER and cover:
        image_html = (
            f'<img src="{html_escape(cover)}" '
            f'width="{config.VISUAL_COVER_WIDTH}" '
            f'alt="{html_escape(alt)}" />'
        )
    else:
        fallback_label = html_escape(truncate(title or "Untitled", 26))
        image_html = (
            f'<div style="display:inline-block;width:{config.VISUAL_COVER_WIDTH}px;'
            f'padding:6px;border:1px solid #444;border-radius:6px;">'
            f"{fallback_label}</div>"
        )

    if config.SHOW_LINK and link:
        image_html = f'<a href="{html_escape(link)}">{image_html}</a>'

    if config.VISUAL_SHOW_CAPTION:
        caption = render_visual_caption(book)
        if caption:
            return (
                '<td align="center" valign="top" style="padding:8px;">'
                f"{image_html}<br/>{caption}"
                "</td>"
            )

    return f'<td align="center" valign="top" style="padding:8px;">{image_html}</td>'


def render_visual_block(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    books = snapshot.get("books", [])[: config.BOOKS_LIMIT]

    lines: list[str] = [f"### {config.VISUAL_BLOCK_TITLE}"]

    if config.VISUAL_INSERT_BLANK_LINE_AFTER_TITLE:
        lines.append("")

    meta_summary_parts = []
    if config.SHOW_SHELF:
        meta_summary_parts.append(f"shelf: **{md_escape_inline(str(meta.get('shelf', '')))}**")
    if config.SHOW_ITEM_COUNT:
        meta_summary_parts.append(f"books: **{md_escape_inline(str(meta.get('item_count', 0)))}**")
    if config.SHOW_STATUS:
        meta_summary_parts.append(f"status: **{md_escape_inline(str(meta.get('status', '')))}**")
    if config.SHOW_LAST_SYNC:
        sync = str(meta.get("last_successful_sync", ""))
        if sync:
            meta_summary_parts.append(f"last sync: **{md_escape_inline(sync)}**")

    if meta_summary_parts:
        lines.append(" | ".join(meta_summary_parts))
        lines.append("")

    if not books:
        lines.append(config.VISUAL_EMPTY_MESSAGE)
        return "\n".join(lines)

    lines.append(f'<table align="{html_escape(config.VISUAL_ALIGN)}">')
    col_count = max(1, config.VISUAL_COLUMNS)

    for idx, book in enumerate(books):
        if idx % col_count == 0:
            lines.append("<tr>")

        lines.append(render_visual_item(book))

        if idx % col_count == col_count - 1:
            lines.append("</tr>")

    if len(books) % col_count != 0:
        lines.append("</tr>")

    lines.append("</table>")
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
            "books_limit": config.BOOKS_LIMIT,
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
                "shelf": config.GOODREADS_SHELF,
                "status": "no_snapshot",
                "fetch_mode": "none",
                "last_attempted_sync": "",
                "last_successful_sync": "",
                "item_count": 0,
                "error_message": "No cache file present.",
            },
            "books": [],
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
