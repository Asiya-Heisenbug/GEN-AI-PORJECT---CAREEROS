"""Read-only GitHub repository context for project recommendations."""
import json
import os
import re
from urllib.request import Request, urlopen


def _get_json(url: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "resume-analyzer"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def username_from_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if re.fullmatch(r"[A-Za-z0-9-]+", value):
        return value
    match = re.search(r"github\.com/([A-Za-z0-9-]+)", value, re.I)
    return match.group(1) if match else ""


def fetch_repositories(username: str, limit: int = 20) -> dict:
    username = username_from_url(username)
    if not username:
        raise ValueError("Enter a GitHub username or profile URL.")
    repositories = _get_json(f"https://api.github.com/users/{username}/repos?sort=updated&per_page={limit}")
    projects = []
    for repo in repositories:
        projects.append({
            "name": repo.get("name", ""),
            "description": repo.get("description") or "",
            "language": repo.get("language") or "",
            "topics": repo.get("topics", []),
            "url": repo.get("html_url", ""),
            "stars": repo.get("stargazers_count", 0),
            "updated": repo.get("updated_at", ""),
        })
    return {"username": username, "projects": projects}