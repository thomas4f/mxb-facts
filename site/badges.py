"""The badges each card gets (rules/scores.md, "Badge"): four shields drawn the way shields.io draws them, a score tile and a
card with the area scores, as SVG, and the shields.io endpoint JSON. Drawn from a card's score result; they decide nothing.
"""
import json, math
from rules import AREAN, CONCERN, ROOT, RUBRICV, STATES, gsym, gtext
from icons import group as icon_group
from cards import esc
from brand import DARK, RED, figures, figures_width, wordmark, wordmark_width

# Badges (rules/scores.md, "Badge"): four shields in the shields.io styles (flat, plastic, flat-square, for-the-badge: same
# sizes, padding, font, label grey and, on flat and plastic, the same sheen and text shadow), so they sit with a README's other
# shields on a light or a dark page; a score tile and a card with the area scores, in the pit board's look like the card image.
# The shields' label is the MXB/FACTS wordmark in white, drawn as shapes so it looks the same on any page; the score is on the
# site's accent. The message text is sized from DejaVu Sans widths, the shields.io fallback for Verdana, and pinned with
# textLength so every viewer draws it the same width.
LABEL='#555'  # the shields.io label grey: readable on GitHub's light and dark themes alike
# The sheen shields.io lays over flat and plastic badges, as it draws them.
SHEEN={'flat':'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/>',
       'plastic':('<stop offset="0" stop-color="#fff" stop-opacity=".7"/><stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>'
                  '<stop offset=".9" stop-color="#000" stop-opacity=".3"/><stop offset="1" stop-color="#000" stop-opacity=".5"/>')}
GCOL={'score':DARK['accent'],'notscored':'#3d4a5c','malware':RED,'pending':'#3d4a5c'}  # red is for signs of malware alone
GINK={'score':DARK['accent-ink'],'notscored':'#fff','malware':'#fff','pending':'#fff'}  # the message's text on that colour
BW=json.load(open(ROOT+'site/badge-widths.json'))
def _tw(t,k):
    # As shields.io does: the text's width, rounded down, then up to an odd number of pixels.
    w=math.floor(sum(BW[k][ord(c)-32] if 32<=ord(c)<127 else BW[k][ord('m')-32] for c in t)); return w if w%2 else w+1
BFONT='Verdana,Geneva,DejaVu Sans,sans-serif'
BLABEL='MXB Facts'  # the wordmark's words, for titles and the shields.io label
PENDING={'kind':'pending'}  # a release the inventory has seen, with no card yet: the badge says so and scores nothing
def _gtext(G): return 'Not analysed yet' if G['kind']=='pending' else gtext(G)
def ptitle(name,ver): return f'{BLABEL}, {name} {ver}: not analysed yet. The badge shows the score once its card is published.'
def btitle(name,ver,G,date): return f'{BLABEL}, {name} {ver}: {gtext(G)} (rubric {RUBRICV}, analysed {date}). Worked out from the answers\' costs.'
def _n(x): return f'{x:g}'
def shield(style,G,title,uid):
    # style: flat, plastic, flat-square or for-the-badge, sized the way shields.io sizes them; the label side is the wordmark.
    # Flat and plastic carry shields.io's sheen and a 1 px text shadow (the wordmark's too); the square styles have neither.
    big=style=='for-the-badge'; plastic=style=='plastic'; shade=style in SHEEN; kind=G['kind']
    h=28 if big else 18 if plastic else 20; ty=175 if big else 130 if plastic else 140
    msg=_gtext(G).upper() if big else _gtext(G)
    cap=9 if big else 8; pad=12 if big else 6
    lw=round(wordmark_width(cap)+2*pad); mt=_tw(msg,'10b' if big else '11')+(1.25*len(msg) if big else 0); mw=mt+2*(12 if big else 5); w=lw+mw
    label=((f'<g fill-opacity=".3">{wordmark(pad,(h+cap)/2+1,cap,ink="#010101",accent="#010101")}</g>' if shade else '')
           +wordmark(pad,(h+cap)/2,cap,ink='#fff'))
    at=f'transform="scale(.1)" x="{_n((lw+mw/2)*10)}" textLength="{_n(mt*10)}"'+(' font-weight="bold"' if big else '')
    text=((f'<text aria-hidden="true" {at} y="{ty+10}" fill="#010101" fill-opacity=".3">{esc(msg)}</text>' if shade else '')
          +f'<text {at} y="{ty}">{esc(msg)}</text>')
    rects=f'<rect width="{_n(lw)}" height="{h}" fill="{LABEL}"/><rect x="{_n(lw)}" width="{_n(mw)}" height="{h}" fill="{GCOL[kind]}"/>'
    body=(f'<linearGradient id="s{uid}" x2="0" y2="100%">{SHEEN[style]}</linearGradient><clipPath id="r{uid}"><rect width="{_n(w)}" height="{h}" rx="{4 if plastic else 3}"/></clipPath>'
          f'<g clip-path="url(#r{uid})">{rects}<rect width="{_n(w)}" height="{h}" fill="url(#s{uid})"/></g>'
          if shade else f'<g shape-rendering="crispEdges">{rects}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_n(w)}" height="{h}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{body}{label}'
            f'<g fill="{GINK[kind]}" text-anchor="middle" font-family="{BFONT}" text-rendering="geometricPrecision" font-size="{100 if big else 110}">{text}</g></svg>')
def _tile(G,x,y,s):
    # The score square, as the tool page's big score: the score in the site's figures with a small "/100" on its baseline, the
    # slash in the accent and 100 in grey (or the icon for ? and X), the wordmark at the foot, on the pit board's dark (red for
    # signs of malware alone).
    kind=G['kind']; bg=RED if kind=='malware' else DARK['bg']
    if kind=='pending': big=(icon_group(STATES['nc'][2],x+s*.36,y+s*.1,s*.28,DARK['muted'])
                             +f'<text x="{x+s/2:g}" y="{y+s*.62:g}" text-anchor="middle" font-family="{BFONT}" font-size="{s*.1:g}" fill="{DARK["muted"]}">Not analysed yet</text>')
    elif kind in ('malware','notscored'): big=icon_group(STATES[kind][2],x+s*.32,y+s*.18,s*.36,DARK['ink'])
    else:
        n=gsym(G); cb,cs=s*.4,s*.13; gap=s*.015
        wn,ws,wh=figures_width(n,cb),figures_width('/',cs),figures_width('100',cs)
        k=min(1,s*.82/(wn+gap+ws+wh))  # a score of 100 is a digit wider: the whole score shrinks to keep its margins
        cb,cs,gap,wn,ws,wh=cb*k,cs*k,gap*k,wn*k,ws*k,wh*k
        x0=x+(s-(wn+gap+ws+wh))/2; yb=y+s*.62
        big=(figures(n,x0,yb,cb,DARK['ink'])+figures('/',x0+wn+gap,yb,cs,DARK['accent'])
             +figures('100',x0+wn+gap+ws,yb,cs,DARK['muted']))
    return (f'<rect x="{x+.5}" y="{y+.5}" width="{s-1}" height="{s-1}" rx="{s*.11:.1f}" fill="{bg}" stroke="{DARK["line"]}"/>'
            f'{big}{wordmark(x+(s-wordmark_width(s*.075))/2,y+s*.88,s*.075)}')
def badge_tile(G,title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{_tile(G,0,0,96)}</svg>'
def badge_areas(G,title):
    # The tile beside one bar per area, as on the tool's page; no area numbers when there is no score.
    nn=G['kind'] in ('notscored','malware','pending'); rows=''
    for i,ar in enumerate(x for x in AREAN if x in CONCERN):
        sc=0 if nn else G['areas'][ar][0]; y=13+i*20
        v='–' if nn else str(sc); fw=0 if nn else sc*.76
        rows+=(f'<text x="124" y="{y+4}" font-size="11" fill="{DARK["muted"]}">{esc(ar)}</text>{figures(v,270,y+5,9,DARK["ink"],"end")}'
               f'<rect x="278" y="{y-3}" width="76" height="6" rx="3" fill="{DARK["sunk"]}"/><rect x="278" y="{y-3}" width="{fw:.1f}" height="6" rx="3" fill="{DARK["accent"]}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="366" height="108" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<rect x=".5" y=".5" width="365" height="107" rx="10" fill="{DARK["surface"]}" stroke="{DARK["line"]}"/>{_tile(G,6,6,96)}<g font-family="{BFONT}">{rows}</g></svg>')
BADGES=[  # (file suffix, name shown to authors, how it is drawn)
    ('','Shield',lambda G,t,u:shield('flat',G,t,u)),
    ('-plastic','Shield, plastic',lambda G,t,u:shield('plastic',G,t,u)),
    ('-flat-square','Shield, square corners',lambda G,t,u:shield('flat-square',G,t,u)),
    ('-for-the-badge','Large shield',lambda G,t,u:shield('for-the-badge',G,t,u)),
    ('-score','Score',lambda G,t,u:badge_tile(G,t)),
    ('-areas','Score and areas',lambda G,t,u:badge_areas(G,t)),
]
def badge_json(ver,G):
    # The shields.io "endpoint" format, so shields.io can draw it in any of its styles, in the same colours.
    # The same words as the drawn shields: the label is the site's name alone (a version beside it reads as the site's own), and,
    # like them, the file is pinned to its release by its address.
    return json.dumps({'schemaVersion':1,'label':BLABEL,'message':_gtext(G),'color':GCOL[G['kind']].lstrip('#'),'labelColor':LABEL.lstrip('#')})
