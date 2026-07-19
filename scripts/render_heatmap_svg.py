#!/usr/bin/env python3
"""
render_heatmap_svg.py

Reads data/contributions.json (written by fetch_contributions.py) and
renders it as a 53-week x 7-day calendar of rounded boxes: a GitHub-style
contribution heatmap. Ships as a single self-contained animated SVG --
CSS keyframes reveal it diagonally on load, then freeze (no looping).

Output: contrib-heatmap.svg (repo root)
"""
import json
import os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")

# none -> brightest (level 5 kept as a neon top end for the hottest day)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_PAD = 34          # room for weekday labels
TOP_PAD = 34            # room for month labels
BOTTOM_PAD = 54         # room for legend + stats footer
RIGHT_PAD = 14

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Mon=1..Sun=0 (python weekday: Mon=0)


def bucket_into_weeks(days):
    """Arrange the flat day list into GitHub-style columns (weeks), each 7 rows (Sun..Sat)."""
    weeks = []
    current_week = [None] * 7
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        dow = (dt.weekday() + 1) % 7  # convert Mon=0..Sun=6 -> Sun=0..Sat=6
        if dow == 0 and any(current_week):
            weeks.append(current_week)
            current_week = [None] * 7
        current_week[dow] = d
    weeks.append(current_week)
    return weeks


def month_label_positions(weeks):
    """Return [(week_index, label)] whenever a week's first real day starts a new month."""
    labels = []
    last_month = None
    for wi, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            m = int(day["date"][5:7])
            if m != last_month:
                labels.append((wi, MONTH_NAMES[m - 1]))
                last_month = m
            break
    return labels


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(payload):
    days = payload["days"]
    stats = payload["stats"]
    weeks = bucket_into_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * STEP + RIGHT_PAD
    height = TOP_PAD + 7 * STEP + BOTTOM_PAD
    width = max(width, 860)  # keep in step with the portrait+info-card row width

    cells_svg = []
    delays = []
    idx = 0
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day is None:
                continue
            x = LEFT_PAD + wi * STEP
            y = TOP_PAD + di * STEP
            color = PALETTE[min(day["level"], len(PALETTE) - 1)]
            # diagonal stagger: cells further down-right animate later
            delay = (wi + di) * 0.012
            delays.append(delay)
            title = f"{day['count']} contribution{'s' if day['count'] != 1 else ''} on {day['date']}"
            cells_svg.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" ry="2.5" fill="{color}" '
                f'style="animation-delay:{delay:.3f}s">'
                f'<title>{esc(title)}</title></rect>'
            )
            idx += 1

    month_labels_svg = []
    for wi, label in month_label_positions(weeks):
        x = LEFT_PAD + wi * STEP
        month_labels_svg.append(
            f'<text x="{x}" y="{TOP_PAD - 12}" class="month-label">{label}</text>'
        )

    weekday_labels_svg = []
    for dow, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + dow * STEP + CELL - 1
        weekday_labels_svg.append(
            f'<text x="{LEFT_PAD - 8}" y="{y}" class="weekday-label" text-anchor="end">{label}</text>'
        )

    # legend: Less [boxes] More, bottom-right aligned under the grid
    legend_y = TOP_PAD + 7 * STEP + 26
    legend_x = width - RIGHT_PAD - (len(PALETTE) * (CELL + 4)) - 34
    legend_svg = [f'<text x="{legend_x - 6}" y="{legend_y + CELL - 1}" class="legend-label" text-anchor="end">Less</text>']
    for i, color in enumerate(PALETTE):
        lx = legend_x + i * (CELL + 4)
        legend_svg.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" ry="2.5" fill="{color}" />'
        )
    more_x = legend_x + len(PALETTE) * (CELL + 4) + 6
    legend_svg.append(f'<text x="{more_x}" y="{legend_y + CELL - 1}" class="legend-label">More</text>')

    footer_y = TOP_PAD + 7 * STEP + 48
    total = payload["total"]
    footer_text = (
        f"{total} contribution{'s' if total != 1 else ''} in the last year &#183; "
        f"current streak {stats['current_streak']}d &#183; longest streak {stats['longest_streak']}d"
    )

    max_delay = max(delays) if delays else 0
    reveal_duration = 0.45

    svg = f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="{esc(payload['username'])} GitHub contribution heatmap">
  <style>
    .bg {{ fill: #0d1117; }}
    .month-label {{ font: 12px 'Segoe UI', Helvetica, Arial, sans-serif; fill: #8b949e; }}
    .weekday-label {{ font: 10px 'Segoe UI', Helvetica, Arial, sans-serif; fill: #8b949e; }}
    .legend-label {{ font: 11px 'Segoe UI', Helvetica, Arial, sans-serif; fill: #8b949e; }}
    .footer {{ font: 12px 'Segoe UI', Helvetica, Arial, sans-serif; fill: #c9d1d9; }}
    .cell {{
      opacity: 0;
      transform: translate(-4px, -4px);
      animation: reveal {reveal_duration}s ease-out forwards;
    }}
    @keyframes reveal {{
      from {{ opacity: 0; transform: translate(-4px, -4px); }}
      to   {{ opacity: 1; transform: translate(0, 0); }}
    }}
  </style>

  <rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10" />

  {''.join(month_labels_svg)}
  {''.join(weekday_labels_svg)}
  {''.join(cells_svg)}
  {''.join(legend_svg)}

  <text x="{LEFT_PAD}" y="{footer_y}" class="footer">{footer_text}</text>
</svg>
'''
    return svg


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    svg = build_svg(payload)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
