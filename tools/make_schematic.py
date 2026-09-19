#!/usr/bin/env python3
"""Draw the JENNIFER cross-section as SVG.

Writes assets/jennifer-schematic.svg and rewrites the inline copy in
index.html, which is the one the page shows: inline means the page fonts
reach the labels inside the figure.

    uv run tools/make_schematic.py
"""

import math
import random
import re
from pathlib import Path

W, H = 1000, 300
CREST_X, CREST_W = 560, 310          # anticline centre and half-width
OWC, GOC = 116, 98                   # oil-water and gas-oil contacts, flat
WELLS = (175, 500, 855)

INK = "#14161a"
TEAL = "#1c9c97"
GAS = "#b0d8e1"
GREY = "#8892a8"

# flank depth -> fill, pattern, right-edge label
BEDS = [
    (150, "#e3eaf5", "shale", "Seal (shale)"),
    (190, "#f1ecdc", "sand", "Reservoir sand"),
    (248, "#e0e4ef", "brick", "Limestone"),
    (278, "#cfd2e0", "organic", "Source rock"),
    (300, "#d8d5dd", "crystal", "Basement"),
]


def fold(x):
    """Bell curve, 1 at the crest and 0 out on the flanks."""
    return math.exp(-(((x - CREST_X) / CREST_W) ** 2))


def horizon(x, depth):
    """Depth of a bed boundary at x. Deeper beds arch a little harder."""
    return depth - (48 + 0.09 * depth) * fold(x)


def seabed(x):
    return 38 + 2.5 * math.sin(x / 55)


def curve(depth, step=20):
    xs = list(range(0, W + 1, step))
    return [(x, horizon(x, depth)) for x in xs]


def poly(points):
    return " ".join(f"{x:g},{y:.1f}" for x, y in points)


def band(top_pts, bottom_pts):
    """Closed path between two horizons, left to right and back."""
    return "M " + poly(top_pts) + " L " + poly(reversed(bottom_pts)) + " Z"


def log_trace(x0, y0, y1, seed):
    """A wiggly borehole log: random walk pulled back towards the hole."""
    rng = random.Random(seed)
    pts, v = [], 0.0
    y = y0
    while y < y1:
        v = v * 0.55 + rng.uniform(-3.2, 3.2)
        pts.append((x0 + max(-7, min(9, v * 2.0)), y))
        y += 3.5
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def patterns():
    return f"""  <defs>
    <pattern id="p-shale" width="26" height="9" patternUnits="userSpaceOnUse">
      <path d="M0 4.5 H15" stroke="#b9c2cc" stroke-width=".8"/>
    </pattern>
    <pattern id="p-sand" width="11" height="9" patternUnits="userSpaceOnUse">
      <circle cx="3" cy="3" r="1.05" fill="#cdbb92"/>
      <circle cx="8.5" cy="7" r="1.05" fill="#cdbb92"/>
    </pattern>
    <pattern id="p-brick" width="22" height="12" patternUnits="userSpaceOnUse">
      <path d="M0 6 H22 M0 12 H22 M11 0 V6 M0 6 V12 M22 6 V12"
            stroke="#c3cfe3" stroke-width=".8" fill="none"/>
    </pattern>
    <pattern id="p-organic" width="20" height="8" patternUnits="userSpaceOnUse">
      <path d="M0 4 H11" stroke="#a9b0c4" stroke-width="1"/>
    </pattern>
    <pattern id="p-crystal" width="13" height="13" patternUnits="userSpaceOnUse">
      <path d="M0 0 L13 13 M13 0 L0 13" stroke="#a9a2b8" stroke-width=".8"/>
    </pattern>
    <clipPath id="panel"><rect width="{W}" height="{H}"/></clipPath>
  </defs>"""


def build():
    out = [
        f'<svg class="schematic" viewBox="0 0 {W} {H}" role="img" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'aria-label="Cross-section of a faulted anticline with three wells. '
        f'JENNIFER infers every layer boundary and the trap between them.">',
        patterns(),
        '  <g clip-path="url(#panel)">',
    ]

    # sea, then each bed from a flat-lying sea floor down into the basement
    sea = [(x, seabed(x)) for x in range(0, W + 1, 20)]
    out.append(f'    <rect width="{W}" height="{H}" fill="#eef1f8"/>')
    out.append(
        f'    <path d="M 0,0 L {poly(sea)} L {W},0 Z" fill="#d6f0f3"/>'
    )

    top = sea
    for depth, fill, pat, _ in BEDS:
        bottom = curve(depth) if depth < H else [(x, H + 40) for x, _ in top]
        out.append(f'    <path d="{band(top, bottom)}" fill="{fill}"/>')
        out.append(f'    <path d="{band(top, bottom)}" fill="url(#p-{pat})"/>')
        top = bottom
    out.append(f'    <path d="M {poly(sea)}" fill="none" stroke="#7c86a8" stroke-width="1.1"/>')

    # what the model infers: every boundary, dashed, plus the beds between them
    out.append('    <g fill="none" stroke="' + TEAL + '" stroke-width="1.3" '
               'stroke-dasharray="9 7" opacity=".85">')
    for depth in (108, 130, 150, 170, 190, 216, 248, 264, 278):
        out.append(f'      <path d="M {poly(curve(depth))}"/>')
    out.append("    </g>")

    # the trap: gas over oil, both cut flat by their contacts
    res = curve(150, step=5)
    for contact, lo, colour in ((GOC, None, GAS), (OWC, GOC, TEAL)):
        cap = [(x, max(y, lo) if lo else y) for x, y in res if y < contact]
        if not cap:
            continue
        floor = [(x, contact) for x, _ in cap]
        out.append(f'    <path d="{band(cap, floor)}" fill="{colour}"/>')
    out.append(
        f'    <path d="M {min(x for x, y in res if y < OWC)},{OWC} '
        f'H {max(x for x, y in res if y < OWC)}" stroke="{INK}" '
        f'stroke-width=".9" stroke-dasharray="2 2.5"/>'
    )

    # a normal fault, near vertical, leaning back as it goes down
    out.append(f'    <path d="M 300,40 L 262,{H}" stroke="{INK}" stroke-width="2.2"/>')

    # three wells, each with its log
    for i, x in enumerate(WELLS):
        head, toe = (24, H) if i == 1 else (34, H - 22)
        out.append(f'    <rect x="{x - 13}" y="{head}" width="30" height="{toe - head}" '
                   f'fill="{INK}" opacity=".06"/>')
        out.append(f'    <path d="{log_trace(x + 9, head + 14, toe - 6, i)}" '
                   f'fill="none" stroke="{INK}" stroke-width="1.1"/>')
        out.append(f'    <rect x="{x - 2.2}" y="{head}" width="4.4" height="{toe - head}" fill="{INK}"/>')
        if i == 1:
            out.append(f'    <rect x="{x - 24}" y="{head - 8}" width="48" height="6" fill="{INK}"/>')
            out.append(f'    <rect x="{x - 9}" y="{head - 17}" width="18" height="9" fill="{INK}"/>')
        else:
            out.append(f'    <rect x="{x - 6}" y="{head - 5}" width="12" height="7" fill="{INK}"/>')

    out.append("  </g>")

    # labels sit on top of the art
    out.append(f'  <text class="s-fig" x="600" y="80" fill="{TEAL}" '
               f'font-weight="600" text-anchor="middle">Inferred trap</text>')
    out.append(f'  <text class="s-tiny" x="762" y="{OWC + 11}" fill="{INK}" '
               f'text-anchor="middle">Oil-water contact</text>')
    out.append(f'  <text class="s-fig" x="320" y="72" fill="{INK}">Normal fault</text>')
    out.append(f'  <text class="s-mark" x="16" y="286" fill="{INK}">schematic</text>')

    out.append(f'  <text class="s-fig" x="{W - 12}" y="26" fill="{GREY}" text-anchor="end">Sea</text>')
    edge = [seabed(W)] + [horizon(W, d) for d, *_ in BEDS]
    for (depth, _, _, label), top_y, bottom_y in zip(BEDS, edge, edge[1:]):
        mid = (top_y + min(bottom_y, H)) / 2 + 4
        out.append(f'  <text class="s-fig" x="{W - 12}" y="{mid:.0f}" fill="{GREY}" '
                   f'text-anchor="end">{label}</text>')

    out.append(f'  <g><rect x="690" y="38" width="9" height="9" fill="{GAS}"/>'
               f'<text class="s-fig" x="705" y="46.5" fill="{GREY}">Gas</text>'
               f'<rect x="690" y="52" width="9" height="9" fill="{TEAL}"/>'
               f'<text class="s-fig" x="705" y="60.5" fill="{GREY}">Oil</text></g>')

    out.append(f'  <rect width="{W}" height="{H}" fill="none" stroke="#b9c2cc" stroke-width="1"/>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    svg = build()
    root = Path(__file__).resolve().parent.parent

    # standalone copy: no page CSS to inherit, so it carries its own type sizes
    style = ('<style>.s-fig{font:13px Georgia,serif}.s-tiny{font:10px Georgia,serif}'
             '.s-mark{font:15px Georgia,serif}</style>\n')
    (root / "assets" / "jennifer-schematic.svg").write_text(
        svg.replace("<defs>", style + "  <defs>", 1)
    )

    page = root / "index.html"
    html, n = re.subn(
        r'<svg class="schematic".*?</svg>',
        lambda _: "\n".join("    " + line for line in svg.splitlines()).strip(),
        page.read_text(),
        count=1,
        flags=re.S,
    )
    page.write_text(html)
    print(f"{len(svg) / 1024:.1f} kB, inlined into index.html" if n else "no <svg class=schematic> in index.html")
