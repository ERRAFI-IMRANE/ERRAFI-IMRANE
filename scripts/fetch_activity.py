#!/usr/bin/env python3
"""
fetch_activity.py

Pulls your recent PUBLIC events from GitHub's REST API (no token needed
locally; GitHub Actions' auto-provided GITHUB_TOKEN is used automatically
when present, for a much higher rate limit) and turns them into a short,
human-readable activity feed -- the "what I've been doing lately" that a
static contribution graph can't show.

Writes data/activity.json:
{
  "username": "...",
  "generated_at": "...Z",
  "items": [{"text": "Pushed 3 commits to Java-TP1", "date": "2026-07-18"}, ...]
}
"""
import json
import os
from datetime import datetime, timezone

import requests

USERNAME = os.environ.get("GITHUB_PROFILE_USER", "ERRAFI-IMRANE")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "activity.json")
MAX_ITEMS = 5

HEADERS = {
    "User-Agent": "profile-readme-bot/1.0",
    "Accept": "application/vnd.github+json",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def describe(event: dict) -> str | None:
    etype = event["type"]
    repo = event["repo"]["name"].split("/")[-1]
    payload = event.get("payload", {})

    if etype == "PushEvent":
        n = len(payload.get("commits", [])) or payload.get("size", 1)
        return f"Pushed {n} commit{'s' if n != 1 else ''} to {repo}"
    if etype == "CreateEvent":
        ref_type = payload.get("ref_type")
        if ref_type == "repository":
            return f"Created repository {repo}"
        if ref_type == "branch":
            return f"Created branch {payload.get('ref')} in {repo}"
        return None
    if etype == "PullRequestEvent":
        action = payload.get("action")
        if action in ("opened", "closed", "merged", "reopened"):
            return f"{action.capitalize()} a pull request in {repo}"
        return None
    if etype == "IssuesEvent":
        action = payload.get("action")
        if action in ("opened", "closed", "reopened"):
            return f"{action.capitalize()} an issue in {repo}"
        return None
    if etype == "WatchEvent":
        return f"Starred {event['repo']['name']}"
    if etype == "ForkEvent":
        return f"Forked {repo}"
    if etype == "PublicEvent":
        return f"Made {repo} public"
    if etype == "ReleaseEvent":
        return f"Published a release in {repo}"
    return None


def main():
    resp = requests.get(
        f"https://api.github.com/users/{USERNAME}/events/public",
        headers=HEADERS,
        params={"per_page": 30},
        timeout=20,
    )
    resp.raise_for_status()
    events = resp.json()

    items = []
    for event in events:
        text = describe(event)
        if not text:
            continue
        date = event["created_at"][:10]
        items.append({"text": text, "date": date})
        if len(items) >= MAX_ITEMS:
            break

    if not items:
        items = [{"text": "No recent public activity", "date": ""}]

    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": items,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {OUT_PATH}: {len(items)} items")


if __name__ == "__main__":
    main()
