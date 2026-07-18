#!/usr/bin/env python3
"""
render_heatmap_svg.py — draw data/contributions.json as the classic
53-week x 7-day contribution calendar (contrib-heatmap.svg).

Rounded, colored boxes on a GitHub-ish green ramp. Reveals once with a
diagonal, line-after-line slide-down (CSS keyframes that play on load, then
freeze — no looping glow). Includes month labels, a Less->More legend, and a
stats footer.

    python scripts/render_heatmap_svg.py
"""
import os
import json
from datetime import datetime

SRC = os.path.join("data", "contributions.json")
OUT = "contrib-heatmap.svg"

# GitHub-ish ramp; index 5 is a neon top end for the busiest days.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD_L = 30          # room for weekday labels
PAD_T = 30          # room for month labels
PAD_R = 16
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
TEXT = "#8b949e"
BG = "#0d1117"
BORDER = "#30363d"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load():
    with open(SRC, encoding="utf-8") as f:
        return json.load(f)


def level_for(day, best_count):
    lvl = int(day.get("level", 0))
    # promote the very busiest level-4 days to the neon level 5
    if lvl >= 4 and best_count and day["count"] >= 0.70 * best_count:
        return 5
    return lvl


def build(data):
    days = data["days"]
    stats = data.get("stats", {})
    best_count = stats.get("best_day", {}).get("count", 0) or 0

    # position every day: consecutive dates -> (col, row) with Sunday on top
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    first_dow = (first.weekday() + 1) % 7   # Mon=0..Sun=6  ->  Sun=0..Sat=6
    placed = []
    max_col = 0
    for i, d in enumerate(days):
        slot = first_dow + i
        col, row = slot // 7, slot % 7
        max_col = max(max_col, col)
        placed.append((col, row, d))

    grid_w = (max_col + 1) * STEP
    width = PAD_L + grid_w + PAD_R
    footer_h = 44
    legend_h = 26
    height = PAD_T + 7 * STEP + legend_h + footer_h

    css = (
        "<style>"
        "@keyframes pop{from{opacity:0;transform:translateY(-8px)}"
        "to{opacity:1;transform:translateY(0)}}"
        # base state is VISIBLE (opacity:1) so GitHub's static render shows the
        # full grid; the reveal only enhances browsers that run the animation.
        ".cell{opacity:1;transform-box:fill-box;"
        "animation:pop .45s ease-out forwards}"
        "@media(prefers-reduced-motion:reduce){"
        ".cell{animation:none;opacity:1}}"
        "</style>"
    )

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" font-family="{FONT}">',
        css,
        f'<rect width="100%" height="100%" rx="10" fill="{BG}" stroke="{BORDER}"/>',
    ]

    # month labels (top), one per column where the month first appears
    seen_month = None
    for col, row, d in placed:
        if row != 0:
            continue
        m = int(d["date"][5:7])
        if m != seen_month:
            seen_month = m
            x = PAD_L + col * STEP
            p.append(f'<text x="{x}" y="{PAD_T - 10}" font-size="9" '
                     f'fill="{TEXT}">{MONTHS[m-1]}</text>')

    # weekday labels (Mon / Wed / Fri)
    for row, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = PAD_T + row * STEP + CELL - 2
        p.append(f'<text x="4" y="{y}" font-size="9" fill="{TEXT}">{lab}</text>')

    # day cells with diagonal reveal delay
    for col, row, d in placed:
        lvl = level_for(d, best_count)
        x = PAD_L + col * STEP
        y = PAD_T + row * STEP
        delay = (col + row) * 0.012
        p.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{PALETTE[lvl]}" '
            f'style="animation-delay:{delay:.3f}s">'
            f'<title>{d["count"]} on {d["date"]}</title></rect>'
        )

    # legend: Less [][][][][] More
    lg_y = PAD_T + 7 * STEP + 6
    lx = PAD_L
    p.append(f'<text x="{lx}" y="{lg_y + CELL - 2}" font-size="9" '
             f'fill="{TEXT}">Less</text>')
    lx += 32
    for i in range(5):
        p.append(f'<rect x="{lx + i*STEP}" y="{lg_y}" width="{CELL}" '
                 f'height="{CELL}" rx="2.5" fill="{PALETTE[i]}"/>')
    lx2 = lx + 5 * STEP + 4
    p.append(f'<text x="{lx2}" y="{lg_y + CELL - 2}" font-size="9" '
             f'fill="{TEXT}">More</text>')

    # footer stats line
    total = stats.get("total", 0)
    cur = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    best = stats.get("best_day", {})
    fy = lg_y + legend_h + 14
    p.append(
        f'<text x="{PAD_L}" y="{fy}" font-size="12" fill="#c9d1d9" '
        f'font-weight="700">{total:,} contributions in the last year</text>'
    )
    sub = (f"Current streak {cur}d  ·  Longest {longest}d  ·  "
           f"Best day {best.get('count', 0)}")
    p.append(f'<text x="{PAD_L}" y="{fy + 17}" font-size="10" '
             f'fill="{TEXT}">{sub}</text>')

    p.append("</svg>")
    return "".join(p)


def main():
    data = load()
    svg = build(data)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[heatmap] wrote {OUT}")


if __name__ == "__main__":
    main()
