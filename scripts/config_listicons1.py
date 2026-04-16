# ============================================================
# LIST-ICONS1 CONFIG
# ============================================================

# External source to probe
SOURCE_URL = "https://gnlz.cl/svg1.html"

# Final single image fallback / display image
FULL_IMAGE_URL = (
    "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/"
    "refs/heads/master/images/icons1inline-full.png"
)

# ============================================================
# DISPLAY MODES
# ============================================================
# Valid values:
# - "none"
# - "links"
# - "full_image"

# Primary mode when everything is OK
PRIMARY_MODE = "full_image"

# Fallback mode when SOURCE_URL is down and fallback is enabled
FALLBACK_MODE = "none"

# If True, checks SOURCE_URL before deciding what to render
CHECK_SOURCE_HEALTH = True

# If True and source is down, use FALLBACK_MODE
USE_FALLBACK_WHEN_SOURCE_DOWN = True

# If False, ignore source health completely and always use PRIMARY_MODE
# (this works together with CHECK_SOURCE_HEALTH; if CHECK_SOURCE_HEALTH=False,
# source health is ignored anyway)
# Kept here for readability / future tweaks.
IGNORE_SOURCE_HEALTH = False

# ============================================================
# LINKS RENDERING
# ============================================================
OPEN_LINKS_IN_NEW_TAB = True

DEFAULT_ICON_WIDTH = 40
DEFAULT_ICON_HEIGHT = 40

# If True, skips entries whose href is "#" or empty
SKIP_PLACEHOLDER_LINKS = False

# If True, renders links all in one line with no separators
RENDER_COMPACT_INLINE = True

# Optional separator if RENDER_COMPACT_INLINE is False
INLINE_SEPARATOR = "\n"

# ============================================================
# README MARKERS
# ============================================================
README_PATH = "README.md"
README_START_MARKER = "<!-- LIST-ICONS1:START -->"
README_END_MARKER = "<!-- LIST-ICONS1:END -->"

# ============================================================
# DATA PATHS
# ============================================================
LINKS_JSON_PATH = "data/list-icons1-links.json"

# ============================================================
# NETWORK
# ============================================================
REQUEST_TIMEOUT = 12
USER_AGENT = "Mozilla/5.0 (compatible; ListIcons1Probe/1.0)"

# ============================================================
# OUTPUT BEHAVIOR
# ============================================================
# If mode cannot be resolved for any reason, this is used
SAFE_DEFAULT_MODE = "none"
