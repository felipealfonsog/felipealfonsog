import urllib.request
import time
from pathlib import Path

ENDPOINT = "https://spotify-github-profile.kittinanx.com/api/view?uid=12133266428&cover_image=true&theme=natemoo-re&show_offline=false&background_color=000000&interchange=false&bar_color=53b14f&bar_color_cover=true"

BLANK = "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/master/images/blank.svg"

README = Path("README.md")

RETRIES = 3
WAIT_SECONDS = 2


# ----------------------------------------------------
# TOGGLE (para simular caída del endpoint)
# Cambia a True si quieres probar el fallback
# ----------------------------------------------------
FORCE_ENDPOINT_DOWN = False
# ----------------------------------------------------


def check_once():
    try:
        req = urllib.request.Request(
            ENDPOINT,
            headers={"User-Agent": "spotify-healthcheck"}
        )

        with urllib.request.urlopen(req, timeout=6) as r:

            if r.status != 200:
                return False

            ctype = r.headers.get("Content-Type", "")
            data = r.read(300).decode("utf-8", "ignore")

            if "svg" not in ctype.lower():
                return False

            if "<svg" not in data:
                return False

            return True

    except Exception:
        return False


def endpoint_alive():

    # Toggle manual
    if FORCE_ENDPOINT_DOWN:
        print("TOGGLE ACTIVE → Simulating endpoint failure")
        return False

    for i in range(RETRIES):

        if check_once():
            return True

        if i < RETRIES - 1:
            time.sleep(WAIT_SECONDS)

    return False


def main():

    text = README.read_text()
    alive = endpoint_alive()

    if alive:

        print("Endpoint OK")

        if BLANK in text:
            print("Restoring live widget")
            text = text.replace(BLANK, ENDPOINT)
            README.write_text(text)

    else:

        print("Endpoint DOWN")

        if ENDPOINT in text:
            print("Switching to blank.svg")
            text = text.replace(ENDPOINT, BLANK)
            README.write_text(text)


if __name__ == "__main__":
    main()
