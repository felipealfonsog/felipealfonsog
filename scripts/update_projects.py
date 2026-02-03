#!/usr/bin/env python3
import os
import re
import requests

USERNAME = os.getenv("GITHUB_USERNAME", "felipealfonsog")
README_PATH = os.getenv("README_PATH", "README.md")

MAX_RECENT = int(os.getenv("MAX_RECENT", "10"))
MAX_CURATED = int(os.getenv("MAX_CURATED", "25"))
MAX_PRIVATE = int(os.getenv("MAX_PRIVATE", "4"))

USE_PROJECT_PRIORITY = os.getenv("USE_PROJECT_PRIORITY", "false").lower() == "true"

# Optional: PAT with repo scope for private repos
PORTFOLIO_TOKEN = os.getenv("PORTFOLIO_TOKEN", "").strip()

API = "https://api.github.com"

HEADERS_PUBLIC = {
    "Accept": "application/vnd.github+json",
}

HEADERS_AUTH = {
    "Accept": "application/vnd.github+json",
}
if PORTFOLIO_TOKEN:
    HEADERS_AUTH["Authorization"] = f"Bearer {PORTFOLIO_TOKEN}"


def safe_get(url, headers, params=None, timeout=30):
    r = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
    return r


def get_languages(repo):
    url = repo.get("languages_url")
    if not url:
        return ""
    # languages_url is public for public repos; for private repos it needs auth
    headers = HEADERS_AUTH if repo.get("private") and PORTFOLIO_TOKEN else HEADERS_PUBLIC
    r = safe_get(url, headers=headers, timeout=20)
    if r.status_code != 200:
        return ""
    langs = r.json() or {}
    if not langs:
        return ""
    top = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:3]
    return " · ".join(lang for lang, _ in top)


def md_public(repo):
    desc = (repo.get("description") or "No description provided.").replace("\n", " ").strip()
    line = f"- [{repo['name']}]({repo['html_url']}): {desc}"
    langs = get_languages(repo)
    if langs:
        line += f"\n  🧬 {langs}"
    return line


def md_private(repo):
    desc = (repo.get("description") or "Private project.").replace("\n", " ").strip()
    line = f"- **{repo['name']}**: {desc}"
    langs = get_languages(repo)
    if langs:
        line += f"\n  🧬 {langs}"
    return line


def priority_score(repo):
    score = 0
    if repo.get("description"):
        score += 3
    # heuristic: more languages usually indicates "real project"
    langs = get_languages(repo)
    if langs:
        score += 2 + min(3, len(langs.split(" · ")))
    if repo.get("updated_at"):
        score += 1
    return score


def fetch_public_repos():
    repos = []
    page = 1
    while True:
        r = safe_get(
            f"{API}/users/{USERNAME}/repos",
            headers=HEADERS_PUBLIC,
            params={"per_page": 100, "page": page, "sort": "updated", "direction": "desc"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Failed to fetch public repos: HTTP {r.status_code} - {r.text[:200]}")
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def fetch_private_repos():
    if not PORTFOLIO_TOKEN:
        return []

    repos = []
    page = 1
    while True:
        r = safe_get(
            f"{API}/user/repos",
            headers=HEADERS_AUTH,
            params={
                "per_page": 100,
                "page": page,
                "visibility": "private",
                "sort": "updated",
                "direction": "desc",
            },
        )
        # If token lacks scope or is invalid, do NOT fail the whole workflow
        if r.status_code == 403 or r.status_code == 401:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Failed to fetch private repos: HTTP {r.status_code} - {r.text[:200]}")

        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def build_block(pinned, recent, curated, private):
    out = []
    out.append("<details>")
    out.append('<summary id="projects">🔍 📁 <strong>Dive into More Featured and Diverse Projects</strong> 🚀✨</summary>')
    out.append("<br>\n")

    out.append("### ⭐ Featured (Pinned)")
    for r in pinned:
        out.append(md_public(r))
    out.append("")

    out.append("### 🕒 Recently Active Projects")
    for r in recent:
        out.append(md_public(r))
    out.append("")

    out.append("### 🧠 Curated Project Collection")
    for r in curated:
        out.append(md_public(r))
    out.append("")

    if private:
        out.append("### 🔒 Selected Private Projects")
        for r in private:
            out.append(md_private(r))
        out.append("")

    out.append("<br>")
    out.append("</details>")
    return "\n".join(out)


def main():
    public = [
        r for r in fetch_public_repos()
        if not r.get("fork") and not r.get("archived")
    ]

    private = [
        r for r in fetch_private_repos()
        if r.get("private") and not r.get("fork") and not r.get("archived") and r.get("description")
    ]

    # Approximate pinned: top by stars then updated.
    pinned = sorted(public, key=lambda x: (x.get("stargazers_count", 0), x.get("updated_at", "")), reverse=True)[:6]
    pinned_names = {r["name"] for r in pinned}

    rest = [r for r in public if r["name"] not in pinned_names]

    if USE_PROJECT_PRIORITY:
        rest.sort(key=priority_score, reverse=True)
        private.sort(key=priority_score, reverse=True)
    else:
        rest.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        private.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    recent = rest[:MAX_RECENT]
    curated = rest[MAX_RECENT:MAX_RECENT + MAX_CURATED]
    private = private[:MAX_PRIVATE]

    block = build_block(pinned, recent, curated, private)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- PROJECTS:START -->(.*?)<!-- PROJECTS:END -->"
    if not re.search(pattern, content, flags=re.S):
        raise RuntimeError("Markers not found. Add <!-- PROJECTS:START --> and <!-- PROJECTS:END --> to README.md")

    updated = re.sub(
        pattern,
        f"<!-- PROJECTS:START -->\n{block}\n<!-- PROJECTS:END -->",
        content,
        flags=re.S,
    )

    if updated != content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
