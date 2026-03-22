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
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/2.0; +https://github.com/felipealfonsog)"


# ============================================================
# GOODREADS SOURCE
# ============================================================
# Tu ID numérico real de Goodreads.
GOODREADS_USER_ID = "10606567"

# Plantilla RSS de shelf.
GOODREADS_RSS_URL_TEMPLATE = (
    "https://www.goodreads.com/review/list_rss/{user_id}?shelf={shelf}"
)


# ============================================================
# SECTIONS / SHELVES
# ============================================================
# Puedes activar/desactivar cada sección por separado.

# SHOW_CURRENTLY_READING_SECTION:
#   True  -> renderiza la sección "currently reading"
#   False -> no la muestra
SHOW_CURRENTLY_READING_SECTION = True

# SHOW_RECENT_READ_SECTION:
#   True  -> renderiza la sección "recently read"
#   False -> no la muestra
SHOW_RECENT_READ_SECTION = True

# Shelf que se usará para "currently reading"
CURRENTLY_READING_SHELF = "currently-reading"

# Shelf que se usará para "recently read"
RECENT_READ_SHELF = "read"

# Cantidad de libros por sección
CURRENTLY_READING_LIMIT = 6
RECENT_READ_LIMIT = 12


# ============================================================
# GLOBAL RENDER CONTROL
# ============================================================
# Qué bloques renderizar en README:
#   "visual" -> solo visual
#   "cli"    -> solo CLI
#   "both"   -> ambos
RENDER_MODE = "both"

# Si un bloque no se usa:
#   True  -> lo deja intacto
#   False -> lo vacía
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

# Mostrar link textual pequeño debajo del caption en visual.
SHOW_VISUAL_TEXT_LINK = True
VISUAL_TEXT_LINK_LABEL = "open"


# ============================================================
# VISUAL STYLE
# ============================================================
# Títulos de bloque
VISUAL_BLOCK_TITLE = "Goodreads Reading Intelligence"
VISUAL_CURRENTLY_READING_TITLE = "Currently Reading"
VISUAL_RECENT_READ_TITLE = "Recently Read"

# Alineación general
VISUAL_ALIGN = "center"

# Tamaño de portadas
VISUAL_COVER_WIDTH = 58
VISUAL_COVER_HEIGHT = 88

# Espaciado entre items
VISUAL_ITEM_MARGIN_PX = 8

# Caption
VISUAL_SHOW_CAPTION = True
VISUAL_CAPTION_SHOW_TITLE = True
VISUAL_CAPTION_SHOW_AUTHOR = True
VISUAL_CAPTION_MAX_TITLE_LENGTH = 24
VISUAL_CAPTION_MAX_AUTHOR_LENGTH = 20

# Estilo de texto y título
VISUAL_TITLE_USE_SMALL = True
VISUAL_META_AS_SUBTEXT = True

# Bordes de imagen
VISUAL_IMAGE_BORDER_RADIUS_PX = 4
VISUAL_ENABLE_IMAGE_BORDER = False
VISUAL_IMAGE_BORDER_COLOR = "#bfbfbf"

# Placeholder si no hay cover
VISUAL_FALLBACK_BG = "#1f1f1f"
VISUAL_FALLBACK_TEXT_COLOR = "#f4f4f4"

# Cuántos items por fila
# OJO: no es tabla con bordes. Es una fila HTML calculada.
VISUAL_ITEMS_PER_ROW = 6


# ============================================================
# CLI STYLE
# ============================================================
CLI_BLOCK_TITLE = "Goodreads Telemetry"
CLI_CODE_FENCE_LANGUAGE = "text"

# Mostrar links inline en CLI
# RECOMENDADO: False para que no se vea saturado
CLI_SHOW_LINKS_INLINE = False

# Cantidad de dígitos del índice
CLI_BOOK_INDEX_PAD = 2

# Metadata compacta
CLI_COMPACT_META = True
CLI_DIVIDER = True

# Etiqueta last update
CLI_LABEL_LAST_UPDATE = "last_update"

# Límites visuales del CLI
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
