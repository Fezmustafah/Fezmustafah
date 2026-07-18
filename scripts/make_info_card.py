#!/usr/bin/env python3
"""
make_info_card.py — hand-authored neofetch-style info card (info-card.svg).

Looks like the output of `neofetch`: a title bar, an underline, colored
key/value rows, and a row of color blocks. Each line fades + slides in on a
short stagger so the panel looks like it is printing next to the portrait.

Edit CONFIG below to change the content — this is YOUR story, the numbers the
contribution graph can't tell.

    python scripts/make_info_card.py            # animated
    STATIC=1 python scripts/make_info_card.py   # frozen frame (local preview)
"""
import os
import html

OUT = "info-card.svg"
STATIC = bool(os.environ.get("STATIC"))

# --- edit me ---------------------------------------------------------------
USER = "fezmustafah"
HOST = "github"
# (label, value) rows. Keep values short so they fit the card width.
CONFIG = [
    ("Role",       "Full-stack Developer"),
    ("Location",   "Dubai, UAE"),
    ("Now",        "SaaS · CRMs · Booking systems"),
    # ("Prev",     "add your previous role here"),   # uncomment + edit to use
    ("Stack",      "React · Vite · Tailwind · Node"),
    ("",           "Supabase · Python · PHP / MySQL"),   # stack wrap line
    ("Highlights", "Tijara SaaS · Falcon CRM · LaModa"),
    ("Open to",    "Freelance · Upwork"),
]
# ---------------------------------------------------------------------------

# theme
BG = "#0d1117"
BORDER = "#30363d"
TITLE = "#39d353"     # green username
AT = "#c9d1d9"
HOST_C = "#58a6ff"    # blue host
LABEL = "#f0883e"     # orange keys
VALUE = "#c9d1d9"     # light values
RULE = "#484f58"
BLOCKS = ["#f85149", "#f0883e", "#e3b341", "#39d353",
          "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
FS = 15
PAD = 24
LH = 27
LABEL_W = 118

# layout math
title_txt = f"{USER}@{HOST}"
n_rows = len(CONFIG)
# rows: title, underline, gap, config rows, gap, color blocks
top = PAD + FS
underline_y = top + 8
first_row = underline_y + 20
last_row_y = first_row + (n_rows - 1) * LH
blocks_y = last_row_y + LH + 6
height = blocks_y + 22 + PAD
width = 560

STAGGER = 0.12
START = 0.15


def esc(s):
    return html.escape(s, quote=True)


def anim_group(inner, order):
    """Wrap inner SVG in a fade+slide-in group (or static if STATIC)."""
    if STATIC:
        return f'<g>{inner}</g>'
    begin = START + order * STAGGER
    return (
        f'<g opacity="0" transform="translate(-10,0)">'
        f'<animate attributeName="opacity" from="0" to="1" '
        f'begin="{begin:.2f}s" dur="0.45s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="-10 0" to="0 0" begin="{begin:.2f}s" dur="0.45s" '
        f'calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1" '
        f'fill="freeze"/>{inner}</g>'
    )


def build():
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height:.0f}" viewBox="0 0 {width} {height:.0f}" '
        f'font-family="{FONT}">',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2:.0f}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}"/>',
    ]

    order = 0
    # title:  user@host
    ul = len(title_txt)
    title = (
        f'<text x="{PAD}" y="{top}" font-size="{FS}" font-weight="700">'
        f'<tspan fill="{TITLE}">{esc(USER)}</tspan>'
        f'<tspan fill="{AT}">@</tspan>'
        f'<tspan fill="{HOST_C}">{esc(HOST)}</tspan></text>'
    )
    p.append(anim_group(title, order)); order += 1

    # underline
    rule = (f'<line x1="{PAD}" y1="{underline_y}" x2="{PAD + ul*9}" '
            f'y2="{underline_y}" stroke="{RULE}" stroke-width="1.5"/>')
    p.append(anim_group(rule, order)); order += 1

    # rows
    for i, (label, value) in enumerate(CONFIG):
        y = first_row + i * LH
        if label:
            row = (
                f'<text y="{y}" font-size="{FS}">'
                f'<tspan x="{PAD}" fill="{LABEL}" font-weight="700">{esc(label)}</tspan>'
                f'<tspan x="{PAD + LABEL_W}" fill="{VALUE}">{esc(value)}</tspan></text>'
            )
        else:  # continuation line (no label)
            row = (f'<text x="{PAD + LABEL_W}" y="{y}" font-size="{FS}" '
                   f'fill="{VALUE}">{esc(value)}</text>')
        p.append(anim_group(row, order)); order += 1

    # color blocks (neofetch signature)
    bw = 22
    blocks = ['<g>']
    for j, c in enumerate(BLOCKS):
        blocks.append(
            f'<rect x="{PAD + j*bw}" y="{blocks_y}" width="{bw-4}" '
            f'height="14" rx="2" fill="{c}"/>'
        )
    blocks.append('</g>')
    p.append(anim_group("".join(blocks), order)); order += 1

    p.append("</svg>")
    return "".join(p)


def main():
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build())
    mode = "static" if STATIC else "animated"
    print(f"[card] wrote {OUT} ({mode})")


if __name__ == "__main__":
    main()
