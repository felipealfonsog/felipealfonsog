#!/usr/bin/env python3
import os
import re
import json
import time
import requests

USERNAME = os.getenv("GITHUB_USERNAME", "felipealfonsog")
README_PATH = os.getenv("README_PATH", "README.md")

MAX_LATEST = int(os.getenv("MAX_LATEST", "8"))
MAX_RECENT = int(os.getenv("MAX_RECENT", "10"))
MAX_POPULAR = int(os.getenv("MAX_POPULAR", "10"))
MAX_CURATED = int(os.getenv("MAX_CURATED", "20"))

USE_PROJECT_PRIORITY = os.getenv("USE_PROJECT_PRIORITY", "false").lower() == "true"
DETAILS_OPEN = os.getenv("DETAILS_OPEN", "true").lower() == "true"

EXCLUSIONS_ENABLED = os.getenv("EXCLUSIONS_ENABLED", "true").lower() == "true"
EXCLUSIONS_FILE = os.getenv("EXCLUSIONS_FILE", "config/exclusions.json")

# Fail-soft behavior: if GitHub API/network errors happen, exit 0 and keep last known good README
FAIL_SOFT = os.getenv("FAIL_SOFT", "true").lower() == "true"

PORTFOLIO_TOKEN = os.getenv("PORTFOLIO_TOKEN", "").strip()
if not PORTFOLIO_TOKEN:
    raise SystemExit("PORTFOLIO_TOKEN is required (GraphQL pinnedItems + API).")

API = "https://api.github.com"
GRAPHQL = f"{API}/graphql"

HEADERS_AUTH = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {PORTFOLIO_TOKEN}",
}

# ----------------- HTTP helpers (retries) -----------------

def http_get(url, params=None, timeout=30, retries=3, backoff=1.2):
    last_exc = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS_AUTH, params=params or {}, timeout=timeout)
            return r
        except requests.exceptions.RequestException as e:
            last_exc = e
            time.sleep(backoff ** i)
    raise last_exc  # type: ignore

def http_post(url, payload, timeout=30, retries=3, backoff=1.2):
    last_exc = None
    for i in range(retries):
        try:
            r = requests.post(url, headers=HEADERS_AUTH, json=payload, timeout=timeout)
            return r
        except requests.exceptions.RequestException as e:
            last_exc = e
            time.sleep(backoff ** i)
    raise last_exc  # type: ignore

# ----------------- exclusions -----------------

def load_exclusions():
    if not EXCLUSIONS_ENABLED:
        return {"enabled": False}

    try:
        with open(EXCLUSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    return {
        "enabled": True,
        "exclude_exact": data.get("exclude_exact", []) or [],
        "exclude_prefixes": data.get("exclude_prefixes", []) or [],
        "exclude_contains": data.get("exclude_contains", []) or [],
        "exclude_regex": data.get("exclude_regex", []) or [],
    }

def is_excluded(repo_name: str, rules: dict) -> bool:
    if not rules.get("enabled", False):
        return False

    if repo_name in set(rules.get("exclude_exact", [])):
        return True

    for p in rules.get("exclude_prefixes", []):
        if repo_name.startswith(p):
            return True

    lower = repo_name.lower()
    for c in rules.get("exclude_contains", []):
        if c.lower() in lower:
            return True

    for rx in rules.get("exclude_regex", []):
        try:
            if re.search(rx, repo_name):
                return True
        except re.error:
            pass

    return False

# ----------------- GitHub API -----------------

def gql(query, variables):
    payload = {"query": query, "variables": variables}
    r = http_post(GRAPHQL, payload, timeout=30, retries=3)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

def dedupe_repos(repos):
    seen = set()
    out = []
    for r in repos:
        key = r.get("full_name") or f"{USERNAME}/{r.get('name')}"
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

def get_languages(repo):
    url = repo.get("languages_url")
    if not url:
        return ""
    r = http_get(url, timeout=20, retries=3)
    if r.status_code != 200:
        return ""
    langs = r.json() or {}
    if not langs:
        return ""
    top = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:3]
    return " · ".join(lang for lang, _ in top)

def format_repo_line(repo):
    desc = (repo.get("description") or "No description provided.").replace("\n", " ").strip()
    name = repo["name"]
    url = repo["html_url"]
    langs = get_languages(repo)
    line = f"- [{name}]({url}): {desc}"
    if langs:
        line += f"\n  🧬 {langs}"
    return line

def priority_score(repo):
    score = 0
    if repo.get("description"):
        score += 3
    score += min(2, repo.get("stargazers_count", 0) // 5)
    score += min(2, repo.get("forks_count", 0) // 5)
    if get_languages(repo):
        score += 2
    if repo.get("updated_at"):
        score += 1
    return score

def fetch_pinned_exact():
    query = """
    query($login: String!) {
      user(login: $login) {
        pinnedItems(first: 6, types: [REPOSITORY]) {
          nodes {
            ... on Repository {
              name
              description
              url
              isPrivate
              isFork
              isArchived
              updatedAt
            }
          }
        }
      }
    }
    """
    data = gql(query, {"login": USERNAME})
    pinned = []
    for n in data["user"]["pinnedItems"]["nodes"] or []:
        if not n:
            continue
        if n["isFork"] or n["isArchived"]:
            continue
        # Never show private pinned repos in a public README
        if n["isPrivate"]:
            continue

        pinned.append({
            "name": n["name"],
            "full_name": f"{USERNAME}/{n['name']}",
            "html_url": n["url"],
            "description": n["description"],
            "private": False,
            "fork": False,
            "archived": False,
            "updated_at": n["updatedAt"],
            "languages_url": f"{API}/repos/{USERNAME}/{n['name']}/languages",
            "stargazers_count": 0,
            "forks_count": 0,
        })
    return pinned

def fetch_all_public_repos_auth():
    # Auth endpoint provides consistent metadata; we still output PUBLIC only.
    repos = []
    page = 1
    while True:
        r = http_get(
            f"{API}/user/repos",
            params={"per_page": 100, "page": page, "sort": "updated", "direction": "desc"},
            timeout=30,
            retries=3,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    repos = dedupe_repos(repos)
    return [r for r in repos if not r.get("private")]

# ----------------- block builder -----------------

def build_block(pinned, latest, recent, popular, curated):
    out = []
    out.append("<details open>" if DETAILS_OPEN else "<details>")
    out.append('<summary id="projects">🔍 📁 <strong>Dive into More Featured and Diverse Projects</strong> 🚀✨</summary>')
    out.append("<br>\n")

    out.append("### ⭐ Featured (Pinned)")
    for r in pinned:
        out.append(format_repo_line(r))
    out.append("")

    out.append("### 🆕 Latest OSS Projects")
    for r in latest:
        out.append(format_repo_line(r))
    out.append("")

    out.append("### 🕒 Recently Active Projects")
    for r in recent:
        out.append(format_repo_line(r))
    out.append("")

    out.append("### 📈 Popular Projects (Stars + Forks)")
    for r in popular:
        out.append(format_repo_line(r))
    out.append("")

    out.append("### 🧠 Curated Project Collection")
    for r in curated:
        out.append(format_repo_line(r))
    out.append("")

    out.append("<br>")
    out.append("</details>")
    return "\n".join(out)

def validate_block(block: str):
    # Guard against accidental empty/invalid output overwriting README
    required_markers = [
        "<details",
        "<summary id=\"projects\">",
        "### ⭐ Featured (Pinned)",
        "### 🆕 Latest OSS Projects",
        "### 🕒 Recently Active Projects",
        "### 📈 Popular Projects (Stars + Forks)",
        "### 🧠 Curated Project Collection",
        "</details>",
    ]
    for m in required_markers:
        if m not in block:
            raise RuntimeError(f"Generated block failed validation (missing: {m}).")

    # Very small blocks are suspicious
    if len(block) < 500:
        raise RuntimeError("Generated block looks too small; refusing to overwrite README.")

# ----------------- main -----------------

def main():
    rules = load_exclusions()

    pinned = fetch_pinned_exact()
    pinned_names = {r["full_name"] for r in pinned}

    public = [
        r for r in fetch_all_public_repos_auth()
        if not r.get("fork") and not r.get("archived")
    ]

    # Apply JSON exclusions
    public = [r for r in public if not is_excluded(r.get("name", ""), rules)]

    # Exclude pinned from other sections
    public_non_pinned = [r for r in public if r.get("full_name") not in pinned_names]

    # Latest by created_at
    latest_sorted = sorted(public_non_pinned, key=lambda x: x.get("created_at", ""), reverse=True)
    latest = latest_sorted[:MAX_LATEST]
    latest_names = {r.get("full_name") for r in latest}

    # Recently active by updated_at (exclude latest)
    recent_sorted = sorted(public_non_pinned, key=lambda x: x.get("updated_at", ""), reverse=True)
    recent = [r for r in recent_sorted if r.get("full_name") not in latest_names][:MAX_RECENT]
    recent_names = {r.get("full_name") for r in recent}

    # Popular by stars+forks (exclude latest+recent)
    popular_sorted = sorted(
        public_non_pinned,
        key=lambda x: (x.get("stargazers_count", 0) + x.get("forks_count", 0), x.get("updated_at", "")),
        reverse=True
    )
    popular_exclude = latest_names.union(recent_names)
    popular = [r for r in popular_sorted if r.get("full_name") not in popular_exclude][:MAX_POPULAR]
    popular_names = {r.get("full_name") for r in popular}

    # Curated pool = rest (optionally priority)
    curated_exclude = popular_exclude.union(popular_names)
    curated_pool = [r for r in public_non_pinned if r.get("full_name") not in curated_exclude]

    if USE_PROJECT_PRIORITY:
        curated_pool.sort(key=priority_score, reverse=True)
    else:
        curated_pool.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    curated = curated_pool[:MAX_CURATED]

    block = build_block(pinned, latest, recent, popular, curated)
    validate_block(block)

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
    try:
        main()
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
        if FAIL_SOFT:
            # Preserve last known good README by skipping update, and do not fail the workflow
            print(f"Transient GitHub API/network error. Skipping update to preserve last known good state: {e}")
            raise SystemExit(0)
        raise
