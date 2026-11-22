#!/usr/bin/env -S python3 -I
"""Unpacks an Electron app.asar archive (the app's own code, as the installer ships it) into a folder.

usage: asar.py <app.asar> <folder>
Files the archive marks "unpacked" sit beside it in app.asar.unpacked/ and are left out.
"""
import json, os, struct, sys

src, out = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read()
hsize = struct.unpack_from('<I', d, 4)[0]
jlen = struct.unpack_from('<I', d, 12)[0]
tree, base = json.loads(d[16:16 + jlen]), 8 + hsize


def walk(node, path):
    for name, e in node['files'].items():
        p = os.path.join(path, name)
        assert '..' not in name.split('/') and not os.path.isabs(name), 'unsafe name ' + name
        if 'files' in e: os.makedirs(p, exist_ok=True); walk(e, p)
        elif not e.get('unpacked') and 'link' not in e:
            o = base + int(e['offset'])
            open(p, 'wb').write(d[o:o + e['size']])


os.makedirs(out, exist_ok=True)
walk(tree, out)
