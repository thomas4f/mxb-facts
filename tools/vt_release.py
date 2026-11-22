"""VirusTotal lookups for a release before it is analysed, for the "Analyse a tool" workflow. Nothing is uploaded.

Usage:
  python3 -I tools/vt_release.py hash <release folder> <hashes.json>  (no key: unpack and hash)
  python3 -I tools/vt_release.py lookup <hashes.json> <lookups.json>  (VT_API_KEY: hash lookups only)

"hash" takes the release files tools/fetch_release.py downloaded (each checked again against its SHA-256), unpacks every archive in them
with 7-Zip (zip, 7z, NSIS and MSI installers and the like; up to three levels deep) and writes the SHA-256 of every file
found, with where it was found. Nothing is run: unpacking only reads the archives. "lookup" looks up those hashes with
tools/vt_lookup.py and writes the results by hash, for the analysis to quote on P1 and for the pull request to write to
vt/results.json (tools/vt_lookup.py --from). The two are separate steps, so the key is only in the one that reads hashes.

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # vt_lookup.py sits beside this file
import vt_lookup  # noqa: E402

MAX_HASHES = 40
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


def lookup_release(hashes_path, out_path):
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


if __name__ == '__main__':
    cmd = sys.argv[1:2]
    if cmd == ['hash'] and len(sys.argv) == 4:
        sys.exit(hash_release(sys.argv[2], sys.argv[3]))
    if cmd == ['lookup'] and len(sys.argv) == 4:
        sys.exit(lookup_release(sys.argv[2], sys.argv[3]))
    print(__doc__, file=sys.stderr)
    sys.exit(2)
