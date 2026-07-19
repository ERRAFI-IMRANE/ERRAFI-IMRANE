#!/usr/bin/env python3
"""
render_languages_svg.py

Reads data/languages.json (written by fetch_languages.py) and draws a
single stacked horizontal bar, GitHub-repo-page style, with a legend
row underneath. Segments grow in left-to-right, staggered by rank, then
freeze -- no looping.

Output: languages-bar.svg (repo root)
"""
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "languages.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "languages-bar.svg")

WIDTH = 860
BAR_HEIGHT = 14
TOP_PAD = 18
LEGEND_ROW_H = 22

# GitHub's own linguist colors for common languages; unlisted languages
# fall back to the GRAY palette below, cycled.
LANGUAGE_COLORS = {
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SQL": "#e38c00",
    "PLpgSQL": "#336790",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "PHP": "#4F5D95",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Kotlin": "#A97BFF",
    "Vue": "#41b883",
}
FALLBACK_COLORS = ["#8b949e", "#6e7681", "#57606a"]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def color_for(name, idx):
    return LANGUAGE_COLORS.get(name, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])


def build_svg(payload):
    top = payload["top"]
    height = TOP_PAD + BAR_HEIGHT + 20 + LEGEND_ROW_H * ((len(top) + 2) // 3) + 16

    bar_x = 20
    bar_w = WIDTH - 40

    segments_svg = []
    x_cursor = bar_x
    delay = 0.0
    for i, lang in enumerate(top):
        seg_w = bar_w * (lang["pct"] / 100.0)
        color = color_for(lang["name"], i)
        rx = 4 if i == 0 else 0
        segments_svg.append(
            f'<rect class="seg" x="{x_cursor:.1f}" y="{TOP_PAD}" width="0" height="{BAR_HEIGHT}" '
            f'fill="{color}" style="animation-delay:{delay:.2f}s" data-final-width="{seg_w:.1f}">'
            f'<animate attributeName="width" from="0" to="{seg_w:.1f}" begin="{delay:.2f}s" '
            f'dur="0.5s" fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1" />'
            f'<title>{esc(lang["name"])} - {lang["pct"]}%</title></rect>'
        )
        x_cursor += seg_w
        delay += 0.12

    # legend, wrapped 3 per row
    legend_svg = []
    cols = 3
    col_w = WIDTH // cols
    legend_top = TOP_PAD + BAR_HEIGHT + 26
    for i, lang in enumerate(top):
        col = i % cols
        row = i // cols
        lx = bar_x + col * col_w
        ly = legend_top + row * LEGEND_ROW_H
        color = color_for(lang["name"], i)
        d = 0.5 + i * 0.08
        legend_svg.append(
            f'<g class="legend-item" style="animation-delay:{d:.2f}s">'
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}" />'
            f'<text x="{lx + 16}" y="{ly}" class="legend-text">{esc(lang["name"])} '
            f'<tspan fill="#8b949e">{lang["pct"]}%</tspan></text>'
            f'</g>'
        )

    svg = f'''<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Top languages across public repos">
  <style>
    .bg {{ fill: #0d1117; }}
    .heading {{ font: 600 13px 'Segoe UI', Helvetica, Arial, sans-serif; fill: #8b949e; }}
    .legend-text {{ font: 13px 'Segoe UI', Helvetica, Arial, sans-serif; fill: #c9d1d9; }}
    .legend-item {{ opacity: 0; animation: fadeIn 0.4s ease-out forwards; }}
    @keyframes fadeIn {{ to {{ opacity: 1; }} }}
  </style>
  <rect class="bg" x="0" y="0" width="{WIDTH}" height="{height}" rx="10" />
  <rect x="{bar_x}" y="{TOP_PAD}" width="{bar_w}" height="{BAR_HEIGHT}" rx="4" fill="#161b22" />
  {''.join(segments_svg)}
  {''.join(legend_svg)}
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
