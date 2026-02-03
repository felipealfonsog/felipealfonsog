#!/usr/bin/env python3
import os
import re
import requests

# ---------------- CONFIG ----------------

USERNAME = os.getenv("GITHUB_USERNAME", "felipealfonsog")
README_PATH = os.getenv("README_PATH", "README.md")

MAX_RECENT = int(os.getenv("MAX_RECENT", "10"))
MAX_CURATED = int(os.getenv("MAX_CURATED", "25"))
MAX_PRIVATE = int(os.getenv("MAX_PRIVATE", "4"))

USE_PROJECT_PRIORITY = os.getenv("USE_PROJECT_PRIORITY", "false").lower() == "true"

TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise SystemExit("GITHUB_TOKEN is required")

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

# ---------------- HELPERS ----------------

def get_languages(repo):
    r = requests.get(repo["languages_url"], headers=HEADERS, timeout=20)
    r.raise_for_status()
    langs = r.json()
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
    """
    Heuristic score for 'project importance'
    Used only when USE_PROJECT_PRIORITY = true
    """
    score = 0
    if repo.get("description"):
        score += 3
    if repo.get("languages_url"):
        score += 2
    if repo.get("updated_at"):
        score += 1
    return score


# ---------------- DATA ----------------

def fetch_all_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"{API}/user/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_pinned():
    r = requests.get(
        f"{API}/users/{USERNAME}/repos",
        headers=HEADERS,
        params={"per_page": 100, "sort": "pushed"},
        timeout=30,
    )
    r.raise_for_status()
    # GitHub REST does not expose pinned directly;
    # pinned repos will already be in profile highlights,
    # so we infer pinned manually by stars + activity
    repos = [x for x in r.json() if not x["private"] and not x["fork"] and not x["archived"]]
    repos.sort(key=lambda x: (x["stargazers_count"], x["updated_at"]), reverse=True)
    return repos[:6]


# ---------------- BUILD BLOCK ----------------

def build_block(pinned, recent, curated, private):
    out = []
    out.append("<details>")
    out.append(
        '<summary id="projects">🔍 📁 <strong>Dive into More Featured and Diverse Projects</strong> 🚀✨</summary>\n<br>\n'
    )

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

    out.append("<br>\n</details>")
    return "\n".join(out)


# ---------------- MAIN ----------------

def main():
    all_repos = fetch_all_repos()

    public = [
        r for r in all_repos
        if not r["private"] and not r["fork"] and not r["archived"]
    ]

    private = [
        r for r in all_repos
        if r["private"] and not r["fork"] and not r["archived"] and r.get("description")
    ]

    if USE_PROJECT_PRIORITY:
        public.sort(key=priority_score, reverse=True)
        private.sort(key=priority_score, reverse=True)
    else:
        public.sort(key=lambda x: x["updated_at"], reverse=True)
        private.sort(key=lambda x: x["updated_at"], reverse=True)

    pinned = fetch_pinned()
    pinned_names = {r["name"] for r in pinned}

    public_rest = [r for r in public if r["name"] not in pinned_names]

    recent = public_rest[:MAX_RECENT]
    curated = public_rest[MAX_RECENT:MAX_RECENT + MAX_CURATED]
    private = private[:MAX_PRIVATE]

    block = build_block(pinned, recent, curated, private)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    updated = re.sub(
        r"<!-- PROJECTS:START -->(.*?)<!-- PROJECTS:END -->",
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
