"""The MXB/FACTS identity, in one place for everything drawn outside the site's pages: the badges (badges.py), the link-preview
images (preview.py) and the favicon. Its colours are the pit board's (the dark theme), read from site/static/site.css; its
wordmark and score figures are shapes from site/brand.json (made by tools/wordmark.py from the site's fonts), so a badge looks
the same on any page, where the site's fonts never load.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
_css = open(HERE + 'static/site.css').read()


def _theme(start):
    block = _css[_css.index(start):_css.index('}', _css.index(start))]
    return dict(re.findall(r'--([a-z-]+): (#[0-9a-f]{6})', block))


DARK = _theme(':root {')                      # the pit board: what badges and previews are drawn in
LIGHT = _theme(':root[data-theme="light"]')   # only the favicon uses it, for light browser chrome
for _k in ('bg', 'surface', 'sunk', 'line', 'ink', 'muted', 'accent', 'accent-ink'):
    assert _k in DARK and _k in LIGHT, f'site/static/site.css: each theme needs --{_k}'
RED = '#cf222e'  # signs of malware, and nothing else

B = json.load(open(HERE + 'brand.json'))
WM = B['wordmark']; FIG = B['figures']


def wordmark_width(cap):
    return WM['width'] * cap / WM['cap']


def wordmark(x, y, cap, ink=None, accent=None):
    # The wordmark with its baseline at y and capitals cap pixels tall: MXB and FACTS in ink, the slash in the accent.
    s = cap / WM['cap']; col = {'ink': ink or DARK['ink'], 'accent': accent or DARK['accent']}
    return (f'<g transform="translate({x:g} {y:g}) scale({s:.5g})" aria-hidden="true">'
            + ''.join(f'<g fill="{col[p["role"]]}" transform="translate({p["x"]:g} 0)">{p["g"]}</g>' for p in WM['parts']) + '</g>')


def figures_width(text, cap):
    return sum(FIG[ch]['w'] for ch in text) * cap / 700


def figures(text, x, y, cap, fill, anchor='start'):
    # The score in the site's figures (Barlow Condensed), baseline at y; anchor start, middle or end, as in SVG text.
    s = cap / 700; w = figures_width(text, cap)
    x0 = x - (w / 2 if anchor == 'middle' else w if anchor == 'end' else 0); out, cx = [], 0
    for ch in text:
        if FIG[ch]['d']: out.append(f'<path transform="translate({cx:g} 0)" d="{FIG[ch]["d"]}"/>')
        cx += FIG[ch]['w']
    return f'<g fill="{fill}" transform="translate({x0:.2f} {y:g}) scale({s:.5g})" aria-hidden="true">{"".join(out)}</g>'


def favicon():
    # A pit-board tile with the wordmark's slash, in the accent, for both browser themes.
    sl = WM['parts'][1]['g']; s = .074
    tile = lambda bg: (f'<rect width="64" height="64" rx="14" fill="{bg}"/>'
                       f'<g fill="{DARK["accent"]}" transform="translate({32 - 254 * s:.2f} {32 + 350 * s:.2f}) scale({s})">{sl}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><style>.l{{display:none}}@media (prefers-color-scheme: light){{.d{{display:none}}.l{{display:inline}}}}</style>'
            f'<g class="d">{tile(DARK["bg"])}</g><g class="l">{tile(LIGHT["ink"])}</g></svg>')
