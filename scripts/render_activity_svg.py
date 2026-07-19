#!/usr/bin/env python3
"""
render_activity_svg.py

Reads data/activity.json and draws it as a small `$ git log --oneline`
style terminal feed. Lines fade + slide in top to bottom, staggered,
then freeze -- no looping.

Output: recent-activity.svg (repo root)
"""
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "activity.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "recent-activity.svg")

WIDTH = 860
LINE_HEIGHT = 24
TOP_PAD = 42
BOTTOM_PAD = 16


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(payload):
    items = payload["items"]
    height = TOP_PAD + len(items) * LINE_HEIGHT + BOTTOM_PAD

    rows_svg = []
    for i, item in enumerate(items):
        y = TOP_PAD + i * LINE_HEIGHT
        delay = i * 0.12
        date = f"  <tspan fill=\"#484f58\">{esc(item['date'])}</tspan>" if item["date"] else ""
        rows_svg.append(
            f'<g class="row" style="animation-delay:{delay:.2f}s">'
            f'<text x="20" y="{y}" class="line">'
            f'<tspan fill="#39d353">$</tspan> {esc(item["text"])}{date}'
            f'</text></g>'
        )

    svg = f'''<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Recent public GitHub activity">
  <style>
    .bg {{ fill: #0d1117; }}
    .prompt {{ font: 600 13px 'SFMono-Regular', 'Consolas', 'Menlo', monospace; fill: #8b949e; }}
    .line {{ font: 13px 'SFMono-Regular', 'Consolas', 'Menlo', monospace; fill: #c9d1d9; }}
    .row {{ opacity: 0; transform: translateY(-4px); animation: slideIn 0.35s ease-out forwards; }}
    @keyframes slideIn {{ to {{ opacity: 1; transform: translateY(0); }} }}
  </style>
  <rect class="bg" x="0" y="0" width="{WIDTH}" height="{height}" rx="10" />
  <text x="20" y="24" class="prompt">imrane@github ~ $ git log --oneline -{len(items)}</text>
  {''.join(rows_svg)}
</svg>
'''
    return svg


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    svg = build_svg(payload)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
