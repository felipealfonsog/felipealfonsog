from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
ICONS_JSON = ROOT / "data" / "icons_links
