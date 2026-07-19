#!/usr/bin/env python3
"""
make_typing_svg.py

A self-hosted alternative to third-party "typing SVG" services (like
readme-typing-svg.demolab.com): no external server, no rate limits, no
broken-image risk. Cycles through LINES forever using native SMIL
<animate> tags -- GitHub renders SMIL inside embedded SVGs, same as the
CSS-keyframe animations used elsewhere in this repo.

Each line types in, holds, erases, then the next line begins; the last
line loops back to the first (SMIL supports chaining an element's
`begin` back to an earlier element's `end`, which is what creates the
infinite loop without any JavaScript).

Edit LINES below, then:
    python scripts/make_typing_svg.py
Output: typing-headline.svg
"""
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "typing-headline.svg")

# --- edit me -------------------------------------------------------------
LINES = [
    "Full-Stack Developer",
    "CS Student @ Higher School of Technology (DUT)",
    "Java . JavaScript . SQL . CSS",
    "Based in Azrou, Morocco",
]
WIDTH = 860
FONT_SIZE = 22
TEXT_COLOR = "#39d353"
CURSOR_CHAR = "▌"
# -------------------------------------------------------------------------

CHAR_W = FONT_SIZE * 0.6          # monospace advance width approximation
CHAR_TYPE_S = 0.09                # seconds per character while typing
CHAR_ERASE_S = 0.045              # seconds per character while erasing
HOLD_S = 1.3                      # pause once fully typed
GAP_S = 0.35                      # pause on the blank line between phrases
HEIGHT = int(FONT_SIZE * 2.4)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    x = 20
    y = HEIGHT // 2 + FONT_SIZE // 3

    clip_defs = []
    text_els = []

    n = len(LINES)
    for i, line in enumerate(LINES):
        display = line + CURSOR_CHAR
        full_w = len(display) * CHAR_W
        type_dur = len(display) * CHAR_TYPE_S
        erase_dur = len(display) * CHAR_ERASE_S

        type_id = f"type{i}"
        erase_id = f"erase{i}"
        prev_erase_id = f"erase{(i - 1) % n}"

        if i == 0:
            # starts immediately, and re-triggers every time the *last* line
            # finishes erasing -- this is what makes the whole sequence loop.
            begin_expr = f"0s; {prev_erase_id}.end+{GAP_S}s"
        else:
            begin_expr = f"{prev_erase_id}.end+{GAP_S}s"

        clip_id = f"clip{i}"
        clip_defs.append(f'''
    <clipPath id="{clip_id}">
      <rect x="{x}" y="{y - FONT_SIZE}" width="0" height="{FONT_SIZE * 1.4:.0f}">
        <animate id="{type_id}" attributeName="width" begin="{begin_expr}"
                 dur="{type_dur:.2f}s" from="0" to="{full_w:.1f}" fill="freeze" />
        <animate id="{erase_id}" attributeName="width" begin="{type_id}.end+{HOLD_S}s"
                 dur="{erase_dur:.2f}s" from="{full_w:.1f}" to="0" fill="freeze" />
      </rect>
    </clipPath>''')

        text_els.append(
            f'<text x="{x}" y="{y}" clip-path="url(#{clip_id})" class="typed">'
            f'{esc(display)}</text>'
        )

    svg = f'''<svg viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Headline">
  <defs>{''.join(clip_defs)}
  </defs>
  <style>
    .bg {{ fill: #0d1117; }}
    .typed {{
      font: 600 {FONT_SIZE}px 'SFMono-Regular', 'Consolas', 'Menlo', monospace;
      fill: {TEXT_COLOR};
      white-space: pre;
    }}
  </style>
  <rect class="bg" x="0" y="0" width="{WIDTH}" height="{HEIGHT}" rx="10" />
  {''.join(text_els)}
</svg>
'''
    return svg


def main():
    svg = build_svg()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH} ({len(LINES)} lines, looping)")


if __name__ == "__main__":
    main()
