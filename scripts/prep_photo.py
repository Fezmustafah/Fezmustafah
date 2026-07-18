#!/usr/bin/env python3
"""
prep_photo.py — turn a raw photo into a clean grayscale source for ASCII art.

Steps:
  1. (optional) remove the background with rembg so the subject is isolated.
  2. boost local contrast with CLAHE so a flat face gains real highlights/shadows.
  3. composite onto pure white so the background maps to the blank end of the
     ASCII ramp (white -> spaces).

Output: source-prepped.png  (grayscale, ready for make_ascii_svg.py)

Usage:
    python scripts/prep_photo.py source-photo.jpg
    python scripts/prep_photo.py source-photo.jpg --no-rembg   # skip bg removal

rembg is OPTIONAL. If it is not installed (or fails), the script falls back to a
brightness-based background wash, which works well when the subject is darker
than the background (as in most portraits).
"""
import sys
import os
import argparse
import numpy as np
import cv2
from PIL import Image

OUT = "source-prepped.png"


def load_rgba(path):
    img = Image.open(path).convert("RGBA")
    return img


def try_rembg(pil_img):
    """Return an RGBA PIL image with background removed, or None if unavailable."""
    try:
        from rembg import remove
    except Exception as e:  # ImportError or onnxruntime load failure
        print(f"[prep] rembg unavailable ({e.__class__.__name__}); using fallback.")
        return None
    try:
        print("[prep] removing background with rembg (first run downloads a model)...")
        return remove(pil_img)
    except Exception as e:
        print(f"[prep] rembg failed ({e}); using fallback.")
        return None


def composite_on_white(rgba):
    """Flatten an RGBA image onto a pure-white background -> RGB PIL image."""
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, rgba).convert("RGB")


def apply_clahe(gray_np):
    """Contrast-limited adaptive histogram equalization on a uint8 grayscale array."""
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray_np)


def brightness_fallback(rgb_np, cutoff=205):
    """
    No rembg: push near-white/bright pixels fully to white so the background
    clears to blank glyphs. Keeps darker subject intact.
    """
    gray = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2GRAY)
    # soft mask: pixels brighter than cutoff -> white
    mask = gray >= cutoff
    out = rgb_np.copy()
    out[mask] = (255, 255, 255)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo", help="path to source photo (jpg/png)")
    ap.add_argument("--no-rembg", action="store_true", help="skip background removal")
    ap.add_argument("--cutoff", type=int, default=205,
                    help="fallback brightness cutoff for background wash (0-255)")
    args = ap.parse_args()

    if not os.path.exists(args.photo):
        sys.exit(f"[prep] file not found: {args.photo}")

    pil = load_rgba(args.photo)

    rgba = None
    if not args.no_rembg:
        rgba = try_rembg(pil)

    if rgba is not None:
        rgb = composite_on_white(rgba)
        rgb_np = np.array(rgb)
    else:
        rgb_np = np.array(pil.convert("RGB"))
        rgb_np = brightness_fallback(rgb_np, cutoff=args.cutoff)

    gray = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2GRAY)
    gray = apply_clahe(gray)

    Image.fromarray(gray).save(OUT)
    print(f"[prep] wrote {OUT}  ({gray.shape[1]}x{gray.shape[0]})")


if __name__ == "__main__":
    main()
