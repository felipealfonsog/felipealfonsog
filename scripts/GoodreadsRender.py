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
    """
    Devuelve la mejor fecha/hora UTC disponible para mostrar como last_update.
    Prioridad:
      1. last_attempted_sync
      2. last_successful_sync
      3. utc_now_iso() como fallback extremo
    """
    meta = snapshot.get("meta", {})
    value = str(meta.get("last_attempted_sync", "")).strip()
    if value:
        return value

    value = str(meta.get("last_successful_sync", "")).strip()
    if value:
        return value

    return utc_now_iso()


def render_cli_block(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    books = snapshot.get("books", [])[: config.BOOKS_LIMIT]

    lines: list[str] = []
    lines.append(f"```{config.CLI_CODE_FENCE_LANGUAGE}")
    lines.append(f"# {config.CLI_BLOCK_TITLE}")

    meta_parts = []

    if config.SHOW_SHELF:
        meta_parts.append(f"shelf={meta.get('shelf', '')}")

    if config.SHOW_ITEM_COUNT:
        meta_parts.append(f"books={meta.get('item_count', 0)}")

    if config.SHOW_STATUS:
        meta_parts.append(f"status={meta.get('status', '')}")

    if config.SHOW_FETCH_MODE:
        meta_parts.append(f"mode={meta.get('fetch_mode', '')}")

    if config.SHOW_LAST_SYNC:
        meta_parts.append(f"sync={meta.get('last_successful_sync', '')}")

    if config.CLI_INCLUDE_LAST_UPDATE:
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

    if not books:
        lines.append("# no data available")
    else:
        for idx, book in enumerate(books, start=1):
            title = str(book.get("title", "") or "Untitled")
            author = str(book.get("author", "") or "")
            link = str(book.get("link", "") or "")

            if config.CLI_MAX_TITLE_LENGTH > 0:
                title = truncate(title, config.CLI_MAX_TITLE_LENGTH)

            if config.CLI_MAX_AUTHOR_LENGTH > 0 and author:
                author = truncate(author, config.CLI_MAX_AUTHOR_LENGTH)

            line = f"{str(idx).zfill(config.CLI_BOOK_INDEX_PAD)}. {title}"

            if config.SHOW_AUTHOR and author:
                line += f" — {author}"

            if config.SHOW_LINK and config.CLI_SHOW_LINKS_INLINE and link:
                line += f"  [{link}]"

            lines.append(line)

    lines.append("```")
    return "\n".join(lines)


def render_visual_caption(book: dict[str, Any]) -> str:
    caption_parts: list[str] = []

    if config.VISUAL_CAPTION_SHOW_TITLE and config.SHOW_TITLE:
        title = truncate(str(book.get("title", "") or ""), config.VISUAL_CAPTION_MAX_TITLE_LENGTH)
        if title:
            caption_parts.append(html_escape(title))

    if config.VISUAL_CAPTION_SHOW_AUTHOR and config.SHOW_AUTHOR:
        author = truncate(str(book.get("author", "") or ""), config.VISUAL_CAPTION_MAX_AUTHOR_LENGTH)
        if author:
            caption_parts.append(html_escape(author))

    return "<br/>".join(caption_parts)


def render_visual_item(book: dict[str, Any]) -> str:
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

    caption = ""
    if config.VISUAL_SHOW_CAPTION:
        caption = render_visual_caption(book)

    border_style = ""
    if config.VISUAL_ENABLE_IMAGE_BORDER:
        border_style = f"border:1px solid {config.VISUAL_IMAGE_BORDER_COLOR};"

    if config.SHOW_COVER and cover:
        image_html = (
            f'<img src="{html_escape(cover)}" '
            f'width="{config.VISUAL_COVER_WIDTH}" '
            f'height="{config.VISUAL_COVER_HEIGHT}" '
            f'alt="{html_escape(alt)}" '
            f'style="object-fit:cover;'
            f'border-radius:{config.VISUAL_IMAGE_BORDER_RADIUS_PX}px;'
            f'{border_style}" />'
        )
    else:
        fallback_label = html_escape(truncate(title or "Untitled", 18))
        image_html = (
            f'<div style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:{config.VISUAL_COVER_WIDTH}px;'
            f'height:{config.VISUAL_COVER_HEIGHT}px;'
            f'background:{config.VISUAL_FALLBACK_BG};'
            f'color:{config.VISUAL_FALLBACK_TEXT_COLOR};'
            f'border-radius:{config.VISUAL_IMAGE_BORDER_RADIUS_PX}px;'
            f'font-size:10px;text-align:center;padding:4px;overflow:hidden;'
            f'{border_style}">{fallback_label}</div>'
        )

    if config.SHOW_LINK and link:
        image_html = f'<a href="{html_escape(link)}">{image_html}</a>'

    html_parts: list[str] = []
    html_parts.append(
        f'<span style="display:inline-block;vertical-align:top;'
        f'margin:{config.VISUAL_ITEM_MARGIN_PX}px;text-align:center;">'
    )
    html_parts.append(image_html)

    if caption:
        html_parts.append(f"<br/><sub>{caption}</sub>")

    if config.VISUAL_SHOW_TEXT_LINK_UNDER_CAPTION and config.SHOW_LINK and link:
        html_parts.append(
            f'<br/><sub><a href="{html_escape(link)}">{html_escape(config.VISUAL_TEXT_LINK_LABEL)}</a></sub>'
        )

    html_parts.append("</span>")
    return "".join(html_parts)


def render_visual_block(snapshot: dict[str, Any]) -> str:
    meta = snapshot.get("meta", {})
    books = snapshot.get("books", [])[: config.BOOKS_LIMIT]

    lines: list[str] = []

    lines.append(f'<sub><strong>{html_escape(config.VISUAL_BLOCK_TITLE)}</strong></sub>')

    if config.VISUAL_INSERT_BLANK_LINE_AFTER_TITLE:
        lines.append("")

    if config.VISUAL_META_AS_SUBTEXT:
        meta_parts = []

        if config.SHOW_SHELF:
            meta_parts.append(f"shelf: {html_escape(str(meta.get('shelf', '')))}")

        if config.SHOW_ITEM_COUNT:
            meta_parts.append(f"books: {html_escape(str(meta.get('item_count', 0)))}")

        if config.SHOW_STATUS:
            meta_parts.append(f"status: {html_escape(str(meta.get('status', '')))}")

        if config.SHOW_LAST_SYNC:
            sync = str(meta.get("last_successful_sync", "")).strip()
            if sync:
                meta_parts.append(f"sync: {html_escape(sync)}")

        if meta_parts:
            lines.append(f"<sub>{' • '.join(meta_parts)}</sub>")
            lines.append("")

    if not books:
        lines.append(config.VISUAL_EMPTY_MESSAGE)
        return "\n".join(lines)

    lines.append(f'<div align="{html_escape(config.VISUAL_ALIGN)}">')

    for book in books:
        lines.append(render_visual_item(book))

    lines.append("</div>")

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
