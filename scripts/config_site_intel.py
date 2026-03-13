from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

TARGET_URL = "https://gnlz.cl"
TARGET_HOST = "gnlz.cl"
TARGET_EXPECTED_TEXT = "gnlz.cl"

MODE = "blackbox"  # minimal | ops | intel | full | blackbox

README_PATH = BASE_DIR / "README.md"
CACHE_PATH = BASE_DIR / "data" / "last_probe.json"
ANALYTICS_PATH = BASE_DIR / "data" / "analytics.json"

README_START = "<!-- GNLZ:SITE_INTEL:START -->"
README_END = "<!-- GNLZ:SITE_INTEL:END -->"

CLI_USER = "felipe"
CLI_HOST = "watchops"
CLI_PATH = "~"
CLI_PROMPT_SYMBOL = "$"

SHOW_OPERATOR_LINE = True
OPERATOR_USER = "probe"
OPERATOR_HOST = "watchops"
OPERATOR_PATH = "~"
OPERATOR_PROMPT_SYMBOL = "$"
OPERATOR_CMD = "telemetry-acquire gnlz.cl"

SHOW_BANNER = True
BANNER_TEXT = "GNLZ.CL :: SITE OPERATIONS INTELLIGENCE"

SHOW_LAST_PROBE_UTC = True
SHOW_DATA_STATE = True
SHOW_PROBE_CONFIDENCE = True

SHOW_PROFILE = True
SHOW_TARGET = True
SHOW_STATUS = True
SHOW_HTTP = True
SHOW_LATENCY = True
SHOW_TTFB = True
SHOW_UPTIME = True
SHOW_TLS = True
SHOW_EDGE = True
SHOW_ORIGIN_EXPOSURE = True
SHOW_DNS = True
SHOW_ASN = True
SHOW_HEADERS = True
SHOW_ROBOTS = True
SHOW_SECURITYTXT = True
SHOW_SERVER_HINT = True
SHOW_OS_HINT = True
SHOW_DETECTION_MODEL = True
SHOW_FINGERPRINT_CONFIDENCE = True
SHOW_TRAFFIC = True
SHOW_CACHE_SIGNAL = True
SHOW_CONTENT_LENGTH = True
SHOW_ANOMALY_SIGNAL = True
SHOW_TOR = True
SHOW_ONION = True

SHOW_BLACKBOX_PROTOCOL = True
SHOW_BLACKBOX_TLS_CIPHER = True
SHOW_BLACKBOX_ALPN = True
SHOW_BLACKBOX_TLS_ISSUER = True
SHOW_BLACKBOX_IPV6 = True

TOR_CHECK_ENABLED = True
TOR_PROXY_URL = "socks5h://127.0.0.1:9050"
TOR_TIMEOUT_SECONDS = 35

REQUEST_TIMEOUT_SECONDS = 25
VERIFY_TLS = True
USER_AGENT = "gnlz-site-intel/2.0 (+https://gnlz.cl)"

TLS_STRICT_DAYS_THRESHOLD = 21

HEADER_EXPECTATIONS = {
    "strict-transport-security": True,
    "content-security-policy": True,
    "x-frame-options": True,
    "referrer-policy": True,
    "permissions-policy": True,
}

HEADER_ALIASES = {
    "strict-transport-security": "HSTS",
    "content-security-policy": "CSP",
    "x-frame-options": "XFO",
    "referrer-policy": "REFPOL",
    "permissions-policy": "PERMPOL",
}

MODE_FIELDS = {
    "minimal": {
        "SHOW_PROFILE": False,
        "SHOW_TTFB": False,
        "SHOW_EDGE": False,
        "SHOW_ORIGIN_EXPOSURE": False,
        "SHOW_DNS": False,
        "SHOW_ASN": False,
        "SHOW_HEADERS": False,
        "SHOW_ROBOTS": False,
        "SHOW_SECURITYTXT": False,
        "SHOW_SERVER_HINT": False,
        "SHOW_OS_HINT": False,
        "SHOW_DETECTION_MODEL": False,
        "SHOW_FINGERPRINT_CONFIDENCE": False,
        "SHOW_TRAFFIC": False,
        "SHOW_CACHE_SIGNAL": False,
        "SHOW_CONTENT_LENGTH": False,
        "SHOW_ANOMALY_SIGNAL": False,
        "SHOW_TOR": True,
        "SHOW_ONION": False,
        "SHOW_BLACKBOX_PROTOCOL": False,
        "SHOW_BLACKBOX_TLS_CIPHER": False,
        "SHOW_BLACKBOX_ALPN": False,
        "SHOW_BLACKBOX_TLS_ISSUER": False,
        "SHOW_BLACKBOX_IPV6": False,
    },
    "ops": {
        "SHOW_PROFILE": True,
        "SHOW_HTTP": True,
        "SHOW_LATENCY": True,
        "SHOW_TTFB": True,
        "SHOW_UPTIME": True,
        "SHOW_TLS": True,
        "SHOW_EDGE": False,
        "SHOW_ORIGIN_EXPOSURE": False,
        "SHOW_DNS": False,
        "SHOW_ASN": False,
        "SHOW_HEADERS": False,
        "SHOW_ROBOTS": False,
        "SHOW_SECURITYTXT": False,
        "SHOW_SERVER_HINT": False,
        "SHOW_OS_HINT": False,
        "SHOW_DETECTION_MODEL": False,
        "SHOW_FINGERPRINT_CONFIDENCE": True,
        "SHOW_TRAFFIC": False,
        "SHOW_CACHE_SIGNAL": True,
        "SHOW_CONTENT_LENGTH": True,
        "SHOW_ANOMALY_SIGNAL": False,
        "SHOW_TOR": True,
        "SHOW_ONION": False,
        "SHOW_BLACKBOX_PROTOCOL": False,
        "SHOW_BLACKBOX_TLS_CIPHER": False,
        "SHOW_BLACKBOX_ALPN": False,
        "SHOW_BLACKBOX_TLS_ISSUER": False,
        "SHOW_BLACKBOX_IPV6": False,
    },
    "intel": {
        "SHOW_PROFILE": True,
        "SHOW_HTTP": False,
        "SHOW_LATENCY": False,
        "SHOW_TTFB": False,
        "SHOW_UPTIME": False,
        "SHOW_TLS": False,
        "SHOW_EDGE": True,
        "SHOW_ORIGIN_EXPOSURE": True,
        "SHOW_DNS": True,
        "SHOW_ASN": True,
        "SHOW_HEADERS": True,
        "SHOW_ROBOTS": True,
        "SHOW_SECURITYTXT": True,
        "SHOW_SERVER_HINT": False,
        "SHOW_OS_HINT": False,
        "SHOW_DETECTION_MODEL": False,
        "SHOW_FINGERPRINT_CONFIDENCE": True,
        "SHOW_TRAFFIC": False,
        "SHOW_CACHE_SIGNAL": False,
        "SHOW_CONTENT_LENGTH": False,
        "SHOW_ANOMALY_SIGNAL": True,
        "SHOW_TOR": True,
        "SHOW_ONION": True,
        "SHOW_BLACKBOX_PROTOCOL": False,
        "SHOW_BLACKBOX_TLS_CIPHER": False,
        "SHOW_BLACKBOX_ALPN": False,
        "SHOW_BLACKBOX_TLS_ISSUER": False,
        "SHOW_BLACKBOX_IPV6": False,
    },
    "full": {
        "SHOW_PROFILE": True,
        "SHOW_HTTP": True,
        "SHOW_LATENCY": True,
        "SHOW_TTFB": True,
        "SHOW_UPTIME": True,
        "SHOW_TLS": True,
        "SHOW_EDGE": True,
        "SHOW_ORIGIN_EXPOSURE": True,
        "SHOW_DNS": True,
        "SHOW_ASN": True,
        "SHOW_HEADERS": True,
        "SHOW_ROBOTS": True,
        "SHOW_SECURITYTXT": True,
        "SHOW_SERVER_HINT": True,
        "SHOW_OS_HINT": True,
        "SHOW_DETECTION_MODEL": True,
        "SHOW_FINGERPRINT_CONFIDENCE": True,
        "SHOW_TRAFFIC": True,
        "SHOW_CACHE_SIGNAL": True,
        "SHOW_CONTENT_LENGTH": True,
        "SHOW_ANOMALY_SIGNAL": True,
        "SHOW_TOR": True,
        "SHOW_ONION": True,
        "SHOW_BLACKBOX_PROTOCOL": False,
        "SHOW_BLACKBOX_TLS_CIPHER": False,
        "SHOW_BLACKBOX_ALPN": False,
        "SHOW_BLACKBOX_TLS_ISSUER": False,
        "SHOW_BLACKBOX_IPV6": False,
    },
    "blackbox": {
        "SHOW_PROFILE": True,
        "SHOW_HTTP": True,
        "SHOW_LATENCY": True,
        "SHOW_TTFB": True,
        "SHOW_UPTIME": True,
        "SHOW_TLS": True,
        "SHOW_EDGE": True,
        "SHOW_ORIGIN_EXPOSURE": True,
        "SHOW_DNS": True,
        "SHOW_ASN": True,
        "SHOW_HEADERS": True,
        "SHOW_ROBOTS": True,
        "SHOW_SECURITYTXT": True,
        "SHOW_SERVER_HINT": True,
        "SHOW_OS_HINT": True,
        "SHOW_DETECTION_MODEL": True,
        "SHOW_FINGERPRINT_CONFIDENCE": True,
        "SHOW_TRAFFIC": True,
        "SHOW_CACHE_SIGNAL": True,
        "SHOW_CONTENT_LENGTH": True,
        "SHOW_ANOMALY_SIGNAL": True,
        "SHOW_TOR": True,
        "SHOW_ONION": True,
        "SHOW_BLACKBOX_PROTOCOL": True,
        "SHOW_BLACKBOX_TLS_CIPHER": True,
        "SHOW_BLACKBOX_ALPN": True,
        "SHOW_BLACKBOX_TLS_ISSUER": True,
        "SHOW_BLACKBOX_IPV6": True,
    },
}
