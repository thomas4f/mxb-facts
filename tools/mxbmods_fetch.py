"""Snapshot each tool's mods-site page into registry/mxb-mods.json (MX Bikes, mxb-mods.com)
and registry/gpb-mods.json (GP Bikes, gpb-mods.com).

Reads registry/tools.json. For every tool tied to a post on its game's mods site (its "mxb-mods"
or "gpb-mods" entry), it reads the post through the site's public WordPress REST API
(/wp-json/wp/v2/posts/<id>, the same API MXB App uses; both sites run the same software)
and keeps: title, link, excerpt, published and updated dates, categories.
The site shows only the page link. The excerpt is the page's own claim, kept as input for
the questions that check a tool's claims against its code, never shown as a fact.
It also checks that the post (its body, attached files or public page) still holds the "tied_by" text (a GitHub link, a file name
or a hash) that ties it to the tool; a post that no longer does is kept but marked.

The "Update inventory" workflow runs it every Monday and commits any change to main.
By hand:  python3 -I tools/mxbmods_fetch.py
A file is only rewritten when a page changed, so its "fetched" date is when the text was
last seen to change. Exits 1 when a page no longer holds its tie, so the workflow fails.

Rules it keeps: robots.txt is checked first; one request at a time, a second apart;
a generic User-Agent; no user or author lookups (the site forbids them, and the
registry holds each author's published name already); nothing sent but GET requests.
"""
import datetime, html, json, os, re, sys, time, urllib.parse, urllib.request, urllib.robotparser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
REG = ROOT + 'registry/tools.json'
SITES = {'mxb-mods': 'https://mxb-mods.com', 'gpb-mods': 'https://gpb-mods.com'}  # registry key: site; snapshot registry/<key>.json
UA = 'mxb-facts-fetch/1.0'
WORDS = 60


def get(site, path, params):
    url = site + path + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    time.sleep(1)
    return data


def page(site, url):
    assert url.startswith(site + '/'), url
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode('utf-8', 'replace')
    time.sleep(1)
    return data


def text(h):
    t = html.unescape(re.sub(r'<[^>]+>', ' ', h))
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'\s*\[(…|&hellip;|\.\.\.)\]$', '', t)
    w = t.split(' ')
    return ' '.join(w[:WORDS]) + ('…' if len(w) > WORDS or h.rstrip().endswith('[&hellip;]</p>') else '')


def snapshot(key, site, reg):
    """Fetches the tied pages of one site. Returns the tools whose page no longer holds its tie."""
    out = ROOT + 'registry/' + key + '.json'
    tied_here = {slug: e[key] for slug, e in reg.items() if key in e and e[key]['post']}
    if tied_here:
        # robots.txt is read with the same User-Agent as the pages (gpb-mods.com refuses Python's default one).
        rp = urllib.robotparser.RobotFileParser(site + '/robots.txt')
        req = urllib.request.Request(site + '/robots.txt', headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            rp.parse(r.read().decode('utf-8', 'replace').splitlines())
        if not rp.can_fetch(UA, site + '/wp-json/wp/v2/posts'):
            sys.exit('robots.txt of ' + site + ' does not allow ' + UA + ' to read /wp-json/; nothing fetched')
    posts, cats, bad = {}, set(), []
    for slug, m in tied_here.items():
        pid = m['post']
        p = get(site, '/wp-json/wp/v2/posts/%d' % pid, {'_fields': 'id,status,link,title,excerpt,content,date_gmt,modified_gmt,categories'})
        media = get(site, '/wp-json/wp/v2/media', {'parent': pid, 'per_page': 100, '_fields': 'source_url'})
        tie = m.get('tied_by')
        if tie:
            # Download buttons are drawn by the page template, not the post body, so the public page is read too.
            hay = p['content']['rendered'] + ' ' + ' '.join(x['source_url'] for x in media) + ' ' + page(site, p['link'])
            tied = tie in hay
            if not tied:
                bad.append(slug)
        else:
            tied = None  # tied by the maintainer's confirmation ("confirmed"), nothing on the page to check
        cats.update(p['categories'])
        posts[slug] = {
            'post': p['id'],
            'link': p['link'],
            'title': html.unescape(p['title']['rendered']),
            'excerpt': text(p['excerpt']['rendered']),
            'published': p['date_gmt'][:10],
            'updated': p['modified_gmt'][:10],
            'categories': p['categories'],
            'still_tied': tied,
        }
    names = {}
    if cats:
        for c in get(site, '/wp-json/wp/v2/categories', {'include': ','.join(map(str, sorted(cats))), 'per_page': 100, '_fields': 'id,name'}):
            names[c['id']] = html.unescape(c['name'])
    for p in posts.values():
        p['categories'] = [names.get(c, str(c)) for c in p['categories']]
    tools = dict(sorted(posts.items()))
    try:
        old = json.load(open(out))
    except (OSError, ValueError):
        old = {}
    if old.get('tools') == tools:
        print('No change since %s; %s left as it is' % (old.get('fetched'), os.path.relpath(out, ROOT)))
        return bad
    snap = {
        'fetched': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'),
        'source': site + '/wp-json/wp/v2/posts',
        'note': "Each excerpt is quoted from the tool's " + site.split('//')[1] + " page as published, not verified.",
        'tools': tools,
    }
    with open(out, 'w') as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('%d pages saved to %s' % (len(posts), os.path.relpath(out, ROOT)))
    return bad


def main():
    reg = json.load(open(REG))
    bad = []
    for key, site in SITES.items():
        bad += snapshot(key, site, reg)
    if bad:
        print('No longer tied (check and update registry/tools.json): ' + ', '.join(bad))
        sys.exit(1)


if __name__ == '__main__':
    main()
