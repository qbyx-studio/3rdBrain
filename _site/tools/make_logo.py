"""Recolour the Qbyx Studio mark into the brand's accent gradient.

The source logo is a purple/pink/orange gradient, which clashes with the
Nightfall palette. Only the alpha channel is kept; the colour is replaced with
the guideline's accent gradient (#3CE1FF -> #2E8BFF -> #8B5CF6 at 120 degrees).

    python tools/make_logo.py <source.png>
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image

# Accent gradient from the brand guidelines, page 07.
STOPS = [(0.0, (0x3C, 0xE1, 0xFF)), (0.5, (0x2E, 0x8B, 0xFF)), (1.0, (0x8B, 0x5C, 0xF6))]
ANGLE_DEG = 120
OUT = Path("overlay/assets")


def _colour_at(t: float) -> tuple[int, int, int]:
    t = min(max(t, 0.0), 1.0)
    for (t0, c0), (t1, c1) in zip(STOPS, STOPS[1:]):
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0)
            return tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))
    return STOPS[-1][1]


def build(src: Path, size: int) -> Image.Image:
    logo = Image.open(src).convert("RGBA").resize((size, size), Image.LANCZOS)
    alpha = logo.getchannel("A")

    grad = Image.new("RGBA", (size, size))
    px = grad.load()
    rad = math.radians(ANGLE_DEG)
    dx, dy = math.cos(rad), math.sin(rad)

    # Project across the mark's bounding box, not the whole canvas. The logo is
    # centred with wide margins, so a canvas-wide gradient wastes both ends of
    # the ramp on empty pixels and the mark reads as one flat colour.
    x0, y0, x1, y1 = alpha.getbbox() or (0, 0, size, size)
    corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    projections = [x * dx + y * dy for x, y in corners]
    lo, hi = min(projections), max(projections)
    span = (hi - lo) or 1.0

    for y in range(size):
        for x in range(size):
            t = ((x * dx + y * dy) - lo) / span
            px[x, y] = (*_colour_at(t), 255)

    grad.putalpha(alpha)
    return grad


def main() -> int:
    src = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    for name, size in (("qbyx-logo.png", 512), ("favicon.png", 180)):
        img = build(src, size)
        img.save(OUT / name)
        print(f"  wrote {OUT/name} ({size}px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
