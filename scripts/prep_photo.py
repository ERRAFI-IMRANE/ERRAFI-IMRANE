#!/usr/bin/env python3
"""
prep_photo.py

Run this ONCE per photo (not part of the daily automation).

A flatly-lit face converts to a dark, unreadable ASCII blob. Three steps fix that:
  1. Remove the background with rembg so only the subject remains.
  2. Boost local contrast with OpenCV CLAHE (contrast-limited adaptive
     histogram equalization) -- this is what gives a flat face real
     highlights and shadows.
  3. Composite onto pure white so the background maps to the blank end
     of the ASCII ramp (white -> space character).

Usage:
    python scripts/prep_photo.py source-photo.jpg
Output:
    source-prepped.png  (grayscale, ready for make_ascii_svg.py)
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def remove_background(input_path: str) -> Image.Image:
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)  # downloads a small model on first run
    return Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")


def composite_on_white(rgba_img: Image.Image) -> Image.Image:
    white_bg = Image.new("RGBA", rgba_img.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba_img)
    return composited.convert("RGB")


def boost_local_contrast(rgb_img: Image.Image) -> Image.Image:
    arr = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    boosted = clahe.apply(arr)
    return Image.fromarray(boosted)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/prep_photo.py <source-photo.jpg>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    out_path = "source-prepped.png"

    print("1/3  Removing background (rembg)...")
    no_bg = remove_background(input_path)

    print("2/3  Compositing onto pure white...")
    on_white = composite_on_white(no_bg)

    print("3/3  Boosting local contrast (CLAHE)...")
    final = boost_local_contrast(on_white)

    final.save(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
