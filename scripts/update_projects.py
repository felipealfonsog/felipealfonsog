#!/usr/bin/env python3
import os
import re
import requests

USERNAME = os.getenv("GITHUB_USERNAME", "felipealfonsog")
README_PATH = os.getenv("README_PATH", "README.md")

TOPIC = os.getenv("FILTER_TOPIC", "project").strip()
MAX_TOPIC_REPOS = int(os.getenv("MAX_TOPIC_REPOS", "60"))
INCLUDE_ARCHIVED = os.getenv("INCLUDE_ARCHIVED", "false").lower() == "true"
INCLUDE_FORKS = os.getenv("INCLUDE_FORKS", "false").lower() == "true"

TOKEN = os.getenv("GITHUB_TOKEN", "")
if not TOKEN:
    raise SystemExit("Missing GITHUB_TOKEN (Actions provides secrets.GITHUB_TOKEN by default).")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

GRAPHQL_URL = "https://api.github.com/graphql"

DETAILS_SUMMARY = (
    '<details>\n'
    '<summary id="projects">🔍 :file_folder: <strong>Dive into More Featured and Diverse Projects</strong> :rocket::star2:...</summary>\n'
    "<br>\n\n"
)

DETAILS_FOOTER = "\n<br>\n</details>"

def gql(query: str, variables: dict):
    r = requests.post(
        GRAPHQL_URL,
        headers={**HEADERS, "Accept": "application/vnd.github+json"},
        json={"query": query, "variables": variables},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]

def fetch_pinned():
    query = """
    query($login: String!) {
      user(login: $login) {
        pinnedItems(first: 6, types: [REPOSITORY]) {
          nodes {
            ... on Repository {
              name
              url
              description
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
    nodes = data["user"]["pinnedItems"]["nodes"] or []
    repos = []
    for n in nodes:
        if not n:
            continue
        if n.get("isPrivate"):
            continue
        if not INCLUDE_FORKS and n.get("isFork"):
            continue
        if not INCLUDE_ARCHIVED and n.get("isArchived"):
            continue
        repos.append(n)
    return repos

def fetch_topic_projects(exclude_names: set):
    query = """
    query($q: String!, $first: Int!, $after: String) {
      search(query: $q, type: REPOSITORY, first: $first, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          ... on Repository {
            name
            url
            description
            isPrivate
            isFork
            isArchived
            updatedAt
            owner { login }
          }
        }
      }
    }
    """

    # Orden: GitHub search suele priorizar relevancia; nosotros ordenamos por updatedAt en Python.
    q = f"user:{USERNAME} topic:{TOPIC} is:public"
    if not INCLUDE_FORKS:
        q += " fork:false"
    if not INCLUDE_ARCHIVED:
        q += " archived:false"

    repos = []
    after = None
    page_size = 50

    while len(repos) < MAX_TOPIC_REPOS:
        data = gql(query, {"q": q, "first": page_size, "after": after})
        search = data["search"]
        nodes = search["nodes"] or []
        for n in nodes:
            if not n:
                continue
            if n.get("isPrivate"):
                continue
            if n.get("owner", {}).get("login") != USERNAME:
                continue
            name = n.get("name")
            if name in exclude_names:
                continue
            repos.append(n)
            if len(repos) >= MAX_TOPIC_REPOS:
                break

        if not search["pageInfo"]["hasNextPage"]:
            break
        after = search["pageInfo"]["endCursor"]

    repos.sort(key=lambda x: x.get("updatedAt") or "", reverse=True)
    return repos

def md_line(name, url, desc):
    desc = (desc or "").strip().replace("\n", " ").replace("\r", " ")
    if not desc:
        desc = "No description provided yet."
    return f"  - [{name}]({url}): {desc}"

def build_block(pinned, projects):
    lines = []
    lines.append(DETAILS_SUMMARY)

    if pinned:
        lines.append("### ⭐ Featured (Pinned)")
        for r in pinned:
            lines.append(md_line(r["name"], r["url"], r.get("description")))
        lines.append("")

    lines.append(f"### 📦 More Projects (topic: {TOPIC})")
    if projects:
        for r in projects:
            lines.append(md_line(r["name"], r["url"], r.get("description")))
    else:
        lines.append("  - (No repositories found with this topic yet.)")

    lines.append(DETAILS_FOOTER)
    return "\n".join(lines)

def replace_in_readme(text, new_block):
    pattern = r"<!-- PROJECTS:START -->(.*?)<!-- PROJECTS:END -->"
    if not re.search(pattern, text, flags=re.DOTALL):
        raise RuntimeError("Markers not found. Add <!-- PROJECTS:START --> and <!-- PROJECTS:END --> to README.md")
    replacement = f"<!-- PROJECTS:START -->\n{new_block}\n<!-- PROJECTS:END -->"
    return re.sub(pattern, replacement, text, flags=re.DOTALL)

def main():
    pinned = fetch_pinned()
    pinned_names = {r["name"] for r in pinned}

    projects = fetch_topic_projects(exclude_names=pinned_names)

    new_block = build_block(pinned, projects)

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    updated = replace_in_readme(readme, new_block)

    if updated != readme:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README updated.")
    else:
        print("No changes.")

if __name__ == "__main__":
    main()
