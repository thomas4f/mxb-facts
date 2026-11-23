#!/usr/bin/env -S python3 -I
"""Compares two Windows program files (PE32 or PE32+) byte by byte and names each differing byte range: the link time
stamp in the file header, the file's CheckSum, the time stamp of a debug directory entry, the build ID (CodeView RSDS
GUID and age, which the linker works out over the linked file, so it changes with the time stamp), or "other". The last line says whether every difference lies in those link-time fields.

usage: pe_cmp.py <a.dll> <b.dll>
"""
import struct, sys


def fields(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    assert d[pe:pe + 4] == b'PE\0\0', 'not a PE file'
    out = [(pe + 8, 4, 'file header TimeDateStamp')]
    nsec, optsize = struct.unpack_from('<H', d, pe + 6)[0], struct.unpack_from('<H', d, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from('<H', d, opt)[0]
    dirs = opt + (112 if magic == 0x20B else 96)
    secs = [struct.unpack_from('<8sIIII', d, opt + optsize + 40 * i) for i in range(nsec)]

    def off(rva):
        for _, vsize, va, rsize, raw in secs:
            if va <= rva < va + max(vsize, rsize):
                return raw + rva - va
        return None

    out.append((opt + 64, 4, 'optional header CheckSum'))
    dbg_rva, dbg_size = struct.unpack_from('<II', d, dirs + 6 * 8)
    o = off(dbg_rva) if dbg_size else None
    for i in range(dbg_size // 28 if o is not None else 0):
        e = o + 28 * i
        out.append((e + 4, 4, f'debug entry {i} TimeDateStamp'))
        typ, size, rva, raw = struct.unpack_from('<IIII', d, e + 12)
        if typ == 2 and d[raw:raw + 4] == b'RSDS':
            out.append((raw + 4, 20, f'debug entry {i} CodeView build ID (GUID and age)'))
    return out


a, b = (open(p, 'rb').read() for p in sys.argv[1:3])
print(f'sizes: {len(a)} {len(b)}')
known = fields(a)
diff = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
ranges = []
for i in diff:
    if ranges and ranges[-1][1] == i:
        ranges[-1][1] = i + 1
    else:
        ranges.append([i, i + 1])
other = 0
for s, e in ranges:
    names = sorted({n for o, n_, n in known if o <= s < o + n_ or o < e <= o + n_})
    if not names:
        other += e - s
    print(f'0x{s:x}-0x{e - 1:x} ({e - s} bytes): {", ".join(names) or "other"}')
print(f'{len(diff)} bytes differ; {other} outside the link-time fields; sizes {"equal" if len(a) == len(b) else "differ"}')
sys.exit(0 if other == 0 and len(a) == len(b) else 1)
