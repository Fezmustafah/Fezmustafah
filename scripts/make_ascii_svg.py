#!/usr/bin/env python3
"""
make_ascii_svg.py — convert source-prepped.png into a self-typing monochrome
ASCII-art SVG (avi-ascii.svg).

- Downsamples the prepped image to a character grid.
- Maps each cell's brightness to a glyph from a density ramp
  (bright -> sparse, dark -> dense). Leading SPACE clears background to nothing.
- Monochrome (one light-gray fill) on a dark panel — no rainbow noise.
- Each row wipes in left-to-right with a block cursor, staggered top->bottom.
  Plays once and freezes (SMIL, so GitHub renders it). No looping.

Usage:
    python scripts/make_ascii_svg.py                  # reads source-prepped.png
    python scripts/make_ascii_svg.py my-prepped.png   # custom input
"""
import sys
import html
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
OUT = "avi-ascii.svg"

# --- tunables ---------------------------------------------------------------
COLS = 100                       # character columns
CHAR_ASPECT = 0.50               # glyph cell height/width correction
RAMP = " .`:-=+*cs#%@"           # bright (sparse) -> dark (dense)
FONT_SIZE = 10
CELL_W = FONT_SIZE * 0.60        # monospace advance width
LINE_H = FONT_SIZE * 1.08
PAD = 18
FG = "#c9d1d9"                   # light gray glyphs
BG = "#0d1117"                   # terminal panel
CURSOR = "#39d353"               # green wipe cursor
TYPE_DUR = 0.55                  # seconds per row wipe
ROW_STAGGER = 0.045              # delay added per row
# ---------------------------------------------------------------------------


def build_grid(path):
    try:
        img = Image.open(path).convert("L")
    except FileNotFoundError:
        sys.exit(f"[ascii] {path} not found. Run prep_photo.py first.")
    w, h = img.size
    rows = max(1, int(COLS * (h / w) * CHAR_ASPECT))
    small = img.resize((COLS, rows), Image.LANCZOS)
    px = small.load()
    lines = []
    n = len(RAMP) - 1
    for y in range(rows):
        row = []
        for x in range(COLS):
            b = px[x, y]                       # 0=black .. 255=white
            idx = round((255 - b) / 255 * n)   # white -> 0 -> space
            row.append(RAMP[idx])
        # trim trailing spaces (keeps SVG small, wipe still spans full width)
        lines.append("".join(row).rstrip())
    return lines, rows


def make_svg(lines, rows):
    grid_w = COLS * CELL_W
    width = grid_w + 2 * PAD
    height = rows * LINE_H + 2 * PAD
    total = rows * ROW_STAGGER + TYPE_DUR

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">'
    )
    parts.append(f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>')

    for i, line in enumerate(lines):
        y = PAD + (i + 1) * LINE_H - 2
        begin = i * ROW_STAGGER
        clip_id = f"c{i}"
        text = html.escape(line, quote=False)
        # per-row clip that wipes 0 -> full width
        # base width is FULL so GitHub's static render shows the whole row; the
        # wipe (0 -> full) only enhances browsers that run the animation.
        parts.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{PAD:.1f}" y="{y - LINE_H:.1f}" width="{grid_w:.1f}" height="{LINE_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{grid_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{TYPE_DUR:.3f}s" '
            f'calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1" '
            f'fill="freeze"/></rect></clipPath>'
        )
        parts.append(
            f'<text x="{PAD:.1f}" y="{y:.1f}" fill="{FG}" '
            f'font-size="{FONT_SIZE}" xml:space="preserve" '
            f'clip-path="url(#{clip_id})" '
            f'style="white-space:pre">{text}</text>'
        )
        # cursor block riding the wipe edge, fades out when the row finishes
        if line:
            parts.append(
                f'<rect y="{y - LINE_H + 1.5:.1f}" width="{CELL_W:.1f}" '
                f'height="{LINE_H - 2:.1f}" fill="{CURSOR}" opacity="0">'
                f'<animate attributeName="x" from="{PAD:.1f}" '
                f'to="{PAD + grid_w:.1f}" begin="{begin:.3f}s" '
                f'dur="{TYPE_DUR:.3f}s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="0;0.9;0.9;0" '
                f'keyTimes="0;0.05;0.95;1" begin="{begin:.3f}s" '
                f'dur="{TYPE_DUR:.3f}s" fill="freeze"/></rect>'
            )

    parts.append("</svg>")
    return "".join(parts)


def main():
    lines, rows = build_grid(SRC)
    svg = make_svg(lines, rows)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[ascii] wrote {OUT}  ({COLS}x{rows} grid)")


if __name__ == "__main__":
    main()
