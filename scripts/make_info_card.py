#!/usr/bin/env python3
"""
make_info_card.py

Hand-authors a small SVG that looks like `neofetch` output: a title bar,
then colored key/value rows. Each row fades + slides in on a short
stagger so it looks like it's printing next to the ASCII portrait.

Edit the FIELDS list below with your own info -- this is the "story
numbers can't tell" panel, so keep it to things the contribution graph
doesn't already show.

Set STATIC=1 to emit a frozen (non-animating) frame, handy for local
Quick Look previews:
    STATIC=1 python scripts/make_info_card.py
"""
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

WIDTH = 490
LINE_HEIGHT = 26
PAD_TOP = 58
PAD_X = 22

# --- edit me -----------------------------------------------------------
TITLE = "imrane@github"
FIELDS = [
    ("User", "IMRANE ERRAFI  (@ERRAFI-IMRANE)"),
    ("Role", "Full-Stack Developer / CS Student"),
    ("School", "Higher School of Technology (DUT)"),
    ("Location", "Azrou, Morocco"),
    ("Stack", "CSS · JavaScript · HTML · SCSS · Python · Java"),
    ("Repos", "31 public repos · 4 stars"),
    ("LinkedIn", "in/errafi-imrane-bb8a26233"),
    ("Highlights", "GitHub Pro"),
]
# accent colors cycle down the rows, neofetch-style
ACCENTS = ["#39d353", "#58a6ff", "#f778ba", "#e3b341", "#79c0ff", "#ff7b72", "#56d364", "#d2a8ff"]
# -------------------------------------------------------------------------


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    height = PAD_TOP + len(FIELDS) * LINE_HEIGHT + 24

    rows_svg = []
    for i, (key, val) in enumerate(FIELDS):
        y = PAD_TOP + i * LINE_HEIGHT
        accent = ACCENTS[i % len(ACCENTS)]
        delay = i * 0.09
        anim_style = "" if STATIC else (
            f'style="animation-delay:{delay:.2f}s"'
        )
        row_class = "row" if not STATIC else "row row-static"
        rows_svg.append(
            f'<g class="{row_class}" {anim_style}>'
            f'<text x="{PAD_X}" y="{y}" class="key" fill="{accent}">{esc(key)}</text>'
            f'<text x="{PAD_X + 108}" y="{y}" class="val">{esc(val)}</text>'
            f'</g>'
        )

    animation_css = "" if STATIC else '''
    .row { opacity: 0; transform: translateX(-6px); animation: fadeIn 0.4s ease-out forwards; }
    @keyframes fadeIn { to { opacity: 1; transform: translateX(0); } }
    '''

    svg = f'''<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="neofetch-style info card">
  <style>
    .card-bg {{ fill: #0d1117; }}
    .titlebar {{ fill: #161b22; }}
    .dot {{ }}
    .title {{ font: 600 13px 'SFMono-Regular', 'Consolas', 'Menlo', monospace; fill: #8b949e; }}
    .key {{ font: 600 14px 'SFMono-Regular', 'Consolas', 'Menlo', monospace; }}
    .val {{ font: 14px 'SFMono-Regular', 'Consolas', 'Menlo', monospace; fill: #c9d1d9; }}
    {animation_css}
  </style>

  <rect class="card-bg" x="0" y="0" width="{WIDTH}" height="{height}" rx="10" />
  <rect class="titlebar" x="0" y="0" width="{WIDTH}" height="34" rx="10" />
  <rect x="0" y="18" width="{WIDTH}" height="16" fill="#161b22" />
  <circle class="dot" cx="20" cy="17" r="6" fill="#ff5f56" />
  <circle class="dot" cx="40" cy="17" r="6" fill="#ffbd2e" />
  <circle class="dot" cx="60" cy="17" r="6" fill="#27c93f" />
  <text x="{WIDTH / 2}" y="21" text-anchor="middle" class="title">{esc(TITLE)}</text>

  {''.join(rows_svg)}
</svg>
'''
    return svg


def main():
    svg = build_svg()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH} ({'static' if STATIC else 'animated'})")


if __name__ == "__main__":
    main()
