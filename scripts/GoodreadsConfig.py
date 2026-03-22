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
#       GOODREADS_USER_ID = "12345678"
#   IMPORTANTE:
#   - Debe ser string.
#   - Si queda como "YOUR_GOODREADS_USER_ID", el sync fallará.
GOODREADS_USER_ID = "10606567"

# GOODREADS_SHELF:
#   Shelf que quieres consultar.
#   EJEMPLOS TÍPICOS:
#       "read"
#       "currently-reading"
#       "to-read"
#   También podría servir con shelves custom tuyos si Goodreads
#   entrega RSS para ellos.
GOODREADS_SHELF = "read"

# GOODREADS_PER_PAGE:
#   Valor reservado por si más adelante quieres extender la lógica
#   para paginación o scraping adicional.
#   En esta versión no es crítico para el RSS base, pero queda aquí
#   como referencia configurable.
GOODREADS_PER_PAGE = 100

# GOODREADS_RSS_URL_TEMPLATE:
#   Plantilla base para construir la URL RSS del shelf.
#   Normalmente no necesitas tocar esto.
#   Formato esperado:
#       https://www.goodreads.com/review/list_rss/<USER_ID>?shelf=<SHELF>
GOODREADS_RSS_URL_TEMPLATE = (
    "https://www.goodreads.com/review/list_rss/{user_id}"
    "?shelf={shelf}"
)


# ============================================================
# GLOBAL RENDER CONTROL
# ============================================================
# BOOKS_LIMIT:
#   Cantidad máxima de libros a mostrar/renderizar.
#   Puedes poner, por ejemplo:
#       10
#       15
#       20
#       25
#   Este límite afecta tanto la variante visual como la CLI.
BOOKS_LIMIT = 15

# RENDER_MODE:
#   Controla qué bloque(s) se renderizan en el README.
#   VALORES VÁLIDOS:
#       "visual"  -> solo bloque visual
#       "cli"     -> solo bloque CLI
#       "both"    -> ambos bloques
#   RECOMENDADO:
#       "both"
RENDER_MODE = "both"

# PRESERVE_UNUSED_BLOCKS:
#   Si el modo actual no usa uno de los bloques del README:
#   - True  -> deja intacto el bloque que no se usó
#   - False -> lo vacía
#   RECOMENDADO:
#       True, para no borrar cosas innecesariamente.
PRESERVE_UNUSED_BLOCKS = True


# ============================================================
# TOGGLES: GLOBAL META INFORMATION
# ============================================================
# Estos toggles controlan qué metadatos generales aparecen
# en el bloque visual y/o en el bloque CLI.

# SHOW_STATUS:
#   Muestra el estado del snapshot.
#   Posibles valores visibles:
#       ok
#       cached_fallback
#       source_unavailable_using_cache
#       no_snapshot
SHOW_STATUS = True

# SHOW_LAST_SYNC:
#   Muestra la fecha/hora del último sync válido.
SHOW_LAST_SYNC = True

# SHOW_SOURCE:
#   Muestra la fuente lógica del snapshot.
#   Ejemplo visible:
#       goodreads_rss
SHOW_SOURCE = True

# SHOW_SHELF:
#   Muestra el nombre del shelf actual.
#   Ejemplo:
#       read
#       currently-reading
SHOW_SHELF = True

# SHOW_ITEM_COUNT:
#   Muestra cuántos libros quedaron cargados en el snapshot.
SHOW_ITEM_COUNT = True

# SHOW_FETCH_MODE:
#   Muestra si el render viene de red o desde cache.
#   Ejemplos:
#       network
#       cache
#       none
SHOW_FETCH_MODE = True


# ============================================================
# TOGGLES: BOOK FIELDS
# ============================================================
# Estos toggles controlan qué datos de cada libro se muestran.

# SHOW_TITLE:
#   Mostrar el título del libro.
SHOW_TITLE = True

# SHOW_AUTHOR:
#   Mostrar el autor del libro.
SHOW_AUTHOR = True

# SHOW_LINK:
#   Mostrar / usar el link del libro.
#   En visual:
#       hace clickeable la portada
#   En CLI:
#       añade la URL al final de cada línea del libro
SHOW_LINK = True

# SHOW_COVER:
#   Mostrar la portada si el feed la trae o si se logra extraer.
#   Si es False, el render visual usará un fallback textual.
SHOW_COVER = True


# ============================================================
# VISUAL BLOCK SETTINGS
# ============================================================
# Controlan la apariencia del bloque visual del README.

# VISUAL_BLOCK_TITLE:
#   Título del bloque visual.
#   EJEMPLOS:
#       "Goodreads Shelf"
#       "Reading Shelf"
#       "Book Telemetry"
VISUAL_BLOCK_TITLE = "Goodreads Shelf"

# VISUAL_ALIGN:
#   Alineación del bloque/table en HTML.
#   VALORES RECOMENDADOS:
#       "center"
#       "left"
#       "right"
VISUAL_ALIGN = "center"

# VISUAL_COLUMNS:
#   Cantidad de columnas de portadas por fila.
#   EJEMPLOS:
#       4
#       5
#       6
#   RECOMENDADO:
#       5 para README.
VISUAL_COLUMNS = 5

# VISUAL_COVER_WIDTH:
#   Ancho de cada portada en píxeles.
#   EJEMPLOS:
#       72
#       88
#       96
#       110
#   RECOMENDADO:
#       88 para algo moderado y limpio.
VISUAL_COVER_WIDTH = 88

# VISUAL_SHOW_CAPTION:
#   Si True, pone texto debajo de la portada.
#   Si False, muestra solo portadas.
VISUAL_SHOW_CAPTION = True

# VISUAL_CAPTION_SHOW_TITLE:
#   Si True, el caption puede incluir el título.
VISUAL_CAPTION_SHOW_TITLE = True

# VISUAL_CAPTION_SHOW_AUTHOR:
#   Si True, el caption puede incluir el autor.
#   Si activas esto junto con el título, el caption puede quedar
#   más cargado visualmente.
VISUAL_CAPTION_SHOW_AUTHOR = False

# VISUAL_CAPTION_MAX_TITLE_LENGTH:
#   Límite de caracteres para el título en el caption.
#   Si se pasa, se corta con "…"
VISUAL_CAPTION_MAX_TITLE_LENGTH = 42

# VISUAL_CAPTION_MAX_AUTHOR_LENGTH:
#   Límite de caracteres para el autor en el caption.
VISUAL_CAPTION_MAX_AUTHOR_LENGTH = 32

# VISUAL_INSERT_BLANK_LINE_AFTER_TITLE:
#   Si True, inserta una línea en blanco después del título del bloque.
#   Útil si quieres respirar más el README.
VISUAL_INSERT_BLANK_LINE_AFTER_TITLE = False


# ============================================================
# CLI BLOCK SETTINGS
# ============================================================
# Configuran el bloque estilo telemetry/CLI dentro del README.

# CLI_BLOCK_TITLE:
#   Título del bloque CLI.
#   EJEMPLOS:
#       "Goodreads Telemetry"
#       "ReadingOps"
#       "Shelf Telemetry"
CLI_BLOCK_TITLE = "Goodreads Telemetry"

# CLI_STYLE:
#   Reservado para futuras variantes de estilo.
#   Por ahora se usa como etiqueta conceptual.
#   VALORES SUGERIDOS:
#       "telemetry"
#       "ops"
CLI_STYLE = "telemetry"

# CLI_ALIGN_KEYS:
#   Si True, alinea las keys para que el bloque se vea prolijo.
#   EJEMPLO:
#       shelf        : read
#       books_loaded : 15
#       status       : ok
CLI_ALIGN_KEYS = True

# CLI_DIVIDER:
#   Si True, deja una línea en blanco entre el título y los metadatos.
CLI_DIVIDER = True

# CLI_BOOK_KEY_PREFIX:
#   Prefijo usado en las entradas de libros.
#   EJEMPLO:
#       book_01
#       book_02
#   Puedes cambiarlo por:
#       "entry"
#       "item"
#       "read"
CLI_BOOK_KEY_PREFIX = "book"

# CLI_META_KEY_WIDTH:
#   Ancho fijo de las claves alineadas.
#   Solo tiene efecto si CLI_ALIGN_KEYS = True.
CLI_META_KEY_WIDTH = 12

# CLI_BOOK_INDEX_PAD:
#   Cantidad de dígitos para el índice del libro.
#   EJEMPLOS:
#       2 -> book_01, book_02
#       3 -> book_001, book_002
CLI_BOOK_INDEX_PAD = 2


# ============================================================
# FALLBACK / VALIDATION SETTINGS
# ============================================================
# Esto controla el comportamiento defensivo del sistema.
# Es una de las partes más importantes.

# USE_CACHE_FALLBACK:
#   Si Goodreads falla o trae basura:
#   - True  -> usar último snapshot válido
#   - False -> no usar fallback
#   RECOMENDADO:
#       True
USE_CACHE_FALLBACK = True

# PRESERVE_LAST_GOOD_SNAPSHOT:
#   Si True, jamás se pisa el último snapshot válido con basura.
#   RECOMENDADO:
#       True
PRESERVE_LAST_GOOD_SNAPSHOT = True

# STRICT_VALIDATION:
#   Si True, si el nuevo snapshot no pasa validación, se rechaza.
#   RECOMENDADO:
#       True
STRICT_VALIDATION = True

# MIN_VALID_BOOKS:
#   Cantidad mínima de libros válidos para aceptar un snapshot nuevo.
#   EJEMPLOS:
#       1  -> flexible
#       3  -> un poco más estricto
#       5  -> más duro
MIN_VALID_BOOKS = 1

# MAX_DUPLICATE_RATIO:
#   Proporción máxima de duplicados tolerados.
#   Si se supera, el snapshot se considera sospechoso.
#   EJEMPLO:
#       0.60 = 60%
MAX_DUPLICATE_RATIO = 0.60

# ALLOW_EMPTY_COVER:
#   Permite aceptar libros sin portada.
#   RECOMENDADO:
#       True, porque el RSS puede ser inconsistente.
ALLOW_EMPTY_COVER = True

# ALLOW_EMPTY_LINK:
#   Permite aceptar libros sin link.
#   RECOMENDADO:
#       False, salvo que quieras ser mucho más permisivo.
ALLOW_EMPTY_LINK = False

# ALLOW_EMPTY_AUTHOR:
#   Permite aceptar libros sin autor.
#   RECOMENDADO:
#       False si quieres mantener cierta calidad.
ALLOW_EMPTY_AUTHOR = False


# ============================================================
# README MARKERS
# ============================================================
# Bloques delimitadores dentro del README.
# NO cambies estos valores a la ligera a menos que también cambies
# los markers reales dentro de README.md.

# README_MARKER_VISUAL_START / END:
#   Delimitan el bloque visual.
README_MARKER_VISUAL_START = "<!-- GOODREADS:VISUAL_START -->"
README_MARKER_VISUAL_END = "<!-- GOODREADS:VISUAL_END -->"

# README_MARKER_CLI_START / END:
#   Delimitan el bloque CLI.
README_MARKER_CLI_START = "<!-- GOODREADS:CLI_START -->"
README_MARKER_CLI_END = "<!-- GOODREADS:CLI_END -->"


# ============================================================
# JSON OUTPUT / FILE WRITING
# ============================================================
# Configuración del formato de escritura JSON.

# WRITE_FILES_PRETTY:
#   Reservado para futura expansión.
#   La escritura actual ya usa formato legible.
WRITE_FILES_PRETTY = True

# JSON_INDENT:
#   Cantidad de espacios de indentación en JSON.
#   RECOMENDADO:
#       2
JSON_INDENT = 2

# JSON_SORT_KEYS:
#   Si True, ordena alfabéticamente las keys del JSON.
#   Si False, conserva un orden más natural/semántico.
#   RECOMENDADO:
#       False
JSON_SORT_KEYS = False


# ============================================================
# OPTIONAL LABELS / EMPTY STATE TEXT
# ============================================================
# Etiquetas visibles y mensajes para estados vacíos.

# SOURCE_LABEL:
#   Nombre lógico de la fuente. Se muestra si SHOW_SOURCE = True.
SOURCE_LABEL = "goodreads_rss"

# VISUAL_EMPTY_MESSAGE:
#   Mensaje mostrado en el bloque visual cuando no hay snapshot válido.
VISUAL_EMPTY_MESSAGE = "No valid Goodreads snapshot available."

# CLI_EMPTY_MESSAGE:
#   Mensaje mostrado en el bloque CLI cuando no hay snapshot válido.
CLI_EMPTY_MESSAGE = "No valid Goodreads snapshot available."
