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
#   Carpeta donde se guardan snapshots/cache y metadatos.
DATA_DIR = ROOT_DIR / "data"

# CACHE_PATH:
#   Snapshot persistente con los últimos datos válidos.
#   Este archivo NO lo llenas a mano.
CACHE_PATH = DATA_DIR / "GoodreadsCache.json"

# LAST_RENDER_PATH:
#   Metadatos del último render del README. Sirve para debugging.
LAST_RENDER_PATH = DATA_DIR / "GoodreadsLastRender.json"


# ============================================================
# NETWORK / REQUEST SETTINGS
# ============================================================
# REQUEST_TIMEOUT:
#   Tiempo máximo en segundos para esperar la respuesta del feed.
REQUEST_TIMEOUT = 20

# USER_AGENT:
#   User-Agent enviado en la petición HTTP.
USER_AGENT = "Mozilla/5.0 (compatible; GoodreadsTelemetry/1.0; +https://github.com/felipealfonsog)"


# ============================================================
# GOODREADS SOURCE SETTINGS
# ============================================================
# GOODREADS_USER_ID:
#   Tu ID numérico real de Goodreads.
#   EJEMPLO:
#       "10606567"
GOODREADS_USER_ID = "10606567"

# GOODREADS_SHELF:
#   Shelf que quieres consultar.
#   EJEMPLOS:
#       "read"
#       "currently-reading"
#       "to-read"
GOODREADS_SHELF = "read"

# GOODREADS_PER_PAGE:
#   Reservado por si en el futuro amplías la lógica de extracción.
GOODREADS_PER_PAGE = 100

# GOODREADS_RSS_URL_TEMPLATE:
#   Plantilla base para construir la URL RSS del shelf.
GOODREADS_RSS_URL_TEMPLATE = (
    "https://www.goodreads.com/review/list_rss/{user_id}"
    "?shelf={shelf}"
)


# ============================================================
# GLOBAL RENDER CONTROL
# ============================================================
# BOOKS_LIMIT:
#   Cantidad máxima de libros a mostrar/renderizar.
#   Afecta tanto la vista visual como la CLI.
#   EJEMPLOS:
#       10
#       15
#       20
#       25
BOOKS_LIMIT = 15

# RENDER_MODE:
#   Qué bloques se renderizan en README.
#   VALORES:
#       "visual" -> solo visual
#       "cli"    -> solo CLI
#       "both"   -> ambos
RENDER_MODE = "both"

# PRESERVE_UNUSED_BLOCKS:
#   Si el modo actual no usa uno de los bloques del README:
#   - True  -> deja el bloque intacto
#   - False -> lo vacía
PRESERVE_UNUSED_BLOCKS = True


# ============================================================
# TOGGLES: GLOBAL META INFORMATION
# ============================================================
# Estos toggles controlan metadatos generales visibles.

# SHOW_STATUS:
#   Muestra el estado del snapshot.
SHOW_STATUS = True

# SHOW_LAST_SYNC:
#   Muestra la fecha/hora del último sync válido.
SHOW_LAST_SYNC = True

# SHOW_SOURCE:
#   Muestra la fuente lógica del snapshot.
SHOW_SOURCE = True

# SHOW_SHELF:
#   Muestra el shelf actual.
SHOW_SHELF = True

# SHOW_ITEM_COUNT:
#   Muestra cuántos libros quedaron cargados.
SHOW_ITEM_COUNT = True

# SHOW_FETCH_MODE:
#   Muestra si la data vino de red o de cache.
SHOW_FETCH_MODE = True


# ============================================================
# TOGGLES: BOOK FIELDS
# ============================================================
# Estos toggles controlan qué datos mostrar por libro.

# SHOW_TITLE:
#   Mostrar el título del libro.
SHOW_TITLE = True

# SHOW_AUTHOR:
#   Mostrar el autor del libro.
SHOW_AUTHOR = True

# SHOW_LINK:
#   Mostrar/usar el link del libro.
#   - En visual: hace clickeable la portada
#   - En CLI: agrega el link inline al final
SHOW_LINK = True

# SHOW_COVER:
#   Mostrar la portada si existe.
SHOW_COVER = True


# ============================================================
# VISUAL BLOCK SETTINGS
# ============================================================
# VISUAL_BLOCK_TITLE:
#   Título visible del bloque visual.
VISUAL_BLOCK_TITLE = "Goodreads Shelf"

# VISUAL_ALIGN:
#   Alineación del contenedor visual.
#   VALORES RECOMENDADOS:
#       "center"
#       "left"
VISUAL_ALIGN = "center"

# VISUAL_COLUMNS:
#   Queda como referencia conceptual para futuras variantes.
#   En esta versión usamos inline layout, no tabla rígida.
VISUAL_COLUMNS = 5

# VISUAL_COVER_WIDTH:
#   Ancho de la portada en píxeles.
#   EJEMPLOS BONITOS:
#       56
#       60
#       64
#       68
VISUAL_COVER_WIDTH = 64

# VISUAL_COVER_HEIGHT:
#   Alto de la portada en píxeles.
#   Puedes ajustarlo independiente del ancho.
#   EJEMPLOS BONITOS:
#       88
#       96
#       100
VISUAL_COVER_HEIGHT = 96

# VISUAL_SHOW_CAPTION:
#   Si True, muestra un caption pequeño debajo de la portada.
VISUAL_SHOW_CAPTION = True

# VISUAL_CAPTION_SHOW_TITLE:
#   Si True, muestra el título en el caption.
VISUAL_CAPTION_SHOW_TITLE = True

# VISUAL_CAPTION_SHOW_AUTHOR:
#   Si True, muestra también el autor en el caption.
#   Si quieres un look más limpio, déjalo en False.
VISUAL_CAPTION_SHOW_AUTHOR = False

# VISUAL_CAPTION_MAX_TITLE_LENGTH:
#   Límite del título en el caption.
VISUAL_CAPTION_MAX_TITLE_LENGTH = 26

# VISUAL_CAPTION_MAX_AUTHOR_LENGTH:
#   Límite del autor en el caption.
VISUAL_CAPTION_MAX_AUTHOR_LENGTH = 22

# VISUAL_INSERT_BLANK_LINE_AFTER_TITLE:
#   Inserta una línea extra después del título del bloque.
VISUAL_INSERT_BLANK_LINE_AFTER_TITLE = False

# VISUAL_META_AS_SUBTEXT:
#   Si True, muestra una línea pequeña con metadata del shelf.
VISUAL_META_AS_SUBTEXT = True

# VISUAL_ITEM_MARGIN_PX:
#   Margen entre portadas.
VISUAL_ITEM_MARGIN_PX = 6

# VISUAL_IMAGE_BORDER_RADIUS_PX:
#   Bordes redondeados de la portada.
VISUAL_IMAGE_BORDER_RADIUS_PX = 4

# VISUAL_ENABLE_IMAGE_BORDER:
#   Si True, dibuja un borde sutil a cada portada.
#   Si quieres máxima limpieza visual, déjalo en False.
VISUAL_ENABLE_IMAGE_BORDER = False

# VISUAL_IMAGE_BORDER_COLOR:
#   Color del borde si VISUAL_ENABLE_IMAGE_BORDER = True.
VISUAL_IMAGE_BORDER_COLOR = "#bbbbbb"

# VISUAL_FALLBACK_BG:
#   Fondo del placeholder si un libro no trae portada.
VISUAL_FALLBACK_BG = "#222222"

# VISUAL_FALLBACK_TEXT_COLOR:
#   Color del texto del placeholder.
VISUAL_FALLBACK_TEXT_COLOR = "#f0f0f0"

# VISUAL_SHOW_TEXT_LINK_UNDER_CAPTION:
#   Si True, agrega un link textual pequeño bajo el caption.
#   Normalmente no hace falta si la portada ya es clickeable.
VISUAL_SHOW_TEXT_LINK_UNDER_CAPTION = False

# VISUAL_TEXT_LINK_LABEL:
#   Texto del link pequeño bajo el caption.
VISUAL_TEXT_LINK_LABEL = "view"


# ============================================================
# CLI BLOCK SETTINGS
# ============================================================
# CLI_BLOCK_TITLE:
#   Título del bloque CLI.
CLI_BLOCK_TITLE = "Goodreads Telemetry"

# CLI_STYLE:
#   Estilo conceptual.
#   VALORES SUGERIDOS:
#       "compact"
#       "telemetry"
CLI_STYLE = "compact"

# CLI_DIVIDER:
#   Si True, deja una línea en blanco entre cabecera y libros.
CLI_DIVIDER = True

# CLI_BOOK_INDEX_PAD:
#   Cantidad de dígitos para el índice.
#   EJ:
#       2 -> 01, 02
#       3 -> 001, 002
CLI_BOOK_INDEX_PAD = 2

# CLI_CODE_FENCE_LANGUAGE:
#   Lenguaje del bloque.
#   EJEMPLOS:
#       "bash"
#       "text"
#       "sh"
CLI_CODE_FENCE_LANGUAGE = "bash"

# CLI_COMPACT_META:
#   Si True, muestra la metadata en una sola línea compacta.
CLI_COMPACT_META = True

# CLI_SHOW_LINKS_INLINE:
#   Si True, agrega links inline al final de cada libro.
CLI_SHOW_LINKS_INLINE = True

# CLI_MAX_TITLE_LENGTH:
#   Límite opcional del título en CLI.
#   0 = no truncar.
CLI_MAX_TITLE_LENGTH = 0

# CLI_MAX_AUTHOR_LENGTH:
#   Límite opcional del autor en CLI.
#   0 = no truncar.
CLI_MAX_AUTHOR_LENGTH = 0

# CLI_INCLUDE_LAST_UPDATE:
#   Si True, agrega "last_update=<UTC>" en la metadata del CLI.
CLI_INCLUDE_LAST_UPDATE = True

# CLI_LABEL_LAST_UPDATE:
#   Nombre de la etiqueta last update en el CLI.
CLI_LABEL_LAST_UPDATE = "last_update"


# ============================================================
# FALLBACK / VALIDATION SETTINGS
# ============================================================
# Lógica defensiva. Muy importante.

# USE_CACHE_FALLBACK:
#   Si Goodreads falla, usa cache válida previa.
USE_CACHE_FALLBACK = True

# PRESERVE_LAST_GOOD_SNAPSHOT:
#   Nunca pisa el último snapshot válido con basura.
PRESERVE_LAST_GOOD_SNAPSHOT = True

# STRICT_VALIDATION:
#   Rechaza snapshots malos si es True.
STRICT_VALIDATION = True

# MIN_VALID_BOOKS:
#   Cantidad mínima de libros válidos para aceptar snapshot nuevo.
MIN_VALID_BOOKS = 1

# MAX_DUPLICATE_RATIO:
#   Máximo porcentaje de duplicados tolerados.
MAX_DUPLICATE_RATIO = 0.60

# ALLOW_EMPTY_COVER:
#   Permitir libros sin portada.
ALLOW_EMPTY_COVER = True

# ALLOW_EMPTY_LINK:
#   Permitir libros sin link.
ALLOW_EMPTY_LINK = False

# ALLOW_EMPTY_AUTHOR:
#   Permitir libros sin autor.
ALLOW_EMPTY_AUTHOR = False


# ============================================================
# README MARKERS
# ============================================================
# Delimitadores del README. No cambiarlos a la ligera.

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
# SOURCE_LABEL:
#   Nombre lógico de la fuente.
SOURCE_LABEL = "goodreads_rss"

# VISUAL_EMPTY_MESSAGE:
#   Mensaje mostrado si no hay snapshot visual válida.
VISUAL_EMPTY_MESSAGE = "No valid Goodreads snapshot available."

# CLI_EMPTY_MESSAGE:
#   Mensaje mostrado si no hay snapshot CLI válida.
CLI_EMPTY_MESSAGE = "No valid Goodreads snapshot available."
