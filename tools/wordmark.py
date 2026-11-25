"""Write site/brand.json: the MXB/FACTS wordmark and the score figures as SVG path data, from the site's own fonts.

A badge is an image on someone else's page, where the site's fonts never load; drawn as shapes, the wordmark and the score look
the same there as in the site's header. The build reads site/brand.json (site/brand.py) and needs no font tools itself.

Usage: python3 -I tools/wordmark.py   (once, when the fonts or the wordmark change; needs fonttools and brotli, which read woff2)
Paths are in font units (1000 to the em), y pointing down, with the baseline at 0 and the cap height at -700.
"""
import json, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
FONTS = ROOT + 'site/static/fonts/'
TRACK = -10  # the header's letter-spacing, -.01em


def glyphs(font, chars):
    # Each character's outline (y flipped) and advance, so a line can be set from them.
    f = TTFont(FONTS + font); gs = f.getGlyphSet(); cmap = f.getBestCmap(); out = {}
    for ch in chars:
        name = cmap[ord(ch)]; pen = SVGPathPen(gs, lambda v: f'{v:g}')
        gs[name].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
        out[ch] = {'d': pen.getCommands(), 'w': gs[name].width}
    return out


def setline(gl, text):
    # One line of glyphs as one path, with the header's tracking; returns the path and its width.
    x, parts = 0, []
    for ch in text:
        g = gl[ch]
        if g['d']: parts.append(f'<path transform="translate({x:g} 0)" d="{g["d"]}"/>')
        x += g['w'] + TRACK
    return ''.join(parts), x - TRACK


mark = glyphs('barlow-latin-800-italic.woff2', 'MXBFACTS/')
mxb, w1 = setline(mark, 'MXB'); slash, w2 = setline(mark, '/'); facts, w3 = setline(mark, 'FACTS')
brand = {
    'about': 'Made by tools/wordmark.py from site/static/fonts; do not edit by hand.',
    'wordmark': {  # MXB in ink, the slash in the accent, FACTS in ink: the header's .brand
        'parts': [{'x': 0, 'role': 'ink', 'g': mxb}, {'x': w1 + TRACK, 'role': 'accent', 'g': slash}, {'x': w1 + w2 + 2 * TRACK, 'role': 'ink', 'g': facts}],
        'width': w1 + w2 + w3 + 2 * TRACK, 'cap': 700},
    # The score as the site shows it (Barlow Condensed 700): figures, "/", "?", the dash for no score, and "." for half points.
    'figures': glyphs('barlow-condensed-latin-700-normal.woff2', '0123456789/?.–'),
}
json.dump(brand, open(ROOT + 'site/brand.json', 'w'), separators=(',', ':'))
open(ROOT + 'site/brand.json', 'a').write('\n')
print('wrote site/brand.json')
