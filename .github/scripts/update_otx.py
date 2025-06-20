import requests
import datetime
import os

API_KEY = os.getenv("OTX_API_KEY")
HEADERS = {"X-OTX-API-KEY": API_KEY}
OTX_PULSES_URL = "https://otx.alienvault.com/api/v1/pulses/subscribed"

def fetch_latest_pulse():
    response = requests.get(OTX_PULSES_URL, headers=HEADERS)
    data = response.json()
    latest = data["results"][0]
    return {
        "name": latest["name"],
        "indicator": latest["indicators"][0]["indicator"],
        "type": latest["indicators"][0]["type"],
        "url": f"https://otx.alienvault.com/pulse/{latest['id']}"
    }

def update_readme(pulse):
    with open("README.md", "r", encoding="utf-8") as file:
        content = file.read()

    new_block = f"""\
**Threat Type**: {pulse['type'].title()}  
**Indicator**: {pulse['indicator']}  
**Pulse**: {pulse['name']}  
**Link**: [View on OTX]({pulse['url']})

_Last updated: {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}_
"""

    start_tag = "<!-- OTX-START -->"
    end_tag = "<!-- OTX-END -->"
    updated = f"{start_tag}\n{new_block}\n{end_tag}"
    final_content = content.split(start_tag)[0] + updated + content.split(end_tag)[-1]

    with open("README.md", "w", encoding="utf-8") as file:
        file.write(final_content)

if __name__ == "__main__":
    pulse = fetch_latest_pulse()
    update_readme(pulse)

