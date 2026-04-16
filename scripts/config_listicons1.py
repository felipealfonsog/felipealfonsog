# ============================================================
# LIST-ICONS1
# RENDER MODE (EXACTO COMO PEDISTE)
# ============================================================
# - "links_listicons1_svg_gnlz"
# - "links_listicons1_svg_github"
# - "full_image"
# - "none"

RENDER_MODE = "full_image"


# ============================================================
# REGLA CRÍTICA
# ============================================================

FORCE_EMPTY_IF_GNLZ_DOWN = True


# ============================================================
# HEALTHCHECK
# ============================================================

HEALTHCHECK_ENABLED = True
HEALTHCHECK_URL = "https://gnlz.cl/svg1.html"
HEALTHCHECK_TIMEOUT = 12
HEALTHCHECK_USER_AGENT = "Mozilla/5.0 (compatible; ListIcons1Probe/1.0)"


# ============================================================
# LINKS MODE
# ============================================================

LINKS_JSON_PATH = "data/list-icons1-links.json"

OPEN_LINKS_IN_NEW_TAB = True
DEFAULT_ICON_WIDTH = 40
DEFAULT_ICON_HEIGHT = 40
SKIP_HASH_LINKS = False
LINKS_JOIN_WITH = ""


# ============================================================
# FULL IMAGE MODE
# ============================================================

FULL_IMAGE_URL = "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/refs/heads/master/images/icons1inline-full.png"

FULL_IMAGE_LINK = "#"
FULL_IMAGE_OPEN_IN_NEW_TAB = True
FULL_IMAGE_ALT = "List-icons1 inline strip"


# ============================================================
# README
# ============================================================

README_PATH = "README.md"
README_START_MARKER = "<!-- LIST-ICONS1:START -->"
README_END_MARKER = "<!-- LIST-ICONS1:END -->"
