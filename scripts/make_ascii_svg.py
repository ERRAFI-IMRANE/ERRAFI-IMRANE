#!/usr/bin/env python3
"""
make_ascii_svg.py

Downsamples source-prepped.png (from prep_photo.py) to a character grid
and maps each cell's brightness to a glyph from a density ramp -- sparse
characters for bright areas, dense ones for dark. Monochrome, high
contrast on purpose: color-per-character and low contrast are what make
most ASCII portraits look like static.

Each row is wrapped in a clip-path that wipes left-to-right (a small
block "cursor" rides the wipe edge), staggered top to bottom, so the
portrait looks like it's printing itself in. It prints once and freezes
-- no looping. Because the motion is CSS keyframes inside the SVG,
GitHub renders it.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png]
Output:
    avi-ascii.svg  ->  renamed here to portrait-ascii.svg
"""
import os
import sys

from PIL import Image

# bright (sparse) -> dark (dense); leading space clears the background to nothing
RAMP = " .`:-=+*cs#%@"

COLS = 100
ROWS = 53
CHAR_W = 6.2   # px, monospace advance width at the chosen font-size
CHAR_H = 11    # px, line height
FONT_SIZE = 11

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "portrait-ascii.svg")


def load_and_downsample(path: str):
    img = Image.open(path).convert("L")  # grayscale
    # character cells are taller than wide, so undersample rows vs a square grid
    small = img.resize((COLS, ROWS), Image.LANCZOS)
    return small


def pixel_to_glyph(value: int) -> str:
    # value: 0 (black) .. 255 (white) -> ramp index: 0 (bright/space) .. len-1 (dark)
    idx = int((255 - value) / 255 * (len(RAMP) - 1))
    return RAMP[idx]


def esc(ch: str) -> str:
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;", " ": "&#160;"}.get(ch, ch)


def build_rows(img: Image.Image):
    px = img.load()
    rows = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            chars.append(pixel_to_glyph(px[x, y]))
        rows.append("".join(chars))
    return rows


def build_svg(rows):
    width = COLS * CHAR_W
    height = ROWS * CHAR_H
    n_rows = len(rows)

    row_svgs = []
    for ri, row_text in enumerate(rows):
        y = (ri + 1) * CHAR_H - 2
        delay = ri * 0.045
        wipe_duration = 0.28
        clip_id = f"clip-row-{ri}"
        text_content = "".join(esc(c) for c in row_text)

        row_svgs.append(f'''
    <clipPath id="{clip_id}">
      <rect class="wipe" x="0" y="{ri * CHAR_H}" width="0" height="{CHAR_H}"
            style="animation-delay:{delay:.3f}s" />
    </clipPath>''')

    text_svgs = []
    for ri, row_text in enumerate(rows):
        y = (ri + 1) * CHAR_H - 2
        clip_id = f"clip-row-{ri}"
        text_content = "".join(esc(c) for c in row_text)
        text_svgs.append(
            f'<text x="0" y="{y}" clip-path="url(#{clip_id})" class="ascii-row">{text_content}</text>'
        )

    total_type_time = n_rows * 0.045 + 0.28

    svg = f'''<svg viewBox="0 0 {width:.0f} {height}" width="{width:.0f}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ASCII portrait">
  <defs>{''.join(row_svgs)}
  </defs>
  <style>
    .bg {{ fill: #0d1117; }}
    .ascii-row {{
      font: {FONT_SIZE}px 'SFMono-Regular', 'Consolas', 'Menlo', monospace;
      fill: #c9d1d9;
      white-space: pre;
    }}
    .wipe {{
      animation: wipe-in 0.28s steps(28, end) forwards;
    }}
    @keyframes wipe-in {{
      from {{ width: 0; }}
      to   {{ width: {width:.0f}px; }}
    }}
  </style>
  <rect class="bg" x="0" y="0" width="{width:.0f}" height="{height}" rx="10" />
  {''.join(text_svgs)}
</svg>
'''
    return svg


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    if not os.path.exists(src):
        print(f"ERROR: {src} not found. Run prep_photo.py first.", file=sys.stderr)
        sys.exit(1)

    img = load_and_downsample(src)
    rows = build_rows(img)
    svg = build_svg(rows)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH} ({COLS}x{ROWS} chars)")


if __name__ == "__main__":
    main()
