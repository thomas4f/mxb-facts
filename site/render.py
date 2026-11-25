"""The site's pages, made from the data feed alone (api/v1/: index.json, site.json, cards/<card>.json) with the templates in
site/templates/ and the files in site/static/. Nothing here reads a card, the rules or scoring.yaml: every mark, cost, score and
word the pages show is in the feed, so the site, MXB App and a mods site all show the same thing, and a page can't know
something the feed doesn't say.

Usage: from build.py, write_pages(SITE) after the feed is written.
"""
import json, os, re, shutil
import markdown
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup, escape
from icons import LICENCE as ICON_LICENCE, mask_url
from brand import DARK, favicon
from preview import card_image, site_image

HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
# The pages a tool's id can't take, since the site uses them for its own folders.
FOLDERS = {'api', 'assets', 'authors', 'badge', 'cards', 'compare', 'how'}
# A mark's words: a marked answer shows its verdict (Yes, No, Partly ...), every other state its label.
VERDICT_STATES = ('good', 'note', 'concern', 'major', 'malware')


class _NoHTML(markdown.Extension):
    # Raw HTML in Markdown is shown as text, never kept: card text holds none (cards.no_html), and this keeps it that way on the page.
    def extendMarkdown(self, md):
        md.preprocessors.deregister('html_block')
        md.inlinePatterns.deregister('html')


_MD = markdown.Markdown(extensions=['tables', 'fenced_code', _NoHTML()])


def _post(h):
    # Links to other sites open in a new tab; a table scrolls on its own on a phone and names what its headers head.
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', h)
    h = re.sub(r'<th(?=[ >])(?![^>]*scope)', '<th scope="col"', h)
    return h.replace('<table>', '<div class="tw"><table class="t">').replace('</table>', '</table></div>')


def md(text):
    _MD.reset()
    return Markup(_post(_MD.convert(text or '')))


def mdi(text):
    # One line of Markdown, without the paragraph around it.
    return Markup(re.sub(r'^<p>|</p>$', '', str(md(text)).strip()))


def complete(c, html):
    # Nothing on a card goes missing on its page: every answer and every "Says vs does" claim is a row with its mark, every key
    # answer has its mark, and the page shows each area, limit, file and history row. A section a template forgets fails here,
    # not in front of a reader.
    # Each row's marks line (the row macro: id, question, then <div class="v">), read row by row so one row can't borrow another's mark.
    rows = re.findall(r'<div class="row" id="([^"]+)">\s*<span class="id">[^<]*</span>\s*<div class="rb">\s*<div class="q">.*?</div>\s*<div class="v">(.*?)</div>', html, re.S)
    marked = {i for i, v in rows if 'class="st ' in v}
    claims = sum(len(b['rows']) for s in c['sections'] if s['title'] == 'What it says vs what it does' for b in s['blocks'] if 'Verdict' in b.get('table', []))
    want = {'q-' + x['id'] for x in c['answers']} | {f'claim-{n}' for n in range(1, claims + 1)}
    assert want <= marked, c['card'] + ': rows without their mark on the page: ' + ', '.join(sorted(want - marked))
    keys = re.findall(r'<div class="key"><div class="hd">.*?</div>', html, re.S)
    assert len(keys) == len(c['key_answers']) and all('class="st ' in k for k in keys), c['card'] + ': a key answer without its mark'
    lims = sum(len(b['limits']) for s in c['sections'] if s['title'] == 'Limits of this analysis' for b in s['blocks'])
    for what, n, pat in (('areas', len(c['areas']), r'<details class="fold" id="a-'), ('limits', lims, r'<li id="lim-'),
                         ('files', len(c['files']), r'<code class="hash">'), ('history rows', len(c['history']), r'<td class="nowrap">')):
        assert len(re.findall(pat, html)) == n, f'{c["card"]}: the page shows {len(re.findall(pat, html))} {what}, the card has {n}'


def write_pages(SITE):
    feed = SITE + 'api/v1/'
    IX = json.load(open(feed + 'index.json'))
    SITEJ = json.load(open(feed + 'site.json'))
    CARDS = {f[:-5]: json.load(open(feed + 'cards/' + f)) for f in sorted(os.listdir(feed + 'cards'))}
    STATES = {s['id']: s for s in IX['states']}
    AREAS = IX['areas']
    assert not FOLDERS & {t['id'] for t in IX['tools']}, 'a tool id is also a folder name of the site: ' + ', '.join(FOLDERS & {t['id'] for t in IX['tools']})

    env = Environment(loader=FileSystemLoader(HERE + 'templates'), autoescape=select_autoescape(['html']), undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(md=md, mdi=mdi)

    def mark(state, words=None, cost=None, tip=None):
        # One mark: the state's colour and icon, and its words. The state always comes from the feed; nothing is mapped here.
        s = STATES[state]
        c = Markup(f' <span class="c">{escape(cost)}</span>') if cost else ''
        return Markup(f'<span class="st {state}" title="{escape(tip or s["label"] + ": " + s["meaning"])}">{escape(words or s["label"])}{c}</span>')

    def answer_mark(x, scored):
        # An answer's mark: its state's word in its colour, with what it costs where the tool has a score ("Concern −25", or
        # "±0" when another answer counts it), then the verdict itself ("Yes"). The word is text, never only a colour or icon.
        cost = None
        if scored and x['cost']: cost = f'−{x["cost"]}'
        elif scored and x['cost_note']: cost = '±0'
        pill = mark(x['state'], None, cost, x['cost_note'] or None)
        return pill + Markup(f' <b class="vd">{escape(x["verdict"])}</b>') if x['state'] in VERDICT_STATES else pill

    def tag(t, hidden=False, base=''):
        # A tag is text and colour only (40 kinds: too many shapes to learn; the marks keep their icons). It links to the answer it comes from: on its own page (#q-ID), or on the tool's page from the tools list (base).
        cls = 'concern major' if t['kind'] == 'concern' and t.get('major') else t['kind']
        tip = f'From {t["question"]}' + (', only after a choice you make' if t['kind'] == 'off_by_default' else '')
        return Markup(f'<a class="tag {cls}" href="{base}#q-{t["question"]}" title="{escape(tip)}"{" hidden" if hidden else ""}>{escape(t["label"])}</a>')

    env.globals.update(DARK=DARK, mark=mark, answer_mark=answer_mark, tag=tag, IX=IX, SITE=SITEJ, STATES=STATES, AREAS=AREAS,
                       area_name={a['id']: a['name'] for a in AREAS}, money={m['label']: m for m in IX['money']})

    out = SITE
    def page(path, tpl, depth, **kw):
        os.makedirs(os.path.dirname(out + path), exist_ok=True)
        html = env.get_template(tpl).render(root='../' * depth, path=path, **kw)
        # Every in-page link lands on an id that exists, once (the contents, tags, limits, "From" links).
        ids = re.findall(r'\bid="([^"]+)"', html)
        assert len(ids) == len(set(ids)), path + ': two elements share an id: ' + ', '.join(sorted({i for i in ids if ids.count(i) > 1}))
        # No markup reaches a page as text: a tag escaped by the templates' autoescape means a string was pasted into HTML.
        esc_tags = sorted(set(re.findall(r'&lt;/?(?:span|a|b|i|em|strong|code|div|p|br)\b', html)))
        assert not esc_tags, path + ': markup shown as text (' + ', '.join(esc_tags) + '); pass markup from a template block, text through note='
        dead = sorted(set(re.findall(r'href="#([^"]+)"', html)) - set(ids))
        assert not dead, path + ': links to anchors that don\'t exist: ' + ', '.join(dead)
        open(out + path, 'w').write(html.rstrip() + '\n')
        return html

    def card_path(c):
        return f'{c["tool"]}/' if c['latest'] else f'{c["tool"]}/{c["version"]}/'

    # Where each card lives, so a link to a card file id (an old "#<card>" or "#<tool>" address included) finds its page.
    addr = {cid: card_path(c) for cid, c in CARDS.items()}
    addr.update({t['id']: t['id'] + '/' for t in IX['tools']})

    # The link-preview images (preview.py): one per card and one for the site, named with their content's hash so a chat app
    # that cached an older image fetches the new one.
    os.makedirs(out + 'preview', exist_ok=True)
    def image(name, data_hash):
        data, h = data_hash
        open(out + f'preview/{name}.png', 'wb').write(data)
        return f'{IX["site"]}preview/{name}.png?v={h}'
    env.globals['og_image'] = image('site', site_image(IX))

    page('index.html', 'home.html', 0, addresses=addr)
    for t in IX['tools']:
        for r in t['releases']:
            c = CARDS[r['card']]
            complete(c, page(card_path(c) + 'index.html', 'tool.html', card_path(c).count('/'), t=t, c=c, card_image=image(c['card'], card_image(c, IX))))
    page('compare/index.html', 'compare.html', 1, cards=[CARDS[r['card']] for t in IX['tools'] for r in t['releases']])
    page('how/index.html', 'how.html', 1)
    page('authors/index.html', 'authors.html', 1)

    # The static files, and the CSS made from the feed's states and tags: each state's and tag's icon as a mask, so it takes the mark's colour.
    os.makedirs(out + 'assets', exist_ok=True)
    for f in os.listdir(HERE + 'static'):
        src = HERE + 'static/' + f
        if os.path.isdir(src): shutil.copytree(src, out + 'assets/' + f, dirs_exist_ok=True)
        else: shutil.copyfile(src, out + 'assets/' + f)
    icon = {k: s['icon'] for k, s in STATES.items()}
    css = ['/* Made by site/render.py from the feed: one icon per state (Lucide, ISC licence, see the end of this file). */']
    css += [f'.st.{k}::before {{ -webkit-mask-image: {mask_url(v)}; mask-image: {mask_url(v)} }}' for k, v in icon.items()]
    css.append('/*\n' + ICON_LICENCE + '*/')
    open(out + 'assets/icons.css', 'w').write('\n'.join(css) + '\n')
    # The favicon: the wordmark's slash on the pit board (brand.py).
    open(out + 'assets/favicon.svg', 'w').write(favicon() + '\n')
