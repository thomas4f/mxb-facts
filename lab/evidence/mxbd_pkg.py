#!/usr/bin/env -S python3 -I
"""Lists the files in an MXB Damage update package (.pkg: "MXBDPKG1", then for each file its name, its size and its bytes,
each name and size on its own line), one line per file in the release manifest's form: path|size|sha256.

usage: mxbd_pkg.py <file.pkg>
"""
import hashlib, sys

d = open(sys.argv[1], 'rb').read()
assert d.startswith(b'MXBDPKG1\n'), 'not an MXBDPKG1 package'
i = 9
while i < len(d):
    n = d.index(b'\n', i); name = d[i:n].decode('utf-8', 'replace')
    m = d.index(b'\n', n + 1); size = int(d[n + 1:m]); body = d[m + 1:m + 1 + size]
    assert len(body) == size, 'cut short at ' + name
    print(f'{name}|{size}|{hashlib.sha256(body).hexdigest()}')
    i = m + 1 + size
