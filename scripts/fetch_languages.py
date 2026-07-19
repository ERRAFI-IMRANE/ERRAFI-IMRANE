#!/usr/bin/env python3
"""
fetch_languages.py

Aggregates real language byte-counts across your public, non-fork repos
using GitHub's public REST API. No personal token required to run this
locally (60 req/hr per IP) -- but if a GITHUB_TOKEN env var is present
(GitHub Actions sets this automatically), it's used for a much higher
rate limit (5,000 req/hr), which is what the daily workflow relies on.

Writes data/languages.json:
{
  "username": "...",
  "generated_at": "...Z",
  "totals": {"Java": 82345, "JavaScript": 51200, ...},
  "top": [{"name": "Java", "bytes": 82345, "pct": 41.2}, ...]
}
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

USERNAME = os.environ.get("GITHUB_PROFILE_USER", "ERRAFI-IMRANE")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "languages.json")
TOP_N = 6

HEADERS = {
    "User-Agent": "profile-readme-bot/1.0",
    "Accept": "application/vnd.github+json",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def api_get(url, params=None):
    resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        print("ERROR: GitHub API rate limit hit. Set GITHUB_TOKEN for a higher limit.", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def list_own_repos(username):
    repos, page = [], 1
    while True:
        batch = api_get(
            f"https://api.github.com/users/{username}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        if not batch:
            break
        repos.extend(r for r in batch if not r["fork"])
        page += 1
        if len(batch) < 100:
            break
    return repos


def main():
    repos = list_own_repos(USERNAME)
    totals = {}

    for i, repo in enumerate(repos):
        langs = api_get(repo["languages_url"])
        for name, byte_count in langs.items():
            totals[name] = totals.get(name, 0) + byte_count
        # be polite to the unauthenticated rate limit
        if not TOKEN:
            time.sleep(0.15)

    total_bytes = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = [
        {"name": name, "bytes": b, "pct": round(b / total_bytes * 100, 1)}
        for name, b in ranked[:TOP_N]
    ]

    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo_count": len(repos),
        "totals": totals,
        "top": top,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {OUT_PATH}: {len(repos)} repos, top language {top[0]['name'] if top else 'n/a'}")


if __name__ == "__main__":
    main()
