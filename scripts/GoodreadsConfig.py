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
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/14.1; +https://github.com/felipealfonsog)"


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
# THREE OPTIONS
# ============================================================
OPTION1_COVERS_ONLY_ENABLED = True
OPTION2_CARD_TABLE_ENABLED = False
OPTION3_CLI_ENABLED = True

PRESERVE_UNUSED_BLOCKS = True


# ============================================================
# VISUAL BLOCK GENERAL
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
VISUAL_SECTION_HEADER_ALIGN = "left"

# Header / section spacing
VISUAL_SECTION_TOP_SPACER_PX = 16
VISUAL_SECTION_SPACER_PX = 14
VISUAL_SECTION_BOTTOM_SPACER_PX = 20


# ============================================================
# OPTION 1: COVERS ONLY
# ============================================================
OPTION1_SHOW_COVERS = True

OPTION1_COVER_WIDTH = 40
OPTION1_COVER_HEIGHT = 60
OPTION1_COVER_OBJECT_FIT = "cover"

OPTION1_ITEMS_PER_ROW = 6

OPTION1_COVERS_GAP_SPACES = " "
OPTION1_COVERS_ROW_BREAK = "<br/>"

OPTION1_IMAGE_BORDER_RADIUS_PX = 4
OPTION1_ENABLE_IMAGE_BORDER = False
OPTION1_IMAGE_BORDER_COLOR = "#bfbfbf"

OPTION1_FALLBACK_BG = "#f3f3f3"
OPTION1_FALLBACK_TEXT_COLOR = "#666666"


# ============================================================
# OPTION 2: OLD CARD TABLE STYLE
# ============================================================
OPTION2_SHOW_TITLE = True
OPTION2_SHOW_AUTHOR = True
OPTION2_SHOW_LINK = True
OPTION2_SHOW_COVER = True

OPTION2_COVER_WIDTH = 42
OPTION2_COVER_HEIGHT = 64
OPTION2_COVER_OBJECT_FIT = "cover"
OPTION2_ITEMS_PER_ROW = 6

OPTION2_TITLE_MAX_LENGTH = 24
OPTION2_AUTHOR_MAX_LENGTH = 18

OPTION2_TABLE_CELL_PADDING_PX = 4
OPTION2_TABLE_CELL_WIDTH_PX = 76
OPTION2_CAPTION_TOP_MARGIN_PX = 3
OPTION2_AUTHOR_TOP_MARGIN_PX = 1
OPTION2_FORCE_BORDERLESS_TABLE = True

OPTION2_IMAGE_BORDER_RADIUS_PX = 4
OPTION2_ENABLE_IMAGE_BORDER = False
OPTION2_IMAGE_BORDER_COLOR = "#bfbfbf"

OPTION2_FALLBACK_BG = "#f3f3f3"
OPTION2_FALLBACK_TEXT_COLOR = "#666666"


# ============================================================
# VISUAL FOOTER META (between visual and CLI)
# ============================================================
SHOW_VISUAL_FOOTER_META = True
SHOW_LAST_SYNC = True
SHOW_LAST_UPDATE = True
SHOW_SOURCE = True

VISUAL_FOOTER_META_USE_SUB = True
VISUAL_FOOTER_TOP_SPACER_PX = 18
VISUAL_FOOTER_BOTTOM_SPACER_PX = 16
VISUAL_FOOTER_SYNC_LABEL = "SYNC"


# ============================================================
# CLI (OPTION 3)
# ============================================================
SHOW_STATUS = True
SHOW_FETCH_MODE = True

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