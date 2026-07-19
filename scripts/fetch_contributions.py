#!/usr/bin/env python3
"""
fetch_contributions.py

Scrapes the PUBLIC contribution calendar HTML fragment GitHub serves at
    https://github.com/users/<username>/contributions
No auth, no GraphQL API, no personal access token needed.

Writes data/contributions.json:
{
  "username": "...",
  "generated_at": "...Z",
  "total": 123,
  "days": [{"date": "2025-07-13", "count": 1, "level": 1}, ...],
  "stats": {
    "current_streak": 4,
    "longest_streak": 12,
    "best_day": {"date": "2026-04-06", "count": 9},
    "monthly_totals": {"2026-07": 20, ...}
  }
}
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GITHUB_PROFILE_USER", "ERRAFI-IMRANE")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")

HEADERS = {
    # a normal browser UA avoids being treated as a bot / blocked
    "User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot/1.0; +https://github.com)"
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Each day is a <td class="ContributionCalendar-day" data-date="YYYY-MM-DD"
    #   data-level="0-4" id="contribution-day-component-W-D">
    # Each count lives in a sibling <tool-tip for="<same id>">N contribution(s) on ...</tool-tip>
    # (falls back to "No contributions on ..." -> 0)
    tooltip_by_id = {}
    for tip in soup.select("tool-tip[for]"):
        tooltip_by_id[tip.get("for")] = tip.get_text(strip=True)

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        date = td["data-date"]
        level = int(td.get("data-level", 0))
        cell_id = td.get("id", "")
        tip_text = tooltip_by_id.get(cell_id, "")

        count = 0
        m = re.match(r"(\d+)\s+contribution", tip_text)
        if m:
            count = int(m.group(1))
        # "No contributions on ..." -> stays 0

        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    # current streak: walk backwards from the most recent day
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak anywhere in the window
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"], default={"date": None, "count": 0})
    best_day = {"date": best_day["date"], "count": best_day["count"]}

    monthly_totals = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly_totals[month_key] += d["count"]

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": dict(sorted(monthly_totals.items())),
    }


def main():
    try:
        html = fetch_html(URL)
    except requests.RequestException as exc:
        print(f"ERROR fetching {URL}: {exc}", file=sys.stderr)
        sys.exit(1)

    days = parse_days(html)
    if not days:
        print("ERROR: parsed 0 days -- GitHub markup may have changed", file=sys.stderr)
        sys.exit(1)

    stats = compute_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": sum(d["count"] for d in days),
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {OUT_PATH}: {payload['total']} contributions across {len(days)} days")


if __name__ == "__main__":
    main()
