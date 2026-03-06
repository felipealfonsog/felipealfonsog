import urllib.request
import urllib.error
from pathlib import Path

endpoint = "https://spotify-github-profile.kittinanx.com/api/view?uid=12133266428&cover_image=true&theme=natemoo-re&show_offline=false&background_color=000000&interchange=false&bar_color=53b14f&bar_color_cover=true"

readme = Path("README.md")

live_block = "[![spotify-live]"
blank_block = "[![spotify-live](https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/master/images/blank.svg)]"

def endpoint_alive():
    try:
        with urllib.request.urlopen(endpoint, timeout=5) as r:
            if r.status == 200:
                data = r.read(200)
                return b"<svg" in data
    except:
        pass
    return False

def main():
    text = readme.read_text()

    if endpoint_alive():
        print("endpoint OK")
        return

    print("endpoint DOWN → switching to blank")

    new = text.replace(
        endpoint,
        "https://raw.githubusercontent.com/felipealfonsog/felipealfonsog/master/images/blank.svg"
    )

    readme.write_text(new)

if __name__ == "__main__":
    main()
