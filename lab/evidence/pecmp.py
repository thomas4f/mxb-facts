#!/usr/bin/env -S python3 -I
"""Compare a rebuilt PE file with a released one, byte for byte.

usage: pecmp.py <released file> <rebuilt file>

Lists every byte range that differs and names the field it falls in: the PE header's build time stamp, a debug
directory entry's time stamp, or the build ID record the debug directory points at (the CodeView record's GUID and
age, which the linker makes up for each build). Then compares the two files again with those fields blanked in both,
and says whether anything else differs.
"""
import struct, sys


def fields(d):
    """(start, end, name) of every per-build field in the PE file d."""
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    out = [(pe + 8, pe + 12, 'PE header TimeDateStamp')]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    opt = pe + 24
    magic = struct.unpack_from('<H', d, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    secs = []
    sh = opt + struct.unpack_from('<H', d, pe + 20)[0]
    for i in range(nsec):
        va, size, raw = struct.unpack_from('<III', d, sh + i * 40 + 12)[0:3]
        vsize = struct.unpack_from('<I', d, sh + i * 40 + 8)[0]
        secs.append((va, max(vsize, size), raw))

    def off(rva):
        for va, size, raw in secs:
            if va <= rva < va + size:
                return raw + rva - va
        return None
    drva, dsize = struct.unpack_from('<II', d, dd + 6 * 8)
    o = off(drva) if drva else None
    for i in range(dsize // 28 if o is not None else 0):
        e = o + i * 28
        out.append((e + 4, e + 8, f'debug directory entry {i} TimeDateStamp'))
        typ, size, _, ptr = struct.unpack_from('<IIII', d, e + 12)
        if typ == 2 and d[ptr:ptr + 4] == b'RSDS':
            out.append((ptr + 4, ptr + 24, f'debug directory entry {i}: CodeView build ID (GUID and age)'))
    return out


a, b = (open(p, 'rb').read() for p in sys.argv[1:3])
print(f'{sys.argv[1]}: {len(a)} bytes; {sys.argv[2]}: {len(b)} bytes')
if len(a) != len(b):
    sys.exit('sizes differ')
f = fields(a)
diff = [i for i in range(len(a)) if a[i] != b[i]]
runs = []
for i in diff:
    if runs and i == runs[-1][1]:
        runs[-1][1] = i + 1
    else:
        runs.append([i, i + 1])
for s, e in runs:
    names = [n for fs, fe, n in f if fs < e and s < fe]
    print(f'differ at 0x{s:x}-0x{e - 1:x} ({e - s} bytes): {", ".join(names) or "NOT A PER-BUILD FIELD"}')
ma, mb = bytearray(a), bytearray(b)
for s, e, _ in f:
    ma[s:e] = mb[s:e] = bytes(e - s)
print('with those fields blanked in both:', 'identical' if ma == mb else 'STILL DIFFERENT')
sys.exit(0 if ma == mb else 1)
