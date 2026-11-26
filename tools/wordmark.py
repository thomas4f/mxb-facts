"""Write site/brand.json: the MXB FACTS wordmark and the score figures as SVG path data, from the site's own fonts.

A badge is an image on someone else's page, where the site's fonts never load; drawn as shapes, the wordmark and the score look
the same there as in the site's header. The build reads site/brand.json (site/brand.py) and needs no font tools itself.

The wordmark is MXB and FACTS in Saira ExtraBold Italic with the badge check between them: a rounded box in the accent with a
check cut out of it, so whatever is behind the wordmark shows through the check. The box is set as one more capital: as tall
as the capitals, slanted at the font's italic angle, with the side bearings of the font's H.

Usage: python3 -I tools/wordmark.py   (once, when the fonts or the wordmark change; needs fonttools and brotli, which read woff2)
Paths are in font units with the capitals 700 tall, y pointing down, with the baseline at 0 and the cap height at -700; they
use M, L, H, V, Q and Z only, which is all site/preview.py reads.
"""
import json, math, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
FONTS = ROOT + 'site/static/fonts/'
CAP = 700      # the capitals' height the paths are drawn at
TRACK = -10    # the header's letter-spacing, -.01em
# The badge check, in a box CAP tall before the slant: the box's width and corner radius, and the check's spine (three points
# from the box's left edge) and stroke width. The check is a polyline of that width, mitred at its corner, square at its ends.
BOX_W, BOX_R = 610, 120
CHECK, CHECK_W = [(140, -370), (270, -225), (470, -500)], 105


def num(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


def load(font):
    # The font, its glyph set and cmap, and the scale that makes its capitals CAP tall.
    f = TTFont(FONTS + font); gs = f.getGlyphSet(); cmap = f.getBestCmap()
    bp = BoundsPen(gs); gs[cmap[ord('H')]].draw(bp)
    return f, gs, cmap, CAP / bp.bounds[3]


def glyphs(font, chars):
    # Each character's outline (y flipped, capitals CAP tall) and advance, so a line can be set from them.
    f, gs, cmap, s = load(font); out = {}
    for ch in chars:
        name = cmap[ord(ch)]; pen = SVGPathPen(gs, num)
        gs[name].draw(TransformPen(pen, (s, 0, 0, -s, 0, 0)))
        bp = BoundsPen(gs); gs[name].draw(TransformPen(bp, (s, 0, 0, -s, 0, 0)))
        out[ch] = {'d': pen.getCommands(), 'w': gs[name].width * s, 'b': bp.bounds}
    return out


def setline(gl, text, x0=0):
    # One line of glyphs as paths, with the header's tracking; returns the paths, the line's width and the ink's bounds (from x0).
    x, parts, ink = 0, [], []
    for ch in text:
        g = gl[ch]
        if g['d']:
            parts.append(f'<path transform="translate({num(x)} 0)" d="{g["d"]}"/>')
            b = g['b']; ink.append((x0 + x + b[0], b[1], x0 + x + b[2], b[3]))
        x += g['w'] + TRACK
    return ''.join(parts), x - TRACK, ink


def bearings(font):
    # The H's side bearings at the baseline, and the font's slant (x moves right by k for each unit up).
    f, gs, cmap, s = load(font); k = math.tan(math.radians(-f['post'].italicAngle))
    g = gs[cmap[ord('H')]]; bp = BoundsPen(gs); g.draw(bp); x0, _, x1, y1 = bp.bounds
    left = x0 * s; right = (g.width - (x1 - y1 * k)) * s  # the bounds' right edge is the top's; the stem's foot is k*y1 left of it
    return left, right, k


def box_path(k):
    # The box's outline, slanted: straight sides, each rounded corner as two quadratic curves (within 0.1 % of a circle).
    w, h, r = BOX_W, CAP, BOX_R
    pts = []
    def corner(cx, cy, a0):
        # A quarter circle of radius r around (cx, cy) from angle a0 on, as two curves through its middle.
        for i in range(2):
            a = a0 + (i + .5) * math.pi / 4; b = a0 + (i + 1) * math.pi / 4
            pts.append(('Q', (cx + r * math.cos(a) / math.cos(math.pi / 8), cy + r * math.sin(a) / math.cos(math.pi / 8)), (cx + r * math.cos(b), cy + r * math.sin(b))))
    pts.append(('M', (r, -h))); pts.append(('L', (w - r, -h))); corner(w - r, -h + r, -math.pi / 2)
    pts.append(('L', (w, -r))); corner(w - r, -r, 0)
    pts.append(('L', (r, 0))); corner(r, -r, math.pi / 2)
    pts.append(('L', (0, -h + r))); corner(r, -h + r, math.pi)
    sk = lambda p: f'{num(p[0] - k * p[1])} {num(p[1])}'
    return ''.join(c + ' '.join(sk(p) for p in ps) for c, *ps in pts) + 'Z'


def check_path(k):
    # The check as one polygon: the spine offset by half the stroke on each side, mitred at the corner, then slanted.
    h = CHECK_W / 2; n = []
    for (x1, y1), (x2, y2) in zip(CHECK, CHECK[1:]):
        L = math.hypot(x2 - x1, y2 - y1); n.append((-(y2 - y1) / L, (x2 - x1) / L))
    def side(sg):
        out = []
        for i, (px, py) in enumerate(CHECK):
            if i == 0: m = n[0]; f = h
            elif i == len(CHECK) - 1: m = n[-1]; f = h
            else:
                a, b = n[i - 1], n[i]; m = (a[0] + b[0], a[1] + b[1]); f = h / (m[0] * a[0] + m[1] * a[1])
            out.append((px + sg * m[0] * f, py + sg * m[1] * f))
        return out
    poly = side(1) + side(-1)[::-1]
    return 'M' + 'L'.join(f'{num(x - k * y)} {num(y)}' for x, y in poly) + 'Z'


BOLD = 'saira-latin-800-italic.woff2'
mark = glyphs(BOLD, 'MXBFACTS')
left, right, k = bearings(BOLD)
mxb, w1, ink1 = setline(mark, 'MXB')
box, check = box_path(k), check_path(k)
mx = w1 + TRACK + left                    # the box's foot, one capital after MXB
fx = mx + BOX_W + right + TRACK           # FACTS, one capital after the box
facts, w3, ink3 = setline(mark, 'FACTS', fx)
ink = ink1 + ink3 + [(mx, -CAP, mx + BOX_W + k * CAP, 0)]
bounds = [round(min(b[0] for b in ink), 1), round(min(b[1] for b in ink), 1), round(max(b[2] for b in ink), 1), round(max(b[3] for b in ink), 1)]
brand = {
    'about': 'Made by tools/wordmark.py from site/static/fonts; do not edit by hand.',
    'wordmark': {  # MXB and FACTS in ink, the badge check in the accent with its check cut out (even-odd): the header's .brand
        'parts': [{'x': 0, 'role': 'ink', 'g': mxb},
                  {'x': round(mx, 1), 'role': 'accent', 'g': f'<path fill-rule="evenodd" d="{box}{check}"/>'},
                  {'x': round(fx, 1), 'role': 'ink', 'g': facts}],
        'width': round(fx + w3, 1), 'cap': CAP,
        'bounds': bounds,  # the ink's box (x0, y0, x1, y1): the slant and the round letters reach past the advances
        # The badge check's pieces, for what draws it on its own (the favicon) or in steps (the home page's animation).
        'mark': {'x': round(mx, 1), 'w': BOX_W, 'r': BOX_R, 'skew': round(k, 5), 'box': box, 'check': check,
                 'spine': [list(p) for p in CHECK], 'stroke': CHECK_W},
        # How far the slant takes the box past its foot, so a box drawn around the mark alone can be centred on it.
        'lean': round(k * CAP, 1)},
    # The score as the site shows it (Saira Bold, the head face): figures, "/", "?", the dash for no score, and "." for half points.
    'figures': glyphs('saira-latin-700-normal.woff2', '0123456789/?.–'),
}
json.dump(brand, open(ROOT + 'site/brand.json', 'w'), separators=(',', ':'))
open(ROOT + 'site/brand.json', 'a').write('\n')
print('wrote site/brand.json')
