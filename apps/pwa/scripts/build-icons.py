#!/usr/bin/env python3
"""The PWA icon: a white ground and the wordmark, nothing else (owner, 2026-09-13).

Outlines FLAVOR (Stack Sans wght 700) and WORDS (Fraunces wght 600 / opsz 144 / SOFT 60 / WONK 1) from the fonts the
app ships, fitted to one width the way Wordmark.vue fits them (textLength with spacing), so the SVG needs no fonts.
Writes apps/pwa/public/icons/icon.svg; rasterize-icons.mjs turns it into the PNG sizes iOS and Android read.
"""
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "public" / "fonts"
OUT = ROOT / "public" / "icons" / "icon.svg"

CANVAS = 512
WORD_WIDTH = 352  # the wordmark's 100-unit width in canvas px (68.75%): inside the maskable safe zone (limit 363)
INK = "#1E1C1A"
ACCENT = "#7268C9"

# the two lines exactly as Wordmark.vue sets them (100-unit coordinate system)
LINES = [
    ("FLAVOR", "StackSansText-Variable.woff2", {"wght": 700}, 26.0, 24.0, -0.01, INK),
    ("WORDS", "Fraunces-Variable.woff2", {"opsz": 144, "wght": 600, "SOFT": 60, "WONK": 1}, 27.0, 50.0, 0.0, ACCENT),
]


def outline(word, font_file, location, size, baseline, letter_spacing_em, scale, dx, dy):
    font = instancer.instantiateVariableFont(TTFont(FONTS / font_file), location)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()
    names = [cmap[ord(c)] for c in word]
    unit = size / upem  # font units → wordmark units
    advances = [font["hmtx"][n][0] * unit for n in names]
    gap = letter_spacing_em * size
    natural = sum(advances) + gap * (len(names) - 1)
    extra = (100.0 - natural) / (len(names) - 1)  # lengthAdjust="spacing" to textLength 100
    pen = SVGPathPen(glyph_set)
    x = 0.0
    bounds = [1e9, 1e9, -1e9, -1e9]
    for name, adv in zip(names, advances):
        # font units → canvas px: scale, flip y, place on the baseline
        tpen = TransformPen(pen, (unit * scale, 0, 0, -unit * scale, dx + x * scale, dy + baseline * scale))
        glyph_set[name].draw(tpen)
        bpen_font = glyph_set[name]
        # bounds for centering (units)
        from fontTools.pens.boundsPen import BoundsPen

        bp = BoundsPen(glyph_set)
        bpen_font.draw(bp)
        if bp.bounds:
            x0, y0, x1, y1 = bp.bounds
            bounds = [min(bounds[0], x + x0 * unit), min(bounds[1], baseline - y1 * unit), max(bounds[2], x + x1 * unit), max(bounds[3], baseline - y0 * unit)]
        x += adv + gap + extra
    return pen.getCommands(), bounds


def build():
    scale = WORD_WIDTH / 100.0
    # first pass: ink bounds in wordmark units, to centre the ink block (not the 100×52 box) on the canvas
    ink = [1e9, 1e9, -1e9, -1e9]
    for word, f, loc, size, baseline, ls, _ in LINES:
        _, b = outline(word, f, loc, size, baseline, ls, scale, 0, 0)
        ink = [min(ink[0], b[0]), min(ink[1], b[1]), max(ink[2], b[2]), max(ink[3], b[3])]
    ink_w = (ink[2] - ink[0]) * scale
    ink_h = (ink[3] - ink[1]) * scale
    dx = (CANVAS - ink_w) / 2 - ink[0] * scale
    dy = (CANVAS - ink_h) / 2 - ink[1] * scale
    paths = []
    for word, f, loc, size, baseline, ls, fill in LINES:
        d, _ = outline(word, f, loc, size, baseline, ls, scale, dx, dy)
        paths.append(f'  <path d="{d}" fill="{fill}"/>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS} {CANVAS}" width="{CANVAS}" height="{CANVAS}">\n'
        f'  <rect width="{CANVAS}" height="{CANVAS}" fill="#FFFFFF"/>\n' + "\n".join(paths) + "\n</svg>\n"
    )
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT.parent.parent)} ({len(svg)} bytes); ink {ink_w:.0f}×{ink_h:.0f} px centred on {CANVAS}")


if __name__ == "__main__":
    build()
