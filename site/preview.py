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
    return im, d


def png(im):
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True); data = b.getvalue()
    return data, hashlib.sha256(data).hexdigest()[:10]


def plain(md):
    # A text field from site.json as an image shows it: links dropped with their words, the rest kept.
    return re.sub(r'\s*\[[^\]]*\]\([^)]*\)', '', md).strip()

def wrap(d, text, f, width):
    # Words into lines no wider than width.
    lines = ['']
    for w in text.split():
        t = (lines[-1] + ' ' + w).strip()
        if lines[-1] and d.textlength(t, font=f) > width: lines.append(w)
        else: lines[-1] = t
    return lines

def card_image(c, IX, SITE, newer=(), pending=None):
    # A card, laid out as its page's header: wordmark and site address, the path, the name, the big score, a box per area with
    # its bar, and the AI note. newer: releases newer than this card that have none yet (the tool's newest-card image says so).
    # pending: such a release's own image, drawn from the tool's newest card c with no score at all, as its badges are.
    im, d = canvas(); muted = DARK['muted']
    r = {'kind': 'pending', 'areas': {}, 'money': None} if pending else c['result']
    wordmark(d, M, 52, 34)
    addr = IX['site'].split('://', 1)[1].rstrip('/'); f = font(BODY, 22)
    d.text((W - M - d.textlength(addr, font=f), 52), addr, font=f, fill=muted)
    # The header as on the tool page: the path (games / category) in small capitals, the name with its version beside it in
    # grey, who made it and when it was analysed, and the score large on the right, the slash in the accent and 100 in grey.
    if r['kind'] == 'score':
        big = f'{r["score"]:g}'; fb = font(HEAD, 200); fo = font(HEAD, 60)
        sl, hund = '/', '100'
        wr = d.textlength(sl, font=fo) + d.textlength(hund, font=fo)
        xr = W - M - wr; ink = fb.getbbox(big, anchor='ls')  # the digits' ink, so the slash sits close as on the page
        bw0 = ink[2] - ink[0]
        d.text((xr - ink[2], 300), big, font=fb, fill=DARK['ink'], anchor='ls')
        xs = xr - fo.getbbox(sl, anchor='ls')[0]  # the slash's ink, not its box, meets the digits
        d.text((xs, 300), sl, font=fo, fill=DARK['accent'], anchor='ls')
        d.text((xs + d.textlength(sl, font=fo), 300), hund, font=fo, fill=muted, anchor='ls')
        left = xr - bw0
    else:
        words = {'malware': 'Signs of malware', 'pending': 'Not analysed yet'}.get(r['kind'], 'Not scored')
        t, f = fit(d, words, HEAD, 64, 300, 40)
        d.text((W - M, 230), t, font=f, fill=RED if r['kind'] == 'malware' else muted, anchor='rs')
        left = W - M - d.textlength(t, font=f)
    lw = left - M - 40
    path = f'{" + ".join(c["games"])} / {c["category"]}'.upper()
    fp = font(HEAD, 26); x = M
    for k, part in enumerate(path.split(' / ')):
        if k: d.text((x + 6, 150), '/', font=fp, fill=DARK['accent'], anchor='ls'); x += d.textlength('/', font=fp) + 12
        t, _ = fit(d, part, HEAD, 26, max(lw - (x - M), 40), 26); d.text((x, 150), t, font=fp, fill=muted, anchor='ls'); x += d.textlength(t, font=fp)
    name, f = fit(d, c['name'], HEAD, 96, lw - 120, 56); d.text((M, 240), name, font=f, fill=DARK['ink'], anchor='ls')
    vt, fv = fit(d, pending or c['version'], HEAD, 44, max(lw - d.textlength(name, font=f) - 16, 60), 28)
    d.text((M + d.textlength(name, font=f) + 16, 240), vt, font=fv, fill=muted, anchor='ls')
    meta = f'by {c["author"]} · ' + (f'the newest card is for {c["version"]}' if pending else f'analysed {c["analysed"]}')
    meta, f = fit(d, meta, BODY, 26, lw, 20)
    d.text((M, 292), meta, font=f, fill=muted, anchor='ls')
    if newer:  # in the accent, under the name, so a stable image never reads as the newest release's result
        t, f = fit(d, f'{", ".join(newer)}: newer, not analysed yet', BOLD, 24, lw, 18)
        d.text((M, 330), t, font=f, fill=DARK['accent'], anchor='ls')
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
    t, f = fit(d, 'Made by AI. ' + plain(SITE['ai_short']), BODY, 22, W - 2 * M, 18)  # the home page's AI note
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


def site_image(IX, SITE):
    # The site, as the home page opens: the wordmark, its heading, its intro and how many tools have a card.
    im, d = canvas(); muted = DARK['muted']
    wordmark(d, M, 78, 64)
    size = 132  # the home page's heading, its last word in the accent, as large as fits the width
    while size > 96 and d.textlength(SITE['heading'], font=font(HEAD, size)) > W - 2 * M: size -= 2
    f = font(HEAD, size)
    assert d.textlength(SITE['heading'], font=f) <= W - 2 * M, 'preview.py: the home heading is too wide for the site image'
    a, b = SITE['heading'].split(SITE['heading_accent'], 1); x = M
    for t, col in ((a, DARK['ink']), (SITE['heading_accent'], DARK['accent']), (b, DARK['ink'])):
        d.text((x, 280), t, font=f, fill=col, anchor='ls'); x += d.textlength(t, font=f)
    f = font(BODY, 32); lines = wrap(d, plain(SITE['lede']), f, W - 2 * M)
    assert len(lines) <= 3, 'preview.py: the home intro needs more than three lines on the site image'
    for i, t in enumerate(lines): d.text((M, 370 + 44 * i), t, font=f, fill=DARK['ink'], anchor='ls')
    addr = IX['site'].split('://', 1)[1].rstrip('/'); f = font(BODY, 24)
    d.text((M, 572), f"{len(IX['tools'])} tools · {addr}", font=f, fill=muted, anchor='ls')  # the home page's count
    return png(im)
