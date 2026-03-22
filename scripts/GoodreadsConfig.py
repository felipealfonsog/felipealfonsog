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
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/13.0; +https://github.com/felipealfonsog)"


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
#   "covers_only"      -> opción 1 actual
#   "card_table"       -> opción 2 guardada
VISUAL_MODE = "covers_only"

SHOW_VISUAL_BLOCK = True
SHOW_CLI_BLOCK = True

PRESERVE_UNUSED_BLOCKS = True


# ============================================================
# META TOGGLES
# ============================================================
SHOW_STATUS = True
SHOW_LAST_SYNC = True
SHOW_SOURCE = True
SHOW_FETCH_MODE = True
SHOW_LAST_UPDATE = True


# ============================================================
# VISUAL BLOCK
# ============================================================
VISUAL_BLOCK_TITLE = "Goodreads Reading Data"
VISUAL_BLOCK_DESCRIPTION = (
    "A compact reading snapshot showing what I am currently reading "
    "and the latest books I have recently finished on Goodreads."
)

VISUAL_CURRENTLY_READING_TITLE = "Currently Reading"
VISUAL_RECENT_READ_TITLE = "Recently Read"

VISUAL_TITLE_USE_SMALL = True
VISUAL_SHOW_DESCRIPTION = True

# Covers only mode: no titles, no authors, no summaries
SHOW_TITLE = False
SHOW_AUTHOR = False
SHOW_LINK = True
SHOW_COVER = True
SHOW_BOOK_SUMMARY = False

# Covers: all must have exactly the same visual dimensions
VISUAL_COVER_WIDTH = 40
VISUAL_COVER_HEIGHT = 60

# cover -> fills box, may crop slightly, all look uniform
# contain -> preserves full image, may leave empty padding
VISUAL_COVER_OBJECT_FIT = "cover"

# Number of covers per row
VISUAL_ITEMS_PER_ROW = 6

# Spacing
VISUAL_SECTION_HEADER_ALIGN = "left"
VISUAL_SECTION_TOP_SPACER_PX = 16
VISUAL_SECTION_SPACER_PX = 10
VISUAL_SECTION_BOTTOM_SPACER_PX = 16

# Use one normal space between adjacent images in the HTML row
VISUAL_COVERS_GAP_SPACES = " "
VISUAL_COVERS_ROW_BREAK = "<br/>"

# Visual style
VISUAL_IMAGE_BORDER_RADIUS_PX = 4
VISUAL_ENABLE_IMAGE_BORDER = False
VISUAL_IMAGE_BORDER_COLOR = "#bfbfbf"

VISUAL_FALLBACK_BG = "#f3f3f3"
VISUAL_FALLBACK_TEXT_COLOR = "#666666"

# Visual footer meta before CLI
SHOW_VISUAL_FOOTER_META = True
VISUAL_FOOTER_META_USE_SUB = True
VISUAL_FOOTER_TOP_SPACER_PX = 12
VISUAL_FOOTER_BOTTOM_SPACER_PX = 10

# ============================================================
# OPTION 2 (kept for future use)
# ============================================================
VISUAL_TABLE_CELL_PADDING_PX = 4
VISUAL_TABLE_CELL_WIDTH_PX = 76
VISUAL_CAPTION_TOP_MARGIN_PX = 3
VISUAL_AUTHOR_TOP_MARGIN_PX = 1
VISUAL_FORCE_BORDERLESS_TABLE = True

# Not used in covers_only, kept only for card_table mode
VISUAL_TITLE_IS_LINK = False
VISUAL_AUTHOR_IS_LINK = False
VISUAL_TITLE_MAX_LENGTH = 62
VISUAL_AUTHOR_MAX_LENGTH = 24


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