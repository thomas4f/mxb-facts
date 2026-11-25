"""The badges each card gets (rules/scores.md, "Badge"): three shields drawn the way shields.io draws them, a score tile and a
card with the area scores, as SVG, and the shields.io endpoint JSON. Drawn from a card's score result; they decide nothing.
"""
import json, math
from rules import AREAN, CONCERN, ROOT, RUBRICV, STATES, gsym, gtext
from icons import group as icon_group
from cards import esc

GCOL={'score':'#3d4a5c','notscored':'#3d4a5c','malware':'#cf222e'}  # red is for signs of malware alone
# Badges (rules/scores.md, "Badge"): three shields in the shields.io styles (flat, flat-square, for-the-badge: same sizes,
# padding, font and text shadow), a score tile, and a card with the area scores. Text is sized from DejaVu Sans widths, the
# shields.io fallback for Verdana, and pinned with textLength so every viewer draws it the same width.
SITEURL='https://thomas4f.github.io/mxb-facts/'
BW=json.load(open(ROOT+'site/badge-widths.json'))
def _tw(t,k):
    # As shields.io does: the text's width, rounded down, then up to an odd number of pixels.
    w=math.floor(sum(BW[k][ord(c)-32] if 32<=ord(c)<127 else BW[k][ord('m')-32] for c in t)); return w if w%2 else w+1
BFONT='Verdana,Geneva,DejaVu Sans,sans-serif'
BLABEL='MXB Facts'
def btitle(name,ver,G,date): return f'{BLABEL}, {name} {ver}: {gtext(G)} (rubric {RUBRICV}, analysed {date}). Worked out from the answers\' costs.'
def _n(x): return f'{x:g}'
def shield(style,msg,color,title,uid):
    # style: flat, flat-square or for-the-badge, drawn the way shields.io draws them (sizes, padding, fonts, shadow).
    big=style=='for-the-badge'; h=28 if big else 20
    lab,msg=(BLABEL.upper(),msg.upper()) if big else (BLABEL,msg)
    lt=_tw(lab,'10' if big else '11')+(1.25*len(lab) if big else 0); mt=_tw(msg,'10b' if big else '11')+(1.25*len(msg) if big else 0)
    pad=12 if big else 5; lw=lt+2*pad; mw=mt+2*pad; w=lw+mw
    if big:
        texts=(f'<text transform="scale(.1)" x="{_n(lw*5)}" y="175" textLength="{_n(lt*10)}">{esc(lab)}</text>'
               f'<text transform="scale(.1)" x="{_n((lw+mw/2)*10)}" y="175" textLength="{_n(mt*10)}" font-weight="bold">{esc(msg)}</text>')
    else:
        def one(t,x,tl): return (f'<g transform="scale(.1)"><g aria-hidden="true" fill="#010101"><text x="{_n(x*10)}" y="150" fill-opacity=".8" filter="url(#b{uid})" textLength="{_n(tl*10)}">{esc(t)}</text>'
                                 f'<text x="{_n(x*10)}" y="150" fill-opacity=".3" textLength="{_n(tl*10)}">{esc(t)}</text></g>'
                                 f'<text x="{_n(x*10)}" y="140" textLength="{_n(tl*10)}">{esc(t)}</text></g>')
        def flat(t,x,tl): return f'<text x="{_n(x*10)}" y="140" textLength="{_n(tl*10)}" transform="scale(.1)">{esc(t)}</text>'
        if style=='flat-square': one=flat  # no shadow
        texts=one(lab,lw/2+1,lt)+one(msg,lw+mw/2-1,mt)  # shields.io moves each text 1px toward the middle
    rects=f'<rect width="{_n(lw)}" height="{h}" fill="#555"/><rect x="{_n(lw)}" width="{_n(mw)}" height="{h}" fill="{color}"/>'
    body=(f'<filter id="b{uid}"><feGaussianBlur stdDeviation="16"/></filter><linearGradient id="s{uid}" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>'
          f'<clipPath id="r{uid}"><rect width="{_n(w)}" height="{h}" rx="3"/></clipPath><g clip-path="url(#r{uid})">{rects}<rect width="{_n(w)}" height="{h}" fill="url(#s{uid})"/></g>'
          if style=='flat' else f'<g shape-rendering="crispEdges">{rects}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_n(w)}" height="{h}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{body}'
            f'<g fill="#fff" text-anchor="middle" font-family="{BFONT}" text-rendering="geometricPrecision" font-size="{100 if big else 110}">{texts}</g></svg>')
def _tile(G,x,y,s):
    # The score square, as on the site: the score (or ? / X), "/100" under it, the site's name at the foot.
    sym=gsym(G); sub='/100' if G['kind']=='score' else ''
    # Signs of malware and Not scored draw their icon (STATES in rules.py) in place of a number.
    big=(icon_group(STATES[G['kind']][2],x+s*.32,y+s*.2,s*.36,'#fff') if G['kind'] in ('malware','notscored') else
         f'<text x="{x+s/2}" y="{y+s*.5}" font-size="{s*.36:.0f}" font-weight="bold">{esc(sym)}</text>')
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="6" fill="{GCOL[G["kind"]]}"/><g fill="#fff" text-anchor="middle" font-family="{BFONT}">'
            f'{big}<text x="{x+s/2}" y="{y+s*.68}" font-size="{s*.13:.0f}" fill-opacity=".85">{sub}</text>'
            f'<text x="{x+s/2}" y="{y+s*.9}" font-size="{s*.085:.1f}" fill-opacity=".8" letter-spacing=".4">{BLABEL.upper()}</text></g>')
def badge_tile(G,title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{_tile(G,0,0,96)}</svg>'
def badge_areas(G,title):
    # The tile beside one bar per area, as in the Score card on the tool's page; no area numbers when there is no score.
    nn=G['kind'] in ('notscored','malware'); rows=''
    for i,ar in enumerate(x for x in AREAN if x in CONCERN):
        sc=G['areas'][ar][0]; y=13+i*20
        v='–' if nn else str(sc); fw=0 if nn else sc*.76
        rows+=(f'<text x="124" y="{y+4}" font-size="11" fill="#1d2330">{esc(ar)}</text><text x="270" y="{y+4}" font-size="11" font-weight="bold" fill="#1d2330" text-anchor="end">{v}</text>'
               f'<rect x="278" y="{y-3}" width="76" height="6" rx="3" fill="#e3e6eb"/><rect x="278" y="{y-3}" width="{fw:.1f}" height="6" rx="3" fill="#5d6878"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="366" height="108" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<rect x=".5" y=".5" width="365" height="107" rx="8" fill="#fff" stroke="#d0d5dd"/>{_tile(G,6,6,96)}<g font-family="{BFONT}">{rows}</g></svg>')
BADGES=[  # (file suffix, name shown to authors, how it is drawn)
    ('','Shield',lambda G,t,u:shield('flat',gtext(G),GCOL[G['kind']],t,u)),
    ('-flat-square','Shield, square corners',lambda G,t,u:shield('flat-square',gtext(G),GCOL[G['kind']],t,u)),
    ('-for-the-badge','Large shield',lambda G,t,u:shield('for-the-badge',gtext(G),GCOL[G['kind']],t,u)),
    ('-score','Score',lambda G,t,u:badge_tile(G,t)),
    ('-areas','Score and areas',lambda G,t,u:badge_areas(G,t)),
]
def badge_json(ver,G):
    # The shields.io "endpoint" format, so shields.io can draw it in any of its styles.
    return json.dumps({'schemaVersion':1,'label':BLABEL,'message':gtext(G),'color':GCOL[G['kind']].lstrip('#')})
