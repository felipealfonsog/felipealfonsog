# ============================================================
# LIST-ICONS3
# RENDER MODE
# ============================================================
# Valid values:
# - "links_listicons3_svg_gnlz"
# - "links_listicons3_svg_github"
# - "full_image"
# - "none"

RENDER_MODE = "full_image"


# ============================================================
# LIST-ICONS3
# SOURCE HEALTH RULE
# ============================================================
# Exact rule:
# If https://gnlz.cl/svg3techicons.html is down and this is True
# -> render nothing
# -> no visible error in README

FORCE_EMPTY_IF_GNLZ_DOWN = True


# ============================================================
# LIST-ICONS3
# HEALTHCHECK (gnlz.cl)
# ============================================================

HEALTHCHECK_ENABLED = True
HEALTHCHECK_URL = "https://gnlz.cl/svg3techicons.html"
HEALTHCHECK_TIMEOUT = 12
HEALTHCHECK_USER_AGENT = "Mozilla/5.0 (compatible; ListIcons3Probe/1.0)"


# ============================================================
# LIST-ICONS3
# LINKS MODE
# ============================================================

LINKS_JSON_PATH = "data/list-icons3-links.json"

OPEN_LINKS_IN_NEW_TAB = True
DEFAULT_ICON_WIDTH = 40
DEFAULT_ICON_HEIGHT = 40
SKIP_HASH_LINKS = False
LINKS_JOIN_WITH = ""


# ============================================================
# LIST-ICONS3
# FULL IMAGE MODE
# ============================================================

FULL_IMAGE_URL = (
    "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/"
    "refs/heads/master/images/icons3inline-tech.png"
)

FULL_IMAGE_LINK = "#"
FULL_IMAGE_OPEN_IN_NEW_TAB = True
FULL_IMAGE_ALT = "List-icons3 inline strip"


# ============================================================
# LIST-ICONS3
# README TARGET
# ============================================================

README_PATH = "README.md"
README_START_MARKER = "<!-- LIST-ICONS3:START -->"
README_END_MARKER = "<!-- LIST-ICONS3:END -->"
