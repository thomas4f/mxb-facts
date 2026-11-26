"""The MXB FACTS identity, in one place for everything drawn outside the site's pages: the badges (badges.py), the link-preview
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
# The light theme is written twice in site.css (for a light system setting, and when the reader picks it); they must not drift.
_block = lambda start: ' '.join(_css[_css.index(start) + len(start):_css.index('}', _css.index(start))].split())
assert _block(':root:not([data-theme="dark"]) {') == _block(':root[data-theme="light"] {'), 'site/static/site.css: the two light theme blocks differ'
for _k in ('bg', 'surface', 'sunk', 'line', 'ink', 'muted', 'accent', 'accent-ink'):
    assert _k in DARK and _k in LIGHT, f'site/static/site.css: each theme needs --{_k}'
RED = '#cf222e'  # signs of malware, and nothing else

B = json.load(open(HERE + 'brand.json'))
WM = B['wordmark']; FIG = B['figures']


def wordmark_width(cap):
    return WM['width'] * cap / WM['cap']


def wordmark(x, y, cap, ink=None, accent=None):
    # The wordmark with its baseline at y and capitals cap pixels tall: MXB and FACTS in ink, the badge check in the accent.
    s = cap / WM['cap']; col = {'ink': ink or DARK['ink'], 'accent': accent or DARK['accent']}
    return (f'<g transform="translate({x:g} {y:g}) scale({s:.5g})" aria-hidden="true">'
            + ''.join(f'<g fill="{col[p["role"]]}" transform="translate({p["x"]:g} 0)">{p["g"]}</g>' for p in WM['parts']) + '</g>')


def figures_width(text, cap):
    return sum(FIG[ch]['w'] for ch in text) * cap / 700


def figures(text, x, y, cap, fill, anchor='start'):
    # The score in the site's figures (Saira, the head face), baseline at y; anchor start, middle or end, as in SVG text.
    s = cap / 700; w = figures_width(text, cap)
    x0 = x - (w / 2 if anchor == 'middle' else w if anchor == 'end' else 0); out, cx = [], 0
    for ch in text:
        if FIG[ch]['d']: out.append(f'<path transform="translate({cx:g} 0)" d="{FIG[ch]["d"]}"/>')
        cx += FIG[ch]['w']
    return f'<g fill="{fill}" transform="translate({x0:.2f} {y:g}) scale({s:.5g})" aria-hidden="true">{"".join(out)}</g>'


def favicon():
    # The badge check on its own, in the accent, its check cut out to show the tab behind it; the light theme's accent for light
    # browser chrome.
    m = WM['mark']; s = 60 / (m['w'] + WM['lean']); x = (64 - (m['w'] + WM['lean']) * s) / 2; y = (64 + WM['cap'] * s) / 2
    mark = lambda c: f'<path fill="{c}" fill-rule="evenodd" transform="translate({x:.2f} {y:.2f}) scale({s:.5f})" d="{m["box"]}{m["check"]}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><style>.l{{display:none}}@media (prefers-color-scheme: light){{.d{{display:none}}.l{{display:inline}}}}</style>'
            f'<g class="d">{mark(DARK["accent"])}</g><g class="l">{mark(LIGHT["accent"])}</g></svg>')


def _viewbox(pad=12):
    x0, y0, x1, y1 = WM['bounds']
    return f'{x0 - pad:g} {y0 - pad:g} {x1 - x0 + 2 * pad:g} {y1 - y0 + 2 * pad:g}'


def wordmark_html():
    # The header's and footer's wordmark: the same shapes as the badges, in the page's theme colours, as tall as the font size
    # makes the capitals; the words stay in the page for screen readers and search.
    x0, y0, x1, y1 = WM['bounds']; h = (y1 - y0 + 24) / WM['cap']
    parts = ''.join(f'<g fill="var(--{p["role"]})" transform="translate({p["x"]:g} 0)">{p["g"]}</g>' for p in WM['parts'])
    return (f'<svg viewBox="{_viewbox()}" style="height:{h * .72:.3f}em" aria-hidden="true" focusable="false">{parts}</svg>'
            '<span class="vh">MXB Facts</span>')


def hero_html():
    # The home page's big wordmark. Its badge check is drawn as the box with the check masked out of it, so site.js can play it
    # once as the page opens: the box pops in, then the check is cut along its spine. Without the script, or with reduced motion,
    # it stays as drawn: the attributes hold the finished state and the animations only start when asked to. With motion on,
    # the page hides the box (.motion .mk) until site.js starts them, so it doesn't show finished first.
    m = WM['mark']; k = m['skew']; sp = 'M' + 'L'.join(f'{x:g} {y:g}' for x, y in m['spine'])
    cx, cy = m['w'] / 2 + k * WM['cap'] / 2, -WM['cap'] / 2  # the slanted box's centre, for the pop
    letters = ''.join(f'<g fill="var(--ink)" transform="translate({p["x"]:g} 0)">{p["g"]}</g>' for p in WM['parts'] if p['role'] == 'ink')
    check = (f'<path d="{sp}" transform="matrix(1 0 {-k:g} 1 0 0)" fill="none" stroke="#000" stroke-width="{m["stroke"]}" '
             f'stroke-linejoin="miter" stroke-miterlimit="8" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="0">'
             f'<animate attributeName="stroke-dashoffset" values="1;1;0" keyTimes="0;.4;1" dur=".7s" begin="indefinite" fill="freeze" '
             f'calcMode="spline" keySplines="0 0 1 1;.5 0 .2 1"/></path>')
    box = (f'<g transform="translate({cx:g} {cy:g})"><g><animateTransform attributeName="transform" type="scale" values="0;1.1;1" '
           f'keyTimes="0;.7;1" dur=".35s" begin="indefinite" fill="freeze"/><path fill="var(--accent)" '
           f'transform="translate({-cx:g} {-cy:g})" d="{m["box"]}"/></g></g>')
    return (f'<svg viewBox="{_viewbox()}" aria-hidden="true" focusable="false">{letters}'
            f'<g transform="translate({m["x"]:g} 0)"><mask id="hcheck" maskUnits="userSpaceOnUse" x="-100" y="-800" width="1000" height="900">'
            f'<rect x="-100" y="-800" width="1000" height="900" fill="#fff"/>{check}</mask><g class="mk" mask="url(#hcheck)">{box}</g></g></svg>')
