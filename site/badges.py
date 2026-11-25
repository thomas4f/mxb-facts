"""The badges each card gets (rules/scores.md, "Badge"): three shields drawn the way shields.io draws them, a score tile and a
card with the area scores, as SVG, and the shields.io endpoint JSON. Drawn from a card's score result; they decide nothing.
"""
import json, math
from rules import AREAN, CONCERN, ROOT, RUBRICV, STATES, gsym, gtext
from icons import group as icon_group
from cards import esc
from brand import DARK, RED, figures, wordmark, wordmark_width

# Badges (rules/scores.md, "Badge"): three shields in the shields.io styles (flat, flat-square, for-the-badge: same sizes,
# padding and font), a score tile, and a card with the area scores. They carry the site's identity (brand.py): the MXB/FACTS
# wordmark on the pit board's dark, the score on its accent, both drawn as shapes so they look the same on any page. The
# message text is sized from DejaVu Sans widths, the shields.io fallback for Verdana, and pinned with textLength so every
# viewer draws it the same width.
GCOL={'score':DARK['accent'],'notscored':'#3d4a5c','malware':RED}  # red is for signs of malware alone
GINK={'score':DARK['accent-ink'],'notscored':'#fff','malware':'#fff'}  # the message's text on that colour
BW=json.load(open(ROOT+'site/badge-widths.json'))
def _tw(t,k):
    # As shields.io does: the text's width, rounded down, then up to an odd number of pixels.
    w=math.floor(sum(BW[k][ord(c)-32] if 32<=ord(c)<127 else BW[k][ord('m')-32] for c in t)); return w if w%2 else w+1
BFONT='Verdana,Geneva,DejaVu Sans,sans-serif'
BLABEL='MXB Facts'  # the wordmark's words, for titles and the shields.io label
def btitle(name,ver,G,date): return f'{BLABEL}, {name} {ver}: {gtext(G)} (rubric {RUBRICV}, analysed {date}). Worked out from the answers\' costs.'
def _n(x): return f'{x:g}'
def shield(style,G,title,uid):
    # style: flat, flat-square or for-the-badge, sized the way shields.io sizes them; the label side is the wordmark.
    big=style=='for-the-badge'; h=28 if big else 20; kind=G['kind']
    msg=gtext(G).upper() if big else gtext(G)
    cap=9 if big else 8; pad=12 if big else 6
    lw=round(wordmark_width(cap)+2*pad); mt=_tw(msg,'10b' if big else '11')+(1.25*len(msg) if big else 0); mw=mt+2*(12 if big else 5); w=lw+mw
    label=wordmark(pad,(h+cap)/2,cap)
    text=(f'<text transform="scale(.1)" x="{_n((lw+mw/2)*10)}" y="{175 if big else 140}" textLength="{_n(mt*10)}"'
          f'{" font-weight=" + chr(34) + "bold" + chr(34) if big else ""}>{esc(msg)}</text>')
    rects=f'<rect width="{_n(lw)}" height="{h}" fill="{DARK["bg"]}"/><rect x="{_n(lw)}" width="{_n(mw)}" height="{h}" fill="{GCOL[kind]}"/>'
    body=(f'<clipPath id="r{uid}"><rect width="{_n(w)}" height="{h}" rx="3"/></clipPath><g clip-path="url(#r{uid})">{rects}</g>'
          if style=='flat' else f'<g shape-rendering="crispEdges">{rects}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_n(w)}" height="{h}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{body}{label}'
            f'<g fill="{GINK[kind]}" text-anchor="middle" font-family="{BFONT}" text-rendering="geometricPrecision" font-size="{100 if big else 110}">{text}</g></svg>')
def _tile(G,x,y,s):
    # The score square, as the tool page's big score: the score in the site's figures (or the icon for ? and X), "/100" under
    # it, the wordmark at the foot, on the pit board's dark (red for signs of malware alone).
    kind=G['kind']; bg=RED if kind=='malware' else DARK['bg']
    big=(icon_group(STATES[kind][2],x+s*.32,y+s*.14,s*.36,DARK['ink']) if kind in ('malware','notscored') else
         figures(gsym(G),x+s/2,y+s*.5,s*.36,DARK['ink'],'middle'))
    sub=figures('/100',x+s/2,y+s*.68,s*.1,DARK['muted'],'middle') if kind=='score' else ''
    return (f'<rect x="{x+.5}" y="{y+.5}" width="{s-1}" height="{s-1}" rx="{s*.11:.1f}" fill="{bg}" stroke="{DARK["line"]}"/>'
            f'<rect x="{x+s*.3:.1f}" y="{y+s*.76:.1f}" width="{s*.4:.1f}" height="{max(1.5,s*.02):.1f}" fill="{DARK["accent"]}"/>'
            f'{big}{sub}{wordmark(x+(s-wordmark_width(s*.075))/2,y+s*.92,s*.075)}')
def badge_tile(G,title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{_tile(G,0,0,96)}</svg>'
def badge_areas(G,title):
    # The tile beside one bar per area, as on the tool's page; no area numbers when there is no score.
    nn=G['kind'] in ('notscored','malware'); rows=''
    for i,ar in enumerate(x for x in AREAN if x in CONCERN):
        sc=G['areas'][ar][0]; y=13+i*20
        v='–' if nn else str(sc); fw=0 if nn else sc*.76
        rows+=(f'<text x="124" y="{y+4}" font-size="11" fill="{DARK["muted"]}">{esc(ar)}</text>{figures(v,270,y+5,9,DARK["ink"],"end")}'
               f'<rect x="278" y="{y-3}" width="76" height="6" rx="3" fill="{DARK["sunk"]}"/><rect x="278" y="{y-3}" width="{fw:.1f}" height="6" rx="3" fill="{DARK["accent"]}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="366" height="108" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<rect x=".5" y=".5" width="365" height="107" rx="10" fill="{DARK["surface"]}" stroke="{DARK["line"]}"/>{_tile(G,6,6,96)}<g font-family="{BFONT}">{rows}</g></svg>')
BADGES=[  # (file suffix, name shown to authors, how it is drawn)
    ('','Shield',lambda G,t,u:shield('flat',G,t,u)),
    ('-flat-square','Shield, square corners',lambda G,t,u:shield('flat-square',G,t,u)),
    ('-for-the-badge','Large shield',lambda G,t,u:shield('for-the-badge',G,t,u)),
    ('-score','Score',lambda G,t,u:badge_tile(G,t)),
    ('-areas','Score and areas',lambda G,t,u:badge_areas(G,t)),
]
def badge_json(ver,G):
    # The shields.io "endpoint" format, so shields.io can draw it in any of its styles, in the same colours.
    return json.dumps({'schemaVersion':1,'label':BLABEL,'message':gtext(G),'color':GCOL[G['kind']].lstrip('#'),'labelColor':DARK['bg'].lstrip('#')})
