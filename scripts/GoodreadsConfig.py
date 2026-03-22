from pathlib import Path


# ============================================================
# PATHS / PROJECT ROOT
# ============================================================
# ROOT_DIR:
#   Root del repositorio. Se calcula automáticamente desde la
#   ubicación de este archivo, así evitas problemas si ejecutas
#   el script desde otro directorio.
ROOT_DIR = Path(__file__).resolve().parent.parent

# README_PATH:
#   Ruta del README principal que será modificado por el renderer.
README_PATH = ROOT_DIR / "README.md"

# DATA_DIR:
#   Carpeta donde se guardan los snapshots/cache y metadatos.
DATA_DIR = ROOT_DIR / "data"

# CACHE_PATH:
#   Snapshot principal y persistente con los últimos datos válidos
#   obtenidos desde Goodreads. Este archivo NO lo llenas a mano.
CACHE_PATH = DATA_DIR / "GoodreadsCache.json"

# LAST_RENDER_PATH:
#   Metadatos del último render del README. Sirve para debugging
#   y para saber qué pasó en la última ejecución.
LAST_RENDER_PATH = DATA_DIR / "GoodreadsLastRender.json"


# ============================================================
# NETWORK / REQUEST SETTINGS
# ============================================================
# REQUEST_TIMEOUT:
#   Tiempo máximo en segundos para esperar la respuesta del feed.
#   Si Goodreads demora más que esto, el script caerá al fallback.
REQUEST_TIMEOUT = 20

# USER_AGENT:
#   User-Agent enviado en la petición HTTP.
#   Puedes cambiarlo si quieres, pero conviene dejar algo serio.
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/1.0; +https://github.com/felipealfonsog)"


# ============================================================
# GOODREADS SOURCE SETTINGS
# ============================================================
# GOODREADS_USER_ID:
#   Tu ID numérico de Goodreads.
#   EJEMPLO:
#       GOODREADS_USER_ID = "10606567"
GOODREADS_USER_ID = "10606567"

# GOODREADS_SHELF:
#   Shelf que quieres consultar.
#   EJEMPLOS TÍPICOS:
#       "read"
#       "currently-reading"
#       "to-read"
GOODREADS_SHELF = "read"

# GOODREADS_PER_PAGE:
#   Reservado por si más adelante quieres extender la lógica
#   para paginación o scraping adicional.
GOODREADS_PER_PAGE = 100

# GOODREADS_RSS_URL_TEMPLATE:
#   Plantilla base para construir la URL RSS del shelf.
#   Normalmente no necesitas tocar esto.
GOODREADS_RSS_URL_TEMPLATE = (
    "https://www.goodreads.com/review/list_rss/{user_id}"
    "?shelf={shelf}"
)


# ============================================================
# GLOBAL RENDER CONTROL
# ============================================================
# BOOKS_LIMIT:
#   Cantidad máxima de libros a mostrar/renderizar.
#   Afecta tanto la variante visual como la CLI.
BOOKS_LIMIT = 15

# RENDER_MODE:
#   Controla qué bloque(s) se renderizan en el README.
#   VALORES VÁLIDOS:
#       "visual"  -> solo bloque visual
#       "cli"     -> solo bloque CLI
#       "both"    -> ambos bloques
RENDER_MODE = "both"

# PRESERVE_UNUSED_BLOCKS:
#   Si el modo actual no usa uno de los bloques del README:
#   - True  -> deja intacto el bloque que no se usó
#   - False -> lo vacía
PRESERVE_UNUSED_BLOCKS = True


# ============================================================
# TOGGLES: GLOBAL META INFORMATION
# ============================================================
SHOW_STATUS = True
SHOW_LAST_SYNC = True
SHOW_SOURCE = True
SHOW_SHELF = True
SHOW_ITEM_COUNT = True
SHOW_FETCH_MODE = True


# ============================================================
# TOGGLES: BOOK FIELDS
# ============================================================
SHOW_TITLE = True
SHOW_AUTHOR = True
SHOW_LINK = True
SHOW_COVER = True


# ============================================================
# VISUAL BLOCK SETTINGS
# ============================================================
# VISUAL_BLOCK_TITLE:
#   Título del bloque visual.
#   Va renderizado en tamaño más pequeño/elegante.
VISUAL_BLOCK_TITLE = "Goodreads Shelf"

# VISUAL_ALIGN:
#   Alineación del bloque.
#   VALORES RECOMENDADOS:
#       "center"
#       "left"
VISUAL_ALIGN = "center"

# VISUAL_COLUMNS:
#   Valor referencial para mantener consistencia conceptual.
#   En esta nueva versión se usa layout inline limpio en vez de
#   tabla con recuadros. Aun así lo dejamos porque puede servir
#   para futuras variantes.
VISUAL_COLUMNS = 5

# VISUAL_COVER_WIDTH:
#   Tamaño de las portadas.
#   RECOMENDADO para que se vean pequeñas y ordenadas:
#       60
#       64
#       68
#       72
VISUAL_COVER_WIDTH = 64

# VISUAL_SHOW_CAPTION:
#   Si True, muestra un caption pequeño debajo de cada portada.
VISUAL_SHOW_CAPTION = True

# VISUAL_CAPTION_SHOW_TITLE:
#   Si True, el caption muestra el título.
VISUAL_CAPTION_SHOW_TITLE = True

# VISUAL_CAPTION_SHOW_AUTHOR:
#   Si True, el caption muestra también el autor.
#   Si quieres algo más limpio, déjalo en False.
VISUAL_CAPTION_SHOW_AUTHOR = False

# VISUAL_CAPTION_MAX_TITLE_LENGTH:
#   Límite del título en el caption.
VISUAL_CAPTION_MAX_TITLE_LENGTH = 26

# VISUAL_CAPTION_MAX_AUTHOR_LENGTH:
#   Límite del autor en el caption.
VISUAL_CAPTION_MAX_AUTHOR_LENGTH = 22

# VISUAL_INSERT_BLANK_LINE_AFTER_TITLE:
#   Añade línea en blanco después del título del bloque.
VISUAL_INSERT_BLANK_LINE_AFTER_TITLE = False

# VISUAL_META_AS_SUBTEXT:
#   Si True, muestra una línea pequeña de metadatos justo
#   debajo del título del bloque visual.
VISUAL_META_AS_SUBTEXT = True

# VISUAL_ITEM_MARGIN_PX:
#   Espaciado entre portadas.
VISUAL_ITEM_MARGIN_PX = 6

# VISUAL_IMAGE_BORDER_RADIUS_PX:
#   Bordes redondeados de la portada.
VISUAL_IMAGE_BORDER_RADIUS_PX = 4

# VISUAL_ENABLE_HOVER_SHADOW:
#   GitHub README no permite CSS avanzado real como en una app,
#   pero dejamos este toggle como punto de control futuro.
VISUAL_ENABLE_HOVER_SHADOW = False

# VISUAL_FALLBACK_BG:
#   Fondo del placeholder si una portada no existe.
VISUAL_FALLBACK_BG = "#222222"

# VISUAL_FALLBACK_TEXT_COLOR:
#   Color del texto del placeholder.
VISUAL_FALLBACK_TEXT_COLOR = "#f0f0f0"


# ============================================================
# CLI BLOCK SETTINGS
# ============================================================
# CLI_BLOCK_TITLE:
#   Título del bloque CLI.
CLI_BLOCK_TITLE = "Goodreads Telemetry"

# CLI_STYLE:
#   Estilo conceptual del bloque CLI.
#   Por ahora:
#       "telemetry"
#       "compact"
CLI_STYLE = "compact"

# CLI_ALIGN_KEYS:
#   Reservado para variantes futuras. En esta nueva versión
#   el layout CLI es más compacto y limpio.
CLI_ALIGN_KEYS = False

# CLI_DIVIDER:
#   Si True, deja una línea entre cabecera y contenido.
CLI_DIVIDER = True

# CLI_BOOK_KEY_PREFIX:
#   Reservado para posibles variantes antiguas o futuras.
CLI_BOOK_KEY_PREFIX = "book"

# CLI_META_KEY_WIDTH:
#   Reservado.
CLI_META_KEY_WIDTH = 12

# CLI_BOOK_INDEX_PAD:
#   Cantidad de dígitos del índice.
#   EJ:
#       2 -> 01, 02, 03
CLI_BOOK_INDEX_PAD = 2

# CLI_CODE_FENCE_LANGUAGE:
#   Lenguaje del bloque de código del README.
#   Puedes usar:
#       "text"
#       "bash"
#       "sh"
CLI_CODE_FENCE_LANGUAGE = "bash"

# CLI_COMPACT_META:
#   Si True, imprime la metadata en una sola línea compacta.
CLI_COMPACT_META = True

# CLI_SHOW_LINKS_INLINE:
#   Si True, agrega links inline al final de cada entrada.
#   Si quieres un CLI más limpio todavía, puedes poner False.
CLI_SHOW_LINKS_INLINE = True

# CLI_MAX_TITLE_LENGTH:
#   Límite opcional del título en CLI.
#   0 = sin truncar.
CLI_MAX_TITLE_LENGTH = 0

# CLI_MAX_AUTHOR_LENGTH:
#   Límite opcional del autor en CLI.
#   0 = sin truncar.
CLI_MAX_AUTHOR_LENGTH = 0


# ============================================================
# FALLBACK / VALIDATION SETTINGS
# ============================================================
USE_CACHE_FALLBACK = True
PRESERVE_LAST_GOOD_SNAPSHOT = True
STRICT_VALIDATION = True
MIN_VALID_BOOKS = 1
MAX_DUPLICATE_RATIO = 0.60

# Si Goodreads devuelve items sin algunos campos, estos toggles
# definen qué tan permisivo quieres ser.
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
# JSON OUTPUT / FILE WRITING
# ============================================================
WRITE_FILES_PRETTY = True
JSON_INDENT = 2
JSON_SORT_KEYS = False


# ============================================================
# OPTIONAL LABELS / EMPTY STATE TEXT
# ============================================================
SOURCE_LABEL = "goodreads_rss"
VISUAL_EMPTY_MESSAGE = "No valid Goodreads snapshot available."
CLI_EMPTY_MESSAGE = "No valid Goodreads snapshot available."
