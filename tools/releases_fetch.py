"""Find each tool's newest release, wherever it is published, into registry/releases.json.

Reads registry/tools.json. Every tool is looked up in each place it publishes releases:

- github     its "github" repo: the newest release through the GitHub API (tag, date, files with
             the SHA-256 GitHub gives for each file). Set GITHUB_TOKEN for a higher rate limit.
- mxb-mods / gpb-mods
             its tied post: the newest file attached to it (public WordPress API, as in
             tools/mxbmods_fetch.py), or, when the download button points at Mega, MediaFire or
             Google Drive, that file read as below; and the post's last update.
- downloads  any other links in its "downloads" list (registry/README.md), each read by its host:
             mediafire.com (file name, size and upload date from the public page),
             drive.google.com (file name from the public page), mega.nz (size through Mega's
             public API; the name is encrypted, so it isn't kept), and any other URL (the file
             name, size and date the server gives, or, for a web page such as a forum topic, the
             files it links to on its own site, else the first Mega, MediaFire or Google Drive file
             link on it; a file on any other site, such as a runtime it asks players to install, is
             left out).

A file whose name, size or date changed since the last run is downloaded once to work out its
SHA-256 (GitHub gives it, and Mega files are encrypted, so neither is downloaded). Nothing is
uploaded and nothing but GET requests is sent, one at a time, a second apart, with a generic
User-Agent; robots.txt is read first for the mods sites.

For every tool with a card, the newest release is compared with its newest card: newer when the
release's files have hashes, none of them is one the card lists, and its version differs. Tools without a
card are compared with the previous run only. The result goes to the run's summary
($GITHUB_STEP_SUMMARY, or the terminal), and registry/releases.json is only rewritten when a
release changed, so a tool's "seen" date is when that release was first seen. With NEWER_OUT set,
the releases newer than their card are also written there as JSON, for tools/recheck_issues.py.

The "Update inventory" workflow runs it every Monday, after tools/mxbmods_fetch.py.
By hand:  python3 -I tools/releases_fetch.py

With --latest <tool>, it only looks up that tool's latest GitHub release, at the time it runs, and prints
version=<tag>, release=<release page> and source=github, as the "Analyse a tool" workflow reads them; for a tool
with no "github" repo, or one with no published release, it prints them empty and source=registry, and the analysis
then takes the newest release in registry/releases.json. Nothing is written.
"""
import datetime, hashlib, html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser

import yaml  # pinned in requirements.txt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
REG = ROOT + 'registry/tools.json'
OUT = ROOT + 'registry/releases.json'
SITES = {'mxb-mods': 'https://mxb-mods.com', 'gpb-mods': 'https://gpb-mods.com'}
UA = 'mxb-facts-fetch/1.0'
MAXHASH = 1 << 30  # files over 1 GiB are listed without a hash
TODAY = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')


def request(url, accept='*/*', headers=None):
    h = {'User-Agent': UA, 'Accept': accept}
    h.update(headers or {})
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60)


def get_json(url, headers=None, data=None):
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h, data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    time.sleep(1)
    return out


def get_text(url):
    with request(url, 'text/html') as r:
        out = r.read().decode('utf-8', 'replace')
    time.sleep(1)
    return out


def sha256_of(url):
    """Downloads a file once and returns its SHA-256 and size, or (None, size) when it is too big."""
    h, n = hashlib.sha256(), 0
    with request(url) as r:
        size = int(r.headers.get('Content-Length') or 0)
        if size > MAXHASH:
            return None, size
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
            if n > MAXHASH:
                return None, n
    time.sleep(1)
    return h.hexdigest(), n


def name_of(url):
    return urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit('/', 1)[-1])


# Each reader returns a release: {"source", "version", "date", "url", "files": [{"name", "size", "sha256", "url"}]},
# or None when the place has nothing yet.

def from_github(repo):
    h = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    if os.environ.get('GITHUB_TOKEN'):
        h['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    try:
        r = get_json('https://api.github.com/repos/%s/releases/latest' % repo, h)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # no published release (a repo that ships from its main branch, or holds only a README)
        raise
    files = [{'name': a['name'], 'size': a['size'], 'sha256': (a.get('digest') or '').removeprefix('sha256:') or None,
              'url': a['browser_download_url']} for a in r['assets']]
    return {'source': 'github', 'version': r['tag_name'], 'date': (r.get('published_at') or '')[:10],
            'url': r['html_url'], 'files': files}


def from_mods_site(key, post):
    site = SITES[key]
    p = get_json(site + '/wp-json/wp/v2/posts/%d?_fields=link,modified_gmt' % post)
    media = get_json(site + '/wp-json/wp/v2/media?' + urllib.parse.urlencode(
        {'parent': post, 'per_page': 100, '_fields': 'source_url,date_gmt,mime_type'}))
    files = sorted((m for m in media if m['mime_type'].startswith('application/')), key=lambda m: m['date_gmt'], reverse=True)
    if not files:
        # No attached file: the download button may still point at a file on the site.
        t = get_text(p['link'])
        links = re.findall(re.escape(site) + r'/wp-content/uploads/[^"\'\s<>]+\.(?:zip|rar|7z|exe|dlo|msi)', t)
        if not links:
            # Or it points at a file host (Mega, MediaFire, Google Drive): read that link the same way as a "downloads" one.
            ext = re.findall(r'href="(https://(?:mega\.nz/(?:file/|#!)|(?:www\.)?mediafire\.com/file/|drive\.google\.com/file/d/)[^"]+)"', t)
            if ext:
                rel = read_link(html.unescape(ext[0]))
                rel['via'] = p['link']
                return rel
            return {'source': key, 'version': None, 'date': p['modified_gmt'][:10], 'url': p['link'], 'files': []}
        files = [{'source_url': links[0], 'date_gmt': p['modified_gmt']}]
    f = files[0]
    return {'source': key, 'version': None, 'date': f['date_gmt'][:10], 'url': p['link'],
            'files': [{'name': name_of(f['source_url']), 'size': None, 'sha256': None, 'url': f['source_url']}]}


def from_mediafire(url):
    t = get_text(url)
    name = re.search(r'<div class="filename">\s*([^<]+?)\s*</div>', t) or re.search(r'<title>\s*([^<]+?)\s*-\s*MediaFire', t)
    size = re.search(r'Download \(([\d.]+\s*[KMG]B)\)', t)
    date = re.search(r'Uploaded:\s*<span>\s*([\d-]+)', t)
    direct = re.search(r'href="(https://download\d*\.mediafire\.com/[^"]+)"', t)
    return {'source': 'mediafire', 'version': None, 'date': date.group(1) if date else None, 'url': url,
            'files': [{'name': html.unescape(name.group(1)) if name else None, 'size': size.group(1) if size else None,
                       'sha256': None, 'url': direct.group(1) if direct else None}]}


def from_gdrive(url):
    t = get_text(url)
    name = re.search(r'<title>\s*(.+?)\s*-\s*Google Drive\s*</title>', t)
    return {'source': 'drive.google.com', 'version': None, 'date': None, 'url': url,
            'files': [{'name': html.unescape(name.group(1)) if name else None, 'size': None, 'sha256': None, 'url': None}]}


def from_mega(url):
    m = re.search(r'mega\.nz/(?:file/|#!)([\w-]+)', url)
    assert m, 'downloads: a Mega link must be a file link (mega.nz/file/...): ' + url
    r = get_json('https://g.api.mega.co.nz/cs', {'Content-Type': 'application/json'}, json.dumps([{'a': 'g', 'p': m.group(1)}]).encode())
    size = r[0].get('s') if isinstance(r[0], dict) else None
    return {'source': 'mega.nz', 'version': None, 'date': None, 'url': url,
            'files': [{'name': None, 'size': size, 'sha256': None, 'url': None}]}


def page_links(page, text):
    """The release files a web page links to: (files on the page's own site, newest first as the page lists them,
    at most 5; Mega, MediaFire and Google Drive file links). A file on any other site is left out: it is what the
    page asks players to install first (Microsoft's VC++ runtime on the MaXHUD forum topic, issue #27), not the
    tool's release."""
    own = urllib.parse.urlparse(page).hostname
    links, hosted = [], []
    for h in re.findall(r'href="([^"]+)"', text):
        h = urllib.parse.urljoin(page, html.unescape(h))
        if re.match(r'https://(?:mega\.nz/(?:file/|#!)|(?:www\.)?mediafire\.com/file/|drive\.google\.com/file/d/)', h):
            if h not in hosted:
                hosted.append(h)
        elif (urllib.parse.urlparse(h).hostname == own and re.search(r'\.(zip|rar|7z|exe|dlo|msi)(\?|$)', h, re.I)
              and h not in links and len(links) < 5):
            links.append(h)
    return links, hosted


def from_link(url):
    with request(url) as r:
        kind = r.headers.get('Content-Type', '')
        if kind.startswith('text/html'):
            # A web page (a forum topic, a homepage): the files it links to, newest link first as the page lists them.
            t = r.read(4 << 20).decode('utf-8', 'replace')
            time.sleep(1)
            links, hosted = page_links(r.url, t)
            if not links and hosted:
                # No file on the page's own site: read the first Mega, MediaFire or Google Drive file link instead.
                rel = read_link(hosted[0])
                rel['via'] = url
                return rel
            return {'source': urllib.parse.urlparse(url).hostname, 'version': None, 'date': None, 'url': url,
                    'files': [{'name': name_of(h), 'size': None, 'sha256': None, 'url': h} for h in links]}
        cd = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', r.headers.get('Content-Disposition', ''))
        mod = r.headers.get('Last-Modified')
        f = {'name': urllib.parse.unquote(cd.group(1)) if cd else name_of(r.url),
             'size': int(r.headers['Content-Length']) if r.headers.get('Content-Length') else None, 'sha256': None, 'url': r.url}
    time.sleep(1)
    date = datetime.datetime.strptime(mod, '%a, %d %b %Y %H:%M:%S GMT').strftime('%Y-%m-%d') if mod else None
    return {'source': urllib.parse.urlparse(url).hostname, 'version': None, 'date': date, 'url': url, 'files': [f]}


def read_link(url):
    host = urllib.parse.urlparse(url).hostname or ''
    if host.endswith('mediafire.com'):
        return from_mediafire(url)
    if host == 'drive.google.com':
        return from_gdrive(url)
    if host in ('mega.nz', 'mega.co.nz'):
        return from_mega(url)
    return from_link(url)


def same_files(a, b):
    key = lambda r: [(f['name'], f['size']) for f in r['files']] + [r.get('date'), r.get('version')]
    return key(a) == key(b)


def main():
    reg = json.load(open(REG))
    try:
        old = json.load(open(OUT)).get('tools', {})
    except (OSError, ValueError):
        old = {}
    for key, site in SITES.items():
        if any(key in e and e[key]['post'] for e in reg.values()):
            rp = urllib.robotparser.RobotFileParser()
            with request(site + '/robots.txt') as r:
                rp.parse(r.read().decode('utf-8', 'replace').splitlines())
            if not rp.can_fetch(UA, site + '/wp-json/wp/v2/media'):
                sys.exit('robots.txt of ' + site + ' does not allow ' + UA + ' to read /wp-json/; nothing fetched')
    tools, report, failed, newer = {}, [], [], []
    for slug, e in sorted(reg.items()):
        places = []
        if e.get('github'):
            places.append(('github', lambda e=e: from_github(e['github'])))
        for key in SITES:
            # A page someone else uploaded (tied only by the maintainer's confirmation) is no release place
            # when the tool lists its own downloads.
            if key in e and e[key]['post'] and (e[key].get('tied_by') or not e.get('downloads')):
                places.append((key, lambda key=key, e=e: from_mods_site(key, e[key]['post'])))
        for url in e.get('downloads', []):
            places.append((url, lambda url=url: read_link(url)))
        seen = {}
        for place, read in places:
            prev = old.get(slug, {}).get(place)
            try:
                rel = read()
            except Exception as x:  # one place failing doesn't stop the others; the old entry is kept and the run fails at the end
                failed.append('%s (%s): %s' % (slug, place, x))
                if prev:
                    seen[place] = prev
                continue
            if rel is None:
                continue
            if prev and same_files(prev, rel):
                seen[place] = prev  # unchanged: keep its hashes and the date it was first seen
                continue
            for f in rel['files']:
                if not f['sha256'] and f['url'] and rel['source'] not in ('mega.nz',):
                    try:
                        f['sha256'], n = sha256_of(f['url'])
                        f['size'] = f['size'] or n
                    except Exception as x:
                        failed.append('%s (%s, hashing %s): %s' % (slug, place, f['name'], x))
            rel['seen'] = TODAY
            seen[place] = rel
            if prev:
                report.append('%s: %s changed (%s)' % (slug, place, describe(rel)))
        if seen:
            tools[slug] = seen
        if e['cards']:
            card = yaml.safe_load(open(ROOT + 'cards/' + e['cards'][-1]))
            known = {str(f.get('sha256', '')).lower() for f in card.get('files', [])}
            for place, rel in seen.items():
                hashes = {(f['sha256'] or '').lower() for f in rel['files']} - {''}
                # Only a file with a known hash can show the card is behind (Mega and Drive give none).
                if hashes and not (hashes & known) and rel.get('version') != card.get('version'):
                    report.append('%s: newer than its card (%s, version %s): %s' % (slug, e['cards'][-1], card.get('version'), describe(rel)))
                    newer.append({'tool': slug, 'name': e['name'], 'card': e['cards'][-1], 'card_version': card.get('version'),
                                  'place': place, 'version': rel.get('version') or (rel['files'][0]['name'] if rel['files'] else ''),
                                  'url': rel.get('url') or '', 'date': rel.get('date') or ''})
    summary = ['## Releases', '']
    summary += ['- ' + r for r in report] or ['No new release since the last run, and every card matches its newest release.']
    if failed:
        summary += ['', '### Could not be read', ''] + ['- ' + f for f in failed]
    text = '\n'.join(summary) + '\n'
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        open(os.environ['GITHUB_STEP_SUMMARY'], 'a').write(text)
    print(text)
    # The releases newer than their card, for tools/recheck_issues.py (the workflow opens a re-check issue for each).
    if os.environ.get('NEWER_OUT'):
        with open(os.environ['NEWER_OUT'], 'w') as f:
            json.dump(newer, f, indent=1, ensure_ascii=False)
    if tools != old:
        with open(OUT, 'w') as f:
            json.dump({'note': 'The newest release seen in each place a tool publishes, written by tools/releases_fetch.py. '
                               '"seen" is the date it was first seen. Hashes come from GitHub or from downloading the file once.',
                       'tools': tools}, f, indent=1, ensure_ascii=False)
            f.write('\n')
        print('wrote ' + os.path.relpath(OUT, ROOT))
    if failed:
        sys.exit(1)


def describe(rel):
    f = rel['files'][0] if rel['files'] else {}
    bits = [rel.get('version') or f.get('name') or 'no file', rel.get('date'), rel.get('url')]
    return ', '.join(str(b) for b in bits if b)


def latest(slug):
    """The tool's latest GitHub release, looked up now, as the lines the "Analyse a tool" workflow reads."""
    e = json.load(open(REG)).get(slug)
    if e is None:
        sys.exit('not in registry/tools.json: ' + slug)
    rel = from_github(e['github']) if e.get('github') else None
    if rel is None:
        return 'version=\nrelease=\nsource=registry\n'
    return 'version=%s\nrelease=%s\nsource=github\n' % (rel['version'], rel['url'])


if __name__ == '__main__':
    if sys.argv[1:2] == ['--latest'] and len(sys.argv) == 3:
        sys.stdout.write(latest(sys.argv[2]))
    else:
        main()
