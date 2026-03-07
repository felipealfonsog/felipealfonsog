import urllib.request
import time
from pathlib import Path

ENDPOINT = "https://spotify-github-profile.kittinanx.com/api/view?uid=12133266428&cover_image=true&theme=natemoo-re&show_offline=false&background_color=000000&interchange=false&bar_color=53b14f&bar_color_cover=true"

BLANK = "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/master/images/blank.svg"

README = Path("README.md")

START = "<!-- SPOTIFY-WIDGET-START -->"
END = "<!-- SPOTIFY-WIDGET-END -->"

RETRIES = 3
WAIT_SECONDS = 2

# ----------------------------------------------------
# TOGGLE (para simular caída del endpoint) - True / False
# ----------------------------------------------------
FORCE_ENDPOINT_DOWN = True
# ----------------------------------------------------

LIVE_WIDGET = f"[![spotify-live]({ENDPOINT})](https://open.spotify.com/user/12133266428)"

BLANK_WIDGET = f'<img src="{BLANK}" width="0" height="0">'


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

    if FORCE_ENDPOINT_DOWN:
        print("TOGGLE ACTIVE → Simulating endpoint failure")
        return False

    for i in range(RETRIES):

        if check_once():
            return True

        if i < RETRIES - 1:
            time.sleep(WAIT_SECONDS)

    return False


def replace_widget(content, widget):

    start = content.index(START) + len(START)
    end = content.index(END)

    return content[:start] + "\n" + widget + "\n" + content[end:]


def main():

    text = README.read_text()

    alive = endpoint_alive()

    if alive:
        print("Endpoint OK")
        new_text = replace_widget(text, LIVE_WIDGET)
    else:
        print("Endpoint DOWN")
        new_text = replace_widget(text, BLANK_WIDGET)

    if new_text != text:
        print("Updating README")
        README.write_text(new_text)
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
