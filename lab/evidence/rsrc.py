#!/usr/bin/env -S python3 -I
"""Lists the resources of a Windows program file (PE32 or PE32+): type, name, language, size and SHA-256 of each.
With an .ico file, also says which of the program's icons (RT_ICON) are the images in that file, byte for byte; and it
prints the text of the version resource (RT_VERSION).

usage: rsrc.py <file.exe> [<icon.ico>]
"""
import hashlib, struct, sys

TYPES = {3: 'RT_ICON', 14: 'RT_GROUP_ICON', 16: 'RT_VERSION', 24: 'RT_MANIFEST'}


def main():
    d = open(sys.argv[1], 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec, optsize = struct.unpack_from('<H', d, pe + 6)[0], struct.unpack_from('<H', d, pe + 20)[0]
    opt = pe + 24
    dd = opt + (112 if struct.unpack_from('<H', d, opt)[0] == 0x20B else 96)
    rva = struct.unpack_from('<I', d, dd + 2 * 8)[0]
    secs = [struct.unpack_from('<IIII', d, opt + optsize + 40 * i + 8) for i in range(nsec)]
    base = next(raw + rva - va for vs, va, rs, raw in secs if va <= rva < va + max(vs, rs))

    def off(r):
        return next(raw + r - va for vs, va, rs, raw in secs if va <= r < va + max(vs, rs))

    def entries(o):
        n1, n2 = struct.unpack_from('<HH', d, o + 12)
        for i in range(n1 + n2):
            name, ptr = struct.unpack_from('<II', d, o + 16 + 8 * i)
            if name & 0x80000000:
                p = base + (name & 0x7fffffff)
                ln = struct.unpack_from('<H', d, p)[0]
                name = d[p + 2:p + 2 + 2 * ln].decode('utf-16-le')
            yield name, ptr

    res = []
    for t, p1 in entries(base):
        for n, p2 in entries(base + (p1 & 0x7fffffff)):
            for lang, p3 in entries(base + (p2 & 0x7fffffff)):
                drva, size = struct.unpack_from('<II', d, base + p3)
                data = d[off(drva):off(drva) + size]
                res.append((t, n, lang, data))
                print(f'{TYPES.get(t, t)!s:14} {n!s:>4} lang {lang:5} {size:7} bytes  {hashlib.sha256(data).hexdigest()}')
    if len(sys.argv) > 2:
        ico = open(sys.argv[2], 'rb').read()
        count = struct.unpack_from('<H', ico, 4)[0]
        imgs = []
        for i in range(count):
            size, o = struct.unpack_from('<II', ico, 6 + 16 * i + 8)
            imgs.append(ico[o:o + size])
        icons = [r[3] for r in res if r[0] == 3]
        same = sum(1 for img in imgs if img in icons)
        print(f'{sys.argv[2]}: {count} images; {same} of them are RT_ICON resources byte for byte; the program has {len(icons)} RT_ICON')
    for t, n, lang, data in res:
        if t == 16:
            text = data.decode('utf-16-le', 'replace')
            print('RT_VERSION strings:', ' | '.join(s for s in text.split('\0') if len(s) > 1 and s.isascii() and s.isprintable()))


main()
