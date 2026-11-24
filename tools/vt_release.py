"""VirusTotal lookups for a release before it is analysed, for the "Analyse a tool" workflow, and the uploads of the
downloaded files VirusTotal has no record of (CLAUDE.md, "VirusTotal").

Usage:
  python3 -I tools/vt_release.py hash <release folder> <hashes.json>  (no key: unpack and hash)
  python3 -I tools/vt_release.py lookup <hashes.json> <lookups.json> [--upload <release folder>]  (VT_API_KEY)

"hash" takes the release files tools/fetch_release.py downloaded (each checked again against its SHA-256), unpacks every archive in them
with 7-Zip (zip, 7z, NSIS and MSI installers and the like; up to three levels deep) and writes the SHA-256 of every file
found, with where it was found. Nothing is run: unpacking only reads the archives. "lookup" looks up those hashes with
tools/vt_lookup.py and writes the results by hash, for the analysis to quote on P1 and for the pull request to write to
vt/results.json (tools/vt_lookup.py --from). The two are separate steps, so the key is never in the one that unpacks.

With --upload, each file players download (the release files themselves, not what they unpack to) that VirusTotal has no
record of is uploaded from <release folder>, after its SHA-256 is checked against release.json again, then looked up again
once VirusTotal has scanned it. The workflow passes --upload only when the plan's licence read says analysis is allowed
(rule 6) and the run's "Skip upload" input is off. Uploads never hold the run up: a scan that hasn't finished after
SCAN_WAIT seconds is recorded as not on VirusTotal, with the upload date and "pending", and a failed upload is recorded
the same way with its error. Files over MAX_UPLOAD bytes aren't uploaded; over 32 MB they go to an upload URL.

The public API allows 4 lookups a minute, so the downloaded files come first, then program files, then the rest
(shallowest folder first), and at most MAX_HASHES are looked up; the rest are listed as not looked up.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # vt_lookup.py sits beside this file
import vt_lookup  # noqa: E402

MAX_HASHES = 40
MAX_UPLOAD = 650 * 1024 ** 2  # VirusTotal's limit for one file
DIRECT_UPLOAD = 32 * 1024 ** 2  # larger files go to the URL /files/upload_url gives
SCAN_WAIT = 15 * 60  # how long the uploads' scans are waited for, all together
POLL = 60  # seconds between two checks of a scan (4 requests a minute in all)
MAX_DEPTH = 3
MAX_BYTES = 2 * 1024 ** 3  # all unpacked files together
# The archive types 7-Zip names that are unpacked ("7z l -slt", its "Type" line).
ARCHIVES = {'zip', '7z', 'rar', 'rar5', 'gzip', 'bzip2', 'xz', 'zstd', 'tar', 'nsis', 'cab', 'compound', 'iso', 'wim', 'xar', 'dmg'}
PROGRAMS = ('.dlo', '.dll', '.exe', '.msi', '.sys', '.ps1', '.bat', '.cmd', '.js', '.py', '.jar')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def unpack(path, into):
    """Unpacks one archive with 7-Zip; returns False when it isn't an archive of a type in ARCHIVES. A program is read as
    one only when it is an installer (7-Zip would otherwise split any .exe into its sections). The dummy password makes
    an encrypted archive fail instead of waiting for one."""
    r = subprocess.run(['7z', 'l', '-slt', '-pnone', path], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    kind = next((l[7:].strip().lower() for l in r.stdout.splitlines() if l.startswith('Type = ')), None)
    if r.returncode != 0 or kind not in ARCHIVES:
        return False
    r = subprocess.run(['7z', 'x', '-y', '-bd', '-pnone', f'-o{into}', path], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return r.returncode == 0 and os.path.isdir(into) and bool(os.listdir(into))


def hash_release(folder, out_path):
    """The SHA-256 of every release file tools/fetch_release.py saved in <folder>, and of every file unpacked from them."""
    found, total = {}, 0

    def walk(path, where, depth):
        nonlocal total
        for root, _, names in os.walk(path):
            for n in sorted(names):
                p = os.path.join(root, n)
                if os.path.islink(p) or not os.path.isfile(p):
                    continue
                total += os.path.getsize(p)
                assert total <= MAX_BYTES, 'the release unpacks to more than %d bytes' % MAX_BYTES
                add(p, where + '/' + os.path.relpath(p, path).replace(os.sep, '/'), depth)

    def add(p, where, depth):
        h = sha256(p)
        if h not in found:
            found[h] = {'name': where, 'depth': depth, 'program': where.lower().endswith(PROGRAMS)}
        if depth < MAX_DEPTH:
            into = os.path.join(work, '%d.unpacked' % len(os.listdir(work)))
            if unpack(p, into):
                walk(into, where, depth + 1)

    work = os.path.join(os.path.dirname(os.path.abspath(out_path)), 'vt-unpacked')
    os.makedirs(work, exist_ok=True)
    for f in json.load(open(os.path.join(folder, 'release.json'))):
        p = os.path.join(folder, os.path.basename(f['name']))
        assert sha256(p) == f['sha256'], f['name'] + " doesn't match its SHA-256"
        add(p, os.path.basename(f['name']), 0)
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(found, f, indent=1)
        f.write('\n')
    print('%d files hashed' % len(found))
    return 0


def lookup_release(hashes_path, out_path, upload_from=None):
    key = os.environ.get('VT_API_KEY')
    if not key:
        print('Set VT_API_KEY first.', file=sys.stderr)
        return 2
    found = json.load(open(hashes_path))
    # The list was made in a job that unpacked untrusted files, so only well-formed hashes go into a request.
    assert all(re.fullmatch(r'[0-9a-f]{64}', h) for h in found), 'not a list of SHA-256 hashes'
    # Downloads, then programs, then the other files, shallowest folder first.
    order = sorted(found, key=lambda h: (found[h]['depth'] > 0, not found[h]['program'], found[h]['name'].count('/'), found[h]['name']))
    results = vt_lookup.lookup_all(key, order[:MAX_HASHES])
    if upload_from:
        results.update(upload_missing(key, upload_from, {h: r for h, r in results.items() if r.get('found') is False and found[h]['depth'] == 0}))
    today, url = time.strftime('%Y-%m-%d', time.gmtime()), vt_lookup.run_url()
    out = {}
    for h in order:
        r = results.get(h, {'error': 'not looked up (over %d files in this release)' % MAX_HASHES})
        out[h] = dict(r, name=found[h]['name'], looked_up=today, run=url, permalink=vt_lookup.GUI + h)
        print('%s  %s  %s' % (h, found[h]['name'], vt_lookup.describe(r)))
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    return 0


def request(key, url, data=None, content_type=None):
    """One VirusTotal API request; waits a minute and retries on "too many requests". Returns the JSON answer."""
    headers = {'x-apikey': key, 'accept': 'application/json'}
    if content_type:
        headers['content-type'] = content_type
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=600) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(60)
                continue
            raise


def upload(key, path):
    """Uploads one file; returns the id of its analysis."""
    with open(path, 'rb') as f:
        content = f.read()
    url = vt_lookup.API.rstrip('/')
    if len(content) > DIRECT_UPLOAD:
        url = request(key, url + '/upload_url')['data']
        time.sleep(vt_lookup.WAIT)
    boundary = '----mxbfacts' + hashlib.sha256(content).hexdigest()[:32]
    name = re.sub(r'[^A-Za-z0-9._+()-]', '_', os.path.basename(path))[:200] or 'release-file'  # the name players see; untrusted, so plain
    body = b''.join([('--%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\n'
                      'Content-Type: application/octet-stream\r\n\r\n' % (boundary, name)).encode(),
                     content, ('\r\n--%s--\r\n' % boundary).encode()])
    return request(key, url, body, 'multipart/form-data; boundary=' + boundary)['data']['id']


def upload_missing(key, folder, missing):
    """Uploads the downloaded files in <missing> (by hash) and looks each up again once it is scanned, waiting at most
    SCAN_WAIT seconds for all of them. Returns {hash: result}, each with 'uploaded' (the date) and, while its scan isn't
    finished, 'pending'; a failed upload keeps 'found': False with 'upload_error'."""
    files = {f['sha256']: os.path.join(folder, os.path.basename(f['name'])) for f in json.load(open(os.path.join(folder, 'release.json')))}
    today, out, analyses = time.strftime('%Y-%m-%d', time.gmtime()), {}, {}
    for h in missing:
        p = files.get(h)
        if not p or not os.path.isfile(p) or sha256(p) != h:
            out[h] = {'found': False, 'upload_error': "not uploaded: the downloaded file doesn't match its SHA-256"}
            continue
        if os.path.getsize(p) > MAX_UPLOAD:
            out[h] = {'found': False, 'upload_error': 'not uploaded: over %d MB, VirusTotal\'s limit' % (MAX_UPLOAD // 1024 ** 2)}
            continue
        time.sleep(vt_lookup.WAIT)
        try:
            analyses[h] = upload(key, p)
            out[h] = {'found': False, 'uploaded': today, 'pending': True}
            print('%s  uploaded to VirusTotal' % h)
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError) as e:
            out[h] = {'found': False, 'upload_error': 'upload failed (%s)' % (getattr(e, 'code', None) or getattr(e, 'reason', None) or type(e).__name__)}
    deadline = time.monotonic() + SCAN_WAIT
    while analyses and time.monotonic() < deadline:
        time.sleep(POLL)
        for h, aid in list(analyses.items()):
            try:
                status = request(key, vt_lookup.API.replace('/files/', '/analyses/') + aid)['data']['attributes']['status']
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError):
                continue  # asked again on the next round, until the deadline
            if status == 'completed':
                del analyses[h]
                time.sleep(vt_lookup.WAIT)
                r = vt_lookup.lookup(key, h)
                if r.get('found'):
                    out[h] = dict(r, uploaded=today)
            time.sleep(vt_lookup.WAIT)
    for h in analyses:
        print('%s  uploaded; its scan wasn\'t finished after %d minutes' % (h, SCAN_WAIT // 60))
    return out


if __name__ == '__main__':
    cmd = sys.argv[1:2]
    if cmd == ['hash'] and len(sys.argv) == 4:
        sys.exit(hash_release(sys.argv[2], sys.argv[3]))
    if cmd == ['lookup'] and len(sys.argv) == 4:
        sys.exit(lookup_release(sys.argv[2], sys.argv[3]))
    if cmd == ['lookup'] and len(sys.argv) == 6 and sys.argv[4] == '--upload':
        sys.exit(lookup_release(sys.argv[2], sys.argv[3], sys.argv[5]))
    print(__doc__, file=sys.stderr)
    sys.exit(2)
