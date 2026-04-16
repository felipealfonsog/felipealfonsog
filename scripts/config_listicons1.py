# ============================================================
# LIST-ICONS1
# RENDER MODE (EXACTO COMO PEDISTE)
# ============================================================
# Valid values:
# - "links_listicons1_svg_gnlz"
# - "links_listicons1_svg_github"
# - "full_image"
# - "none"

RENDER_MODE = "links_listicons1_svg_github"


# ============================================================
# LIST-ICONS1
# SOURCE HEALTH RULE
# ============================================================
# Exact rule:
# If https://gnlz.cl/svg1.html is down and this is True
# -> render nothing
# -> no visible error in README

FORCE_EMPTY_IF_GNLZ_DOWN = True


# ============================================================
# LIST-ICONS1
# HEALTHCHECK (gnlz.cl)
# ============================================================

HEALTHCHECK_ENABLED = True
HEALTHCHECK_URL = "https://gnlz.cl/svg1.html"
HEALTHCHECK_TIMEOUT = 12
HEALTHCHECK_USER_AGENT = "Mozilla/5.0 (compatible; ListIcons1Probe/1.0)"


# ============================================================
# LIST-ICONS1
# LINKS MODE
# ============================================================
# JSON editable with all <a><img></a> entries

LINKS_JSON_PATH = "data/list-icons1-links.json"

OPEN_LINKS_IN_NEW_TAB = True
DEFAULT_ICON_WIDTH = 40
DEFAULT_ICON_HEIGHT = 40
SKIP_HASH_LINKS = False
LINKS_JOIN_WITH = ""


# ============================================================
# LIST-ICONS1
# FULL IMAGE MODE
# ============================================================

FULL_IMAGE_URL = (
    "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/"
    "refs/heads/master/images/icons1inline-full.png"
)


# ============================================================
# LIST-ICONS1
# README TARGET
# ============================================================

README_PATH = "README.md"
README_START_MARKER = "<!-- LIST-ICONS1:START -->"
README_END_MARKER = "<!-- LIST-ICONS1:END -->"
