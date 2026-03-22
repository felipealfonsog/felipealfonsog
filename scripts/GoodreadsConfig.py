from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
README_PATH = ROOT_DIR / "README.md"
DATA_DIR = ROOT_DIR / "data"

CACHE_PATH = DATA_DIR / "GoodreadsCache.json"
LAST_RENDER_PATH = DATA_DIR / "GoodreadsLastRender.json"

REQUEST_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/1.0; +https://github.com/felipealfonsog)"

# -------------------------------------------------------------------
# SOURCE
# -------------------------------------------------------------------

GOODREADS_USER_ID = "YOUR_GOODREADS_USER_ID"
GOODREADS_SHELF = "read"
GOODREADS_PER_PAGE = 100

# Goodreads shelf RSS commonly follows this shape:
# https://www.goodreads.com/review/list_rss/<USER_ID>?shelf=<SHELF>
GOODREADS_RSS_URL_TEMPLATE = (
    "https://www.goodreads.com/review/list_rss/{user_id}"
    "?shelf={shelf}"
)

# -------------------------------------------------------------------
# GLOBAL RENDER CONTROL
# -------------------------------------------------------------------

BOOKS_LIMIT = 15

# visual | cli | both
RENDER_MODE = "both"

# If a render block is not selected, preserve it as-is in README.
PRESERVE_UNUSED_BLOCKS = True

# -------------------------------------------------------------------
# TOGGLES: GLOBAL META
# -------------------------------------------------------------------

SHOW_STATUS = True
SHOW_LAST_SYNC = True
SHOW_SOURCE = True
SHOW_SHELF = True
SHOW_ITEM_COUNT = True
SHOW_FETCH_MODE = True

# -------------------------------------------------------------------
# TOGGLES: BOOK FIELDS
# -------------------------------------------------------------------

SHOW_TITLE = True
SHOW_AUTHOR = True
SHOW_LINK = True
SHOW_COVER = True

# -------------------------------------------------------------------
# VISUAL BLOCK
# -------------------------------------------------------------------

VISUAL_BLOCK_TITLE = "Goodreads Shelf"
VISUAL_ALIGN = "center"
VISUAL_COLUMNS = 5
VISUAL_COVER_WIDTH = 88
VISUAL_SHOW_CAPTION = True
VISUAL_CAPTION_SHOW_TITLE = True
VISUAL_CAPTION_SHOW_AUTHOR = False
VISUAL_CAPTION_MAX_TITLE_LENGTH = 42
VISUAL_CAPTION_MAX_AUTHOR_LENGTH = 32
VISUAL_INSERT_BLANK_LINE_AFTER_TITLE = False

# -------------------------------------------------------------------
# CLI BLOCK
# -------------------------------------------------------------------

CLI_BLOCK_TITLE = "Goodreads Telemetry"
CLI_STYLE = "telemetry"
CLI_ALIGN_KEYS = True
CLI_DIVIDER = True
CLI_BOOK_KEY_PREFIX = "book"
CLI_META_KEY_WIDTH = 12
CLI_BOOK_INDEX_PAD = 2

# -------------------------------------------------------------------
# FALLBACK / VALIDATION
# -------------------------------------------------------------------

USE_CACHE_FALLBACK = True
PRESERVE_LAST_GOOD_SNAPSHOT = True
STRICT_VALIDATION = True
MIN_VALID_BOOKS = 1
MAX_DUPLICATE_RATIO = 0.60

# If Goodreads returns too little or malformed data, do not overwrite cache.
ALLOW_EMPTY_COVER = True
ALLOW_EMPTY_LINK = False
ALLOW_EMPTY_AUTHOR = False

# -------------------------------------------------------------------
# README MARKERS
# -------------------------------------------------------------------

README_MARKER_VISUAL_START = "<!-- GOODREADS:VISUAL_START -->"
README_MARKER_VISUAL_END = "<!-- GOODREADS:VISUAL_END -->"

README_MARKER_CLI_START = "<!-- GOODREADS:CLI_START -->"
README_MARKER_CLI_END = "<!-- GOODREADS:CLI_END -->"

# -------------------------------------------------------------------
# GIT COMMIT NOISE REDUCTION
# -------------------------------------------------------------------

WRITE_FILES_PRETTY = True
JSON_INDENT = 2
JSON_SORT_KEYS = False

# -------------------------------------------------------------------
# OPTIONAL DECORATION
# -------------------------------------------------------------------

SOURCE_LABEL = "goodreads_rss"
VISUAL_EMPTY_MESSAGE = "No valid Goodreads snapshot available."
CLI_EMPTY_MESSAGE = "No valid Goodreads snapshot available."
