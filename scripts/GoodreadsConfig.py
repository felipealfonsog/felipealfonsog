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
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/6.0; +https://github.com/felipealfonsog)"


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
# GLOBAL RENDER CONTROL
# ============================================================
RENDER_MODE = "both"
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
VISUAL_META_AS_SUBTEXT = True
VISUAL_SHOW_DESCRIPTION = True

# No más texto tipo "check the link"
SHOW_VISUAL_TEXT_LINK = False
VISUAL_TEXT_LINK_LABEL = "check the link"

# Caption
VISUAL_SHOW_CAPTION = True
VISUAL_CAPTION_SHOW_TITLE = True
VISUAL_CAPTION_SHOW_AUTHOR = True

# Título link, autor no
VISUAL_CAPTION_TITLE_IS_LINK = True
VISUAL_CAPTION_AUTHOR_IS_LINK = False

VISUAL_CAPTION_MAX_TITLE_LENGTH = 18
VISUAL_CAPTION_MAX_AUTHOR_LENGTH = 16

# Tamaños
VISUAL_COVER_WIDTH = 42
VISUAL_COVER_HEIGHT = 64

# Card width y spacing
VISUAL_CARD_WIDTH_PX = 78
VISUAL_CARD_MARGIN_RIGHT_PX = 8
VISUAL_CARD_MARGIN_BOTTOM_PX = 10
VISUAL_CAPTION_TOP_MARGIN_PX = 3
VISUAL_AUTHOR_TOP_MARGIN_PX = 1

# Cantidad por fila
VISUAL_ITEMS_PER_ROW = 6

# Layout basado en SPAN inline-block
VISUAL_CARD_USE_SPAN = True
VISUAL_CARD_TEXT_ALIGN = "center"

# Bordes / forma
VISUAL_IMAGE_BORDER_RADIUS_PX = 4
VISUAL_ENABLE_IMAGE_BORDER = False
VISUAL_IMAGE_BORDER_COLOR = "#bfbfbf"

# Placeholder
VISUAL_FALLBACK_BG = "#1f1f1f"
VISUAL_FALLBACK_TEXT_COLOR = "#f4f4f4"

# Headers y separación
VISUAL_SECTION_HEADER_ALIGN = "left"
VISUAL_SECTION_SPACER_PX = 6
VISUAL_SECTION_BOTTOM_SPACER_PX = 12


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
