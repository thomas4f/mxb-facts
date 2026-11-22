"""Download the release files a plan names, check each against its SHA-256, and keep them for the later jobs.

Usage: python3 -I tools/fetch_release.py <plan.json> <folder>

For the "Analyse a tool" workflow: one job downloads the release, and the Windows run and the VirusTotal lookup take the
files from it, so every place a tool publishes works for both. A plain https link is downloaded as it is. A MEGA file
link (https://mega.nz/file/<id>#<key>) is downloaded through MEGA's public API and decrypted with the key in the link,
which gives the file exactly as players get it; its name comes from the file's own attributes. Each file is saved in
<folder> under its name, and <folder>/release.json lists name, url and SHA-256 in the plan's order. A file whose
SHA-256 differs from the plan's stops the run. Nothing downloaded is run. Needs the cryptography package for MEGA.
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


def mega(handle, key, folder):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    k = b64(key)
    a = struct.unpack('>8I', k)
    aes = struct.pack('>4I', a[0] ^ a[4], a[1] ^ a[5], a[2] ^ a[6], a[3] ^ a[7])
    req = urllib.request.Request('https://g.api.mega.co.nz/cs', data=json.dumps([{'a': 'g', 'g': 1, 'ssl': 1, 'p': handle}]).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        info = json.load(r)[0]
    assert isinstance(info, dict) and 'g' in info, 'MEGA has no file %s (answer %r)' % (handle, info)
    dec = Cipher(algorithms.AES(aes), modes.CBC(b'\0' * 16)).decryptor()
    attrs = (dec.update(b64(info['at'])) + dec.finalize()).rstrip(b'\0')
    assert attrs.startswith(b'MEGA{'), 'the key in the MEGA link does not open the file'
    name = json.loads(attrs[4:].decode())['n']
    ctr = Cipher(algorithms.AES(aes), modes.CTR(k[16:24] + b'\0' * 8)).decryptor()
    path = os.path.join(folder, clean(name))
    with urllib.request.urlopen(info['g'], timeout=300) as r:
        return path, save(r, path, ctr)


def clean(name):
    name = NAME.sub('_', os.path.basename(name)).strip(' .') or 'file'
    assert name.lower() != 'release.json', 'a release file may not be named release.json'
    return name


def main(plan_path, folder):
    os.makedirs(folder, exist_ok=True)
    out = []
    for f in json.load(open(plan_path)).get('files', []):
        url, want = f['url'], f['sha256'].lower()
        m = MEGA.match(url)
        if m:
            path, got = mega(m.group(1) or m.group(3), m.group(2) or m.group(4), folder)
        else:
            assert url.startswith('https://'), 'only https downloads: ' + url
            path = os.path.join(folder, clean(url.split('?')[0].split('#')[0]))
            with urllib.request.urlopen(url, timeout=300) as r:
                got = save(r, path)
        assert got == want, '%s has SHA-256 %s, the plan says %s' % (url, got, want)
        assert not any(o['name'] == os.path.basename(path) for o in out), 'two release files are named ' + os.path.basename(path)
        out.append({'name': os.path.basename(path), 'url': url, 'sha256': got})
        print('%s  %s' % (got, os.path.basename(path)))
    with open(os.path.join(folder, 'release.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
