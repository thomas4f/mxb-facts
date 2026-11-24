"""Download the release files a plan names, check each against its SHA-256, and keep them for the later jobs.

Usage:
  python3 -I tools/fetch_release.py <plan.json> <folder>   (the fetch job: every file the plan names)
  python3 -I tools/fetch_release.py list <MEGA folder link>  (each file in the folder, with its own link and size)
  python3 -I tools/fetch_release.py get <link> <folder>      (one file, saved and hashed, for writing the plan)

For the "Analyse a tool" workflow: one job downloads the release, and the Windows run and the VirusTotal lookup take the
files from it, so every place a tool publishes works for both. A plain https link is downloaded as it is. A MEGA file
link (https://mega.nz/file/<id>#<key>) is downloaded through MEGA's public API and decrypted with the key in the link,
which gives the file exactly as players get it; its name comes from the file's own attributes. A file inside a MEGA
folder is named by the folder link with the file's handle (https://mega.nz/folder/<id>#<key>/file/<handle>, which "list"
prints); a folder link alone names no file. Each file is saved in <folder> under its name, and <folder>/release.json lists
name, url and SHA-256 in the plan's order. A file whose SHA-256 differs from the plan's stops the run. Nothing downloaded
is run. Needs the cryptography package for MEGA.
"""
import base64
import hashlib
import json
import os
import re
import struct
import sys
import urllib.request

MEGA = re.compile(r'^https://mega\.(?:nz|co\.nz)/(?:file/([A-Za-z0-9_-]{8})#([A-Za-z0-9_-]{43})|#!([A-Za-z0-9_-]{8})!([A-Za-z0-9_-]{43}))$')
FOLDER = re.compile(r'^https://mega\.(?:nz|co\.nz)/(?:folder/([A-Za-z0-9_-]{8})#([A-Za-z0-9_-]{22})(?:/file/([A-Za-z0-9_-]{8}))?'
                    r'|#F!([A-Za-z0-9_-]{8})!([A-Za-z0-9_-]{22})(?:!([A-Za-z0-9_-]{8}))?)$')
API = 'https://g.api.mega.co.nz/cs'
UA = 'mxb-facts-fetch/1.0'  # a generic name, as tools/mxbmods_fetch.py sends: mxb-mods.com refuses Python's own (403)
NAME = re.compile(r'[^A-Za-z0-9._+ ()-]')


def b64(s):
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


def save(resp, path, decrypt=None):
    h = hashlib.sha256()
    with open(path, 'wb') as out:
        while True:
            block = resp.read(1 << 20)
            if not block:
                break
            if decrypt:
                block = decrypt.update(block)
            h.update(block)
            out.write(block)
    return h.hexdigest()


def api(call, folder=None):
    req = urllib.request.Request(API + ('?id=0&n=' + folder if folder else ''), data=json.dumps([call]).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)[0]


def aes_key(k):
    """A file's 32-byte key folds into its AES key; a folder's 16-byte key is its AES key."""
    if len(k) == 16:
        return k
    a = struct.unpack('>8I', k)
    return struct.pack('>4I', a[0] ^ a[4], a[1] ^ a[5], a[2] ^ a[6], a[3] ^ a[7])


def attrs(at, k):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    dec = Cipher(algorithms.AES(aes_key(k)), modes.CBC(b'\0' * 16)).decryptor()
    a = (dec.update(b64(at)) + dec.finalize()).rstrip(b'\0')
    assert a.startswith(b'MEGA{'), 'the key in the MEGA link does not open the file'
    return json.loads(a[4:].decode())


def download(info, k, folder):
    """Saves a MEGA file (its download answer and 32-byte key) under its own name; returns its path and SHA-256."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    assert isinstance(info, dict) and 'g' in info, 'MEGA has no such file (answer %r)' % (info,)
    ctr = Cipher(algorithms.AES(aes_key(k)), modes.CTR(k[16:24] + b'\0' * 8)).decryptor()
    path = os.path.join(folder, clean(attrs(info['at'], k)['n']))
    with urllib.request.urlopen(info['g'], timeout=300) as r:
        return path, save(r, path, ctr)


def mega(handle, key, folder):
    return download(api({'a': 'g', 'g': 1, 'ssl': 1, 'p': handle}), b64(key), folder)


def mega_nodes(fid, fkey):
    """Every file and folder in a MEGA folder: {handle: (parent, path, size or None, 32- or 16-byte key)}."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    res = api({'a': 'f', 'c': 1, 'r': 1, 'ca': 1}, fid)
    assert isinstance(res, dict) and 'f' in res, 'MEGA has no folder %s (answer %r)' % (fid, res)
    raw = {}
    for n in res['f']:
        dec = Cipher(algorithms.AES(b64(fkey)), modes.ECB()).decryptor()
        k = dec.update(b64(n['k'].split(':')[-1])) + dec.finalize()
        raw[n['h']] = (n['p'], attrs(n['a'], k)['n'], n.get('s') if n['t'] == 0 else None, k)

    def path(h):
        p, name = raw[h][0], raw[h][1]
        return path(p) + '/' + name if p in raw else name
    return {h: (p, path(h), s, k) for h, (p, _n, s, k) in raw.items()}


def mega_folder_file(fid, fkey, handle, folder):
    nodes = mega_nodes(fid, fkey)
    assert handle in nodes and nodes[handle][2] is not None, 'the MEGA folder has no file ' + handle
    return download(api({'a': 'g', 'g': 1, 'ssl': 1, 'n': handle}, fid), nodes[handle][3], folder)


def fetch(url, folder):
    """Downloads one file the link names into <folder>; returns its path and SHA-256."""
    m, f = MEGA.match(url), FOLDER.match(url)
    if m:
        return mega(m.group(1) or m.group(3), m.group(2) or m.group(4), folder)
    if f:
        fid, fkey, handle = f.group(1) or f.group(4), f.group(2) or f.group(5), f.group(3) or f.group(6)
        assert handle, 'a MEGA folder link names no file: name one with /file/<handle> (fetch_release.py list <link>)'
        return mega_folder_file(fid, fkey, handle, folder)
    assert url.startswith('https://'), 'only https downloads: ' + url
    path = os.path.join(folder, clean(url.split('?')[0].split('#')[0]))
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=300) as r:
        return path, save(r, path)


def clean(name):
    name = NAME.sub('_', os.path.basename(name)).strip(' .') or 'file'
    assert name.lower() != 'release.json', 'a release file may not be named release.json'
    return name


def main(plan_path, folder):
    os.makedirs(folder, exist_ok=True)
    out = []
    for f in json.load(open(plan_path)).get('files', []):
        url, want = f['url'], f['sha256'].lower()
        path, got = fetch(url, folder)
        assert got == want, '%s has SHA-256 %s, the plan says %s' % (url, got, want)
        assert not any(o['name'] == os.path.basename(path) for o in out), 'two release files are named ' + os.path.basename(path)
        out.append({'name': os.path.basename(path), 'url': url, 'sha256': got})
        print('%s  %s' % (got, os.path.basename(path)))
    with open(os.path.join(folder, 'release.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    return 0


def list_folder(url):
    f = FOLDER.match(url)
    assert f, 'not a MEGA folder link: ' + url
    fid, fkey = f.group(1) or f.group(4), f.group(2) or f.group(5)
    for h, (_p, path, size, _k) in sorted(mega_nodes(fid, fkey).items(), key=lambda x: x[1][1]):
        if size is not None:
            print('https://mega.nz/folder/%s#%s/file/%s  %10d  %s' % (fid, fkey, h, size, path))
    return 0


def get(url, folder):
    os.makedirs(folder, exist_ok=True)
    path, got = fetch(url, folder)
    print('%s  %s' % (got, os.path.basename(path)))
    return 0


if __name__ == '__main__':
    if sys.argv[1:2] == ['list'] and len(sys.argv) == 3:
        sys.exit(list_folder(sys.argv[2]))
    if sys.argv[1:2] == ['get'] and len(sys.argv) == 4:
        sys.exit(get(sys.argv[2], sys.argv[3]))
    if len(sys.argv) != 3 or sys.argv[1] in ('list', 'get'):
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
