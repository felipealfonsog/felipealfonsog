import urllib.request
import time
from pathlib import Path


PRIMARY_ENDPOINT = (
    "https://spotify-github-profile.kittinanx.com/api/view"
    "?uid=12133266428"
    "&cover_image=true"
    "&theme=natemoo-re"
    "&show_offline=false"
    "&background_color=000000"
    "&interchange=false"
    "&bar_color=53b14f"
    "&bar_color_cover=true"
)

FALLBACK_ENDPOINT = (
    "https://spotify-github-profile.kittinanx.com/api/view"
    "?uid=12133266428"
    "&cover_image=true"
    "&theme=natemoo-re"
    "&show_offline=true"
    "&background_color=121212"
    "&interchange=true"
    "&profanity=true"
    "&hide_remaster=true"
    "&bar_color=53b14f"
    "&bar_color_cover=true"
)

SPOTIFY_PROFILE = "https://open.spotify.com/user/12133266428"

BLANK = (
    "https://raw.githubusercontent.com/"
    "felipealfonsog/felipealfonsog/master/images/blank.svg"
)

README = Path("README.md")

START = "<!-- SPOTIFY-WIDGET-START -->"
END = "<!-- SPOTIFY-WIDGET-END -->"

RETRIES = 3
WAIT_SECONDS = 2


# ----------------------------------------------------
# TOGGLES de prueba
# ----------------------------------------------------
FORCE_PRIMARY_DOWN = False
FORCE_FALLBACK_DOWN = False
# ----------------------------------------------------


BLANK_WIDGET = (
    f'<img src="{BLANK}" width="0" height="0" '
    'style="display:none" alt="">'
)


def live_widget(endpoint):
    return f"[![spotify-live]({endpoint})]({SPOTIFY_PROFILE})"


def check_once(endpoint):
    try:
        # Cache-bust para que el healthcheck no reciba
        # una respuesta cacheada antigua.
        separator = "&" if "?" in endpoint else "?"
        check_url = f"{endpoint}{separator}_healthcheck={int(time.time())}"

        req = urllib.request.Request(
            check_url,
            headers={
                "User-Agent": "spotify-healthcheck",
                "Accept": "image/svg+xml,image/*,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )

        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status != 200:
                return False

            content_type = (
                response.headers.get("Content-Type", "")
                .lower()
            )

            # Leemos suficiente para comprobar que realmente
            # estamos recibiendo un SVG.
            data = response.read(4096)

            if "svg" not in content_type and "image" not in content_type:
                return False

            if b"<svg" not in data.lower():
                return False

            return True

    except Exception as exc:
        print(f"Healthcheck error: {exc}")
        return False


def endpoint_alive(endpoint, name, force_down=False):
    if force_down:
        print(f"{name} TOGGLE ACTIVE -> Simulating endpoint failure")
        return False

    for attempt in range(1, RETRIES + 1):
        print(f"Checking {name} ({attempt}/{RETRIES})...")

        if check_once(endpoint):
            print(f"{name} OK")
            return True

        if attempt < RETRIES:
            time.sleep(WAIT_SECONDS)

    print(f"{name} DOWN")
    return False


def select_endpoint():
    # 1. Intentar endpoint original
    if endpoint_alive(
        PRIMARY_ENDPOINT,
        "PRIMARY",
        FORCE_PRIMARY_DOWN,
    ):
        return PRIMARY_ENDPOINT

    print("PRIMARY unavailable -> trying FALLBACK")

    # 2. Intentar endpoint nuevo
    if endpoint_alive(
        FALLBACK_ENDPOINT,
        "FALLBACK",
        FORCE_FALLBACK_DOWN,
    ):
        return FALLBACK_ENDPOINT

    # 3. Ninguno disponible
    return None


def replace_widget(content, widget):
    if START not in content:
        raise RuntimeError(
            f"START marker not found in {README}"
        )

    if END not in content:
        raise RuntimeError(
            f"END marker not found in {README}"
        )

    start_index = content.index(START) + len(START)
    end_index = content.index(END)

    if end_index <= start_index:
        raise RuntimeError(
            "Spotify widget markers are in the wrong order"
        )

    return (
        content[:start_index]
        + "\n"
        + widget
        + "\n"
        + content[end_index:]
    )


def main():
    text = README.read_text(encoding="utf-8")

    selected_endpoint = select_endpoint()

    if selected_endpoint == PRIMARY_ENDPOINT:
        print("Using PRIMARY Spotify widget")
        widget = live_widget(PRIMARY_ENDPOINT)

    elif selected_endpoint == FALLBACK_ENDPOINT:
        print("Using FALLBACK Spotify widget")
        widget = live_widget(FALLBACK_ENDPOINT)

    else:
        print("PRIMARY and FALLBACK are DOWN")
        print("Using hidden blank widget")
        widget = BLANK_WIDGET

    new_text = replace_widget(text, widget)

    if new_text != text:
        print("Updating README")
        README.write_text(new_text, encoding="utf-8")
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
