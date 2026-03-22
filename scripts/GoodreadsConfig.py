from pathlib import Path


# ============================================================
# PATHS
# ============================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
README_PATH = ROOT_DIR / "README.md"
DATA_DIR = ROOT_DIR / "data"
CACHE_PATH = DATA_DIR / "GoodreadsCache.json"
LAST_RENDER_PATH = DATA_DIR / "GoodreadsLastRender.json"


# ============================================================
# NETWORK
# ============================================================
REQUEST_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/12.1; +https://github.com/felipealfonsog)"


# ============================================================
# GOODREADS SOURCE
# ============================================================
GOODREADS_USER_ID = "10606567"
GOODREADS_RSS_URL_TEMPLATE = (
    "https://www.goodreads.com/review/list_rss/{user_id}?shelf={shelf}"
)


# ============================================================
# SECTION TOGGLES
# ============================================================
SHOW_CURRENTLY_READING_SECTION = True
SHOW_RECENT_READ_SECTION = True

CURRENTLY_READING_SHELF = "currently-reading"
RECENT_READ_SHELF = "read"


# ============================================================
# SECTION LIMITS
# ============================================================
GLOBAL_SECTION_LIMIT = 10
USE_GLOBAL_SECTION_LIMIT = False

CURRENTLY_READING_LIMIT = 8
RECENT_READ_LIMIT = 10


# ============================================================
# RENDER MODES
# ============================================================
# VISUAL_MODE:
#   "covers_and_list"  -> opción 1 recomendada
#   "card_table"       -> opción 2 guardada
VISUAL_MODE = "covers_and_list"

SHOW_VISUAL_BLOCK = True
SHOW_CLI_BLOCK = True

PRESERVE_UNUSED_BLOCKS = True


# ============================================================
# GLOBAL META TOGGLES
# ============================================================
SHOW_STATUS = True
SHOW_LAST_SYNC = True
SHOW_SOURCE = True
SHOW_FETCH_MODE = True
SHOW_LAST_UPDATE = True


# ============================================================
# BOOK FIELD TOGGLES
# ============================================================
SHOW_TITLE = True
SHOW_AUTHOR = True
SHOW_LINK = True
SHOW_COVER = True


# ============================================================
# VISUAL BLOCK
# ============================================================
VISUAL_BLOCK_TITLE = "Goodreads Reading Intelligence"
VISUAL_BLOCK_DESCRIPTION = (
    "A compact reading snapshot showing what I am currently reading and "
    "the latest books I have recently finished on Goodreads."
)

VISUAL_CURRENTLY_READING_TITLE = "Currently Reading"
VISUAL_RECENT_READ_TITLE = "Recently Read"

VISUAL_TITLE_USE_SMALL = True
VISUAL_META_AS_SUBTEXT = False
VISUAL_SHOW_DESCRIPTION = True

# Título con link, autor sin link
VISUAL_TITLE_IS_LINK = True
VISUAL_AUTHOR_IS_LINK = False

# 0 = no truncar
VISUAL_TITLE_MAX_LENGTH = 0
VISUAL_AUTHOR_MAX_LENGTH = 22

# Covers
VISUAL_COVER_WIDTH = 42
VISUAL_COVER_HEIGHT = 64
VISUAL_ITEMS_PER_ROW = 6

# Compact spacing
VISUAL_SECTION_HEADER_ALIGN = "left"
VISUAL_SECTION_TOP_SPACER_PX = 8
VISUAL_SECTION_SPACER_PX = 8
VISUAL_SECTION_BOTTOM_SPACER_PX = 14

# Fila de covers
VISUAL_COVERS_GAP_SPACES = " "
VISUAL_COVERS_ROW_BREAK = "<br/>"

# Listado compacto debajo
VISUAL_LIST_USE_SUB = True
VISUAL_LIST_SHOW_INDEX = False
VISUAL_LIST_PREFIX = "-"
VISUAL_LIST_SHOW_READ_MORE = False
VISUAL_READ_MORE_LABEL = "[read more]"
VISUAL_LIST_LINE_BREAK = "<br/>"

# Summary / description
# Goodreads RSS no entrega una sinopsis limpia útil, así que por defecto va apagado.
# Solo aplica a VISUAL_MODE = "covers_and_list"
SHOW_BOOK_SUMMARY = False
BOOK_SUMMARY_MAX_LENGTH = 140

# Opción 2: card table compacta guardada
VISUAL_TABLE_CELL_PADDING_PX = 4
VISUAL_TABLE_CELL_WIDTH_PX = 76
VISUAL_CAPTION_TOP_MARGIN_PX = 3
VISUAL_AUTHOR_TOP_MARGIN_PX = 1
VISUAL_FORCE_BORDERLESS_TABLE = True

# Estilo de imagen
VISUAL_IMAGE_BORDER_RADIUS_PX = 4
VISUAL_ENABLE_IMAGE_BORDER = False
VISUAL_IMAGE_BORDER_COLOR = "#bfbfbf"

VISUAL_FALLBACK_BG = "#ffffff"
VISUAL_FALLBACK_TEXT_COLOR = "#666666"

# Línea meta entre visual y CLI
SHOW_VISUAL_FOOTER_META = True
VISUAL_FOOTER_META_PREFIX = ""
VISUAL_FOOTER_META_USE_SUB = True
VISUAL_FOOTER_TOP_SPACER_PX = 8
VISUAL_FOOTER_BOTTOM_SPACER_PX = 10


# ============================================================
# CLI STYLE
# ============================================================
CLI_BLOCK_TITLE = "Goodreads Telemetry"
CLI_DESCRIPTION = (
    "Structured shelf telemetry derived from Goodreads RSS with validated caching continuity."
)

CLI_CODE_FENCE_LANGUAGE = "text"
CLI_SHOW_LINKS_INLINE = False
CLI_BOOK_INDEX_PAD = 2
CLI_COMPACT_META = True
CLI_DIVIDER = True
CLI_LABEL_LAST_UPDATE = "last_update"

CLI_MAX_TITLE_LENGTH = 0
CLI_MAX_AUTHOR_LENGTH = 0

CLI_SHOW_SECTION_HEADERS = True
CLI_SHOW_SECTION_SHELF = True
CLI_SHOW_SECTION_BOOK_COUNT = True
CLI_SHOW_SECTION_LIMIT = True


# ============================================================
# FALLBACK / VALIDATION
# ============================================================
USE_CACHE_FALLBACK = True
PRESERVE_LAST_GOOD_SNAPSHOT = True
STRICT_VALIDATION = True
MIN_VALID_BOOKS_PER_SECTION = 1
MAX_DUPLICATE_RATIO = 0.60

ALLOW_EMPTY_COVER = True
ALLOW_EMPTY_LINK = False
ALLOW_EMPTY_AUTHOR = False


# ============================================================
# README MARKERS
# ============================================================
README_MARKER_VISUAL_START = "<!-- GOODREADS:VISUAL_START -->"
README_MARKER_VISUAL_END = "<!-- GOODREADS:VISUAL_END -->"

README_MARKER_CLI_START = "<!-- GOODREADS:CLI_START -->"
README_MARKER_CLI_END = "<!-- GOODREADS:CLI_END -->"


# ============================================================
# JSON WRITING
# ============================================================
JSON_INDENT = 2
JSON_SORT_KEYS = False


# ============================================================
# LABELS / EMPTY STATES
# ============================================================
SOURCE_LABEL = "goodreads_rss"
VISUAL_EMPTY_MESSAGE = "No valid Goodreads snapshot available."
CLI_EMPTY_MESSAGE = "No valid Goodreads snapshot available."
