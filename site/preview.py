"""The link-preview images (og:image): one for each card and one for the site, 1200 by 630, in the pit board's colours and fonts
(brand.py), so a link pasted into Discord or another chat app shows the tool's score and areas under the MXB/FACTS wordmark.
Drawn from the feed alone, like the pages; they decide nothing. Pillow reads the site's own woff2 fonts.
"""
import hashlib, io, re
from PIL import Image, ImageDraw, ImageFont
from brand import DARK, HERE, RED, WM

W, H, M = 1200, 630, 64  # size and margin
FONTS = HERE + 'static/fonts/'
_cache = {}


def font(name, size):
    k = (name, size)
    if k not in _cache: _cache[k] = ImageFont.truetype(FONTS + name + '.woff2', size, layout_engine=ImageFont.Layout.BASIC)
    return _cache[k]


BODY = 'barlow-latin-500-normal'; BOLD = 'barlow-latin-700-normal'; HEAD = 'barlow-condensed-latin-700-normal'; MARK = 'barlow-latin-800-italic'


def fit(d, text, name, size, width, least):
    # The largest size from size down to least that fits the width; past that, the text is cut with an ellipsis.
    while size > least and d.textlength(text, font=font(name, size)) > width: size -= 2
    f = font(name, size)
    if d.textlength(text, font=f) > width:
        while text and d.textlength(text + '…', font=f) > width: text = text[:-1]
        text = text.rstrip() + '…'
    return text, f


def wordmark(d, x, y, size):
    # MXB and FACTS in ink, the slash in the accent, as the header; y is the top of the capitals.
    f = font(MARK, size); top = f.getbbox('M')[1]
    for part, col in (('MXB', DARK['ink']), ('/', DARK['accent']), ('FACTS', DARK['ink'])):
        d.text((x, y - top), part, font=f, fill=col); x += d.textlength(part, font=f) - size * .01


def canvas():
    im = Image.new('RGB', (W, H), DARK['bg']); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 8), fill=DARK['accent'])
    return im, d


def png(im):
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True); data = b.getvalue()
    return data, hashlib.sha256(data).hexdigest()[:10]


def card_image(c, IX):
    # A card: wordmark and site address, the tool's name, what it is, the big score, a box per area with its bar, and the AI note.
    im, d = canvas(); r = c['result']; muted = DARK['muted']
    wordmark(d, M, 52, 34)
    addr = IX['site'].split('://', 1)[1].rstrip('/'); f = font(BODY, 22)
    d.text((W - M - d.textlength(addr, font=f), 52), addr, font=f, fill=muted)
    # The score box, top right, as on the tool page.
    bx = (W - M - 250, 104, W - M, 322)
    d.rounded_rectangle(bx, 18, fill=DARK['surface'], outline=RED if r['kind'] == 'malware' else DARK['line'], width=2)
    cx = (bx[0] + bx[2]) / 2
    if r['kind'] == 'score':
        big = f'{r["score"]:g}'; fs = 150 if len(big) <= 3 else 112
        d.text((cx, 240), big, font=font(HEAD, fs), fill=DARK['ink'], anchor='ms')
        d.text((cx, 290), 'out of 100', font=font(BODY, 24), fill=muted, anchor='ms')
    else:
        words = 'Signs of malware' if r['kind'] == 'malware' else 'Not scored'
        t, f = fit(d, words, HEAD, 56, 220, 34)
        d.text((cx, 232), t, font=f, fill=RED if r['kind'] == 'malware' else DARK['ink'], anchor='ms')
    # Name and what it is, left of the box.
    lw = bx[0] - M - 40
    name, f = fit(d, c['name'], HEAD, 96, lw, 60); d.text((M, 206), name, font=f, fill=DARK['ink'], anchor='ls')
    ver, f = fit(d, 'version ' + c['version'], BOLD, 30, lw, 22); d.text((M, 254), ver, font=f, fill=DARK['accent'], anchor='ls')
    meta, f = fit(d, f'{" + ".join(c["games"])} · {c["category"]} · analysed {c["analysed"]}', BODY, 26, lw, 20)
    d.text((M, 298), meta, font=f, fill=muted, anchor='ls')
    # One box per area, the Money label last, as on the tool page: three to a row, so they stay readable at chat-app sizes.
    areas = IX['areas']; gap = 14; cols = 3; bw = (W - 2 * M - gap * (cols - 1)) / cols; bh = 88
    ls = 26  # one size for every area's name: the largest at which the longest fits beside its value
    while ls > 18 and max(d.textlength(a['name'], font=font(BODY, ls)) for a in areas) > bw - 130: ls -= 1
    for i, a in enumerate(areas):
        x0 = M + (i % cols) * (bw + gap); y0 = 352 + (i // cols) * (bh + gap)
        d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 14, fill=DARK['surface'], outline=DARK['line'], width=2)
        d.text((x0 + 20, y0 + 50), a['name'], font=font(BODY, ls), fill=muted, anchor='ls')
        v = r['areas'].get(a['id']) if a['scored'] else r['money']
        vt = '–' if v is None else f'{v:g}' if a['scored'] else v
        t, f = fit(d, vt, HEAD, 48, 140, 30); d.text((x0 + bw - 20, y0 + 54), t, font=f, fill=DARK['ink'], anchor='rs')
        if a['scored']:
            d.rounded_rectangle((x0 + 20, y0 + 66, x0 + bw - 20, y0 + 74), 4, fill=DARK['sunk'])
            if v: d.rounded_rectangle((x0 + 20, y0 + 66, x0 + 20 + (bw - 40) * v / 100, y0 + 74), 4, fill=DARK['accent'])
    t, f = fit(d, 'Every answer links its evidence. Made by AI from a public prompt; no person checks each answer.', BODY, 22, W - 2 * M, 18)
    d.text((M, 600), t, font=f, fill=muted, anchor='ls')
    return png(im)


def _outline(d, steps=6):
    # A brand.json path (M, L, H, V, Q and Z only, as tools/wordmark.py writes them) as one polygon's points.
    pts = []; x = y = 0.0
    tok = re.findall(r'[MLHVQZ]|-?[0-9.]+', d); i = 0; cmd = None
    while i < len(tok):
        if tok[i].isalpha(): cmd = tok[i]; i += 1
        if cmd == 'Z': continue
        n = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'Q': 4}[cmd]; a = [float(v) for v in tok[i:i + n]]; i += n
        if cmd in 'ML': x, y = a
        elif cmd == 'H': x = a[0]
        elif cmd == 'V': y = a[0]
        else:
            cx, cy, ex, ey = a
            for k in range(1, steps + 1):
                t = k / steps; pts.append(((1 - t) ** 2 * x + 2 * (1 - t) * t * cx + t * t * ex, (1 - t) ** 2 * y + 2 * (1 - t) * t * cy + t * t * ey))
            x, y = ex, ey; continue
        pts.append((x, y))
    return pts


def touch_icon(size=180):
    # The favicon as a PNG for phones' home screens (apple-touch-icon): the slash on the pit board, square, as the phone rounds it.
    im = Image.new('RGB', (size, size), DARK['bg']); d = ImageDraw.Draw(im)
    path = re.search(r' d="([^"]+)"', WM['parts'][1]['g']).group(1)
    s = .074 * size / 64 * .82; ox = size / 2 - 254 * s; oy = size / 2 + 350 * s
    d.polygon([(ox + px * s, oy + py * s) for px, py in _outline(path)], fill=DARK['accent'])
    return png(im)[0]


def site_image(IX):
    # The site: the wordmark large, what it answers, and how many tools have a card.
    im, d = canvas(); muted = DARK['muted']
    wordmark(d, M, 78, 64)
    f = font(HEAD, 96)  # the home page's heading, its last word in the accent
    d.text((M, 270), 'What MX Bikes and GP Bikes', font=f, fill=DARK['ink'], anchor='ls')
    d.text((M, 368), 'tools ', font=f, fill=DARK['ink'], anchor='ls')
    d.text((M + d.textlength('tools ', font=f), 368), 'do', font=f, fill=DARK['accent'], anchor='ls')
    n = len(IX['tools']); f = font(BODY, 30)
    d.text((M, 450), f'{n} plugins, apps and mods · the same questions for every tool', font=f, fill=DARK['ink'], anchor='ls')
    d.text((M, 494), 'Every answer links its evidence: code, files, or a test anyone can repeat.', font=f, fill=muted, anchor='ls')
    addr = IX['site'].split('://', 1)[1].rstrip('/'); f = font(BODY, 24)
    d.text((M, 572), addr, font=f, fill=muted, anchor='ls')
    return png(im)
