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
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/2.2; +https://github.com/felipealfonsog)"


# ============================================================
# GOODREADS SOURCE
# ============================================================
# Tu ID numérico real de Goodreads.
GOODREADS_USER_ID = "10606567"

# Plantilla RSS del shelf.
GOODREADS_RSS_URL_TEMPLATE = (
    "https://www.goodreads.com/review/list_rss/{user_id}?shelf={shelf}"
)


# ============================================================
# SECTIONS / SHELVES
# ============================================================
# Puedes activar o desactivar cada sección por separado.

# True -> mostrar sección "Currently Reading"
SHOW_CURRENTLY_READING_SECTION = True

# True -> mostrar sección "Recently Read"
SHOW_RECENT_READ_SECTION = True

# Shelf usado para "Currently Reading"
CURRENTLY_READING_SHELF = "currently-reading"

# Shelf usado para "Recently Read"
RECENT_READ_SHELF = "read"

# Cantidad máxima de libros por sección.
# Si Goodreads devuelve menos, se mostrarán menos.
CURRENTLY_READING_LIMIT = 8
RECENT_READ_LIMIT = 10


# ============================================================
# GLOBAL RENDER CONTROL
# ============================================================
# "visual" -> solo bloque visual
# "cli"    -> solo bloque CLI
# "both"   -> ambos
RENDER_MODE = "both"

# Si una parte no se renderiza:
# True  -> la deja intacta
# False -> la vacía
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

# Link textual pequeño en el visual.
SHOW_VISUAL_TEXT_LINK = True

# Texto moderno para el link visual.
VISUAL_TEXT_LINK_LABEL = "check the link"


# ============================================================
# VISUAL STYLE
# ============================================================
VISUAL_BLOCK_TITLE = "Goodreads Reading Intelligence"

# Texto descriptivo pequeño debajo del título principal.
VISUAL_BLOCK_DESCRIPTION = (
    "A compact reading snapshot showing what I am currently reading and "
    "the latest books I have recently finished on Goodreads."
)

VISUAL_CURRENTLY_READING_TITLE = "Currently Reading"
VISUAL_RECENT_READ_TITLE = "Recently Read"

# Alineación general base del bloque
VISUAL_ALIGN = "left"

# Tamaño de portadas
VISUAL_COVER_WIDTH = 46
VISUAL_COVER_HEIGHT = 70

# Margen entre items
VISUAL_ITEM_MARGIN_PX = 6

# Caption bajo la portada
VISUAL_SHOW_CAPTION = True
VISUAL_CAPTION_SHOW_TITLE = True
VISUAL_CAPTION_SHOW_AUTHOR = True
VISUAL_CAPTION_MAX_TITLE_LENGTH = 18
VISUAL_CAPTION_MAX_AUTHOR_LENGTH = 16

# Título principal pequeño
VISUAL_TITLE_USE_SMALL = True

# Mostrar línea meta pequeña debajo del título principal
VISUAL_META_AS_SUBTEXT = True

# Bordes y forma
VISUAL_IMAGE_BORDER_RADIUS_PX = 4
VISUAL_ENABLE_IMAGE_BORDER = False
VISUAL_IMAGE_BORDER_COLOR = "#bfbfbf"

# Placeholder si falta portada
VISUAL_FALLBACK_BG = "#1f1f1f"
VISUAL_FALLBACK_TEXT_COLOR = "#f4f4f4"


# ============================================================
# CLI STYLE
# ============================================================
CLI_BLOCK_TITLE = "Goodreads Telemetry"

# Lenguaje del code fence
CLI_CODE_FENCE_LANGUAGE = "text"

# Mostrar links inline en CLI
# Recomendado False para que se vea limpio.
CLI_SHOW_LINKS_INLINE = False

# Dígitos del índice
CLI_BOOK_INDEX_PAD = 2

# Metadata compacta arriba
CLI_COMPACT_META = True

# Línea en blanco entre metadata y contenido
CLI_DIVIDER = True

# Etiqueta last update
CLI_LABEL_LAST_UPDATE = "last_update"

# Texto descriptivo pequeño para CLI
CLI_DESCRIPTION = (
    "Structured shelf telemetry derived from Goodreads RSS with validated caching continuity."
)

# Límites opcionales del CLI
# 0 = no truncar
CLI_MAX_TITLE_LENGTH = 0
CLI_MAX_AUTHOR_LENGTH = 0


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
