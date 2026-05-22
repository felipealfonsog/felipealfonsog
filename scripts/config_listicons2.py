# ============================================================
# LIST-ICONS2
# RENDER MODE
# ============================================================
# Valid values:
# - "links_listicons2_svg_gnlz"
# - "links_listicons2_svg_github"
# - "full_image"
# - "none"

RENDER_MODE = "full_image"


# ============================================================
# LIST-ICONS2
# SOURCE HEALTH RULE
# ============================================================
# Exact rule:
# If https://gnlz.cl/svg2.html is down and this is True
# -> render nothing
# -> no visible error in README

FORCE_EMPTY_IF_GNLZ_DOWN = True


# ============================================================
# LIST-ICONS2
# HEALTHCHECK (gnlz.cl)
# ============================================================

HEALTHCHECK_ENABLED = True
HEALTHCHECK_URL = "https://gnlz.cl/svg2.html"
HEALTHCHECK_TIMEOUT = 12
HEALTHCHECK_USER_AGENT = "Mozilla/5.0 (compatible; ListIcons2Probe/1.0)"


# ============================================================
# LIST-ICONS2
# LINKS MODE
# ============================================================

LINKS_JSON_PATH = "data/list-icons2-links.json"

OPEN_LINKS_IN_NEW_TAB = True
DEFAULT_ICON_WIDTH = 40
DEFAULT_ICON_HEIGHT = 40
SKIP_HASH_LINKS = False
LINKS_JOIN_WITH = ""


# ============================================================
# LIST-ICONS2
# FULL IMAGE MODE
# ============================================================

FULL_IMAGE_URL = (
    "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/"
    "refs/heads/master/images/icons2inline-full.png"
)

FULL_IMAGE_LINK = "#"
FULL_IMAGE_OPEN_IN_NEW_TAB = True
FULL_IMAGE_ALT = "List-icons2 inline strip"


# ============================================================
# LIST-ICONS2
# README TARGET
# ============================================================

README_PATH = "README.md"
README_START_MARKER = "<!-- LIST-ICONS2:START -->"
README_END_MARKER = "<!-- LIST-ICONS2:END -->"
