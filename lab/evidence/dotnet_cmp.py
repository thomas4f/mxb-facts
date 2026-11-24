#!/usr/bin/env -S python3 -I
"""Compare a rebuilt .NET assembly with a released one, byte for byte.

usage: dotnet_cmp.py <released .dll> <rebuilt .dll> [<version>]

Both files must have the same size. Lists every byte range that differs and names the field it falls in: the PE
header's build time stamp, a debug directory entry (its time stamp, or the record it points at: the CodeView record
with the build ID and the path of the PDB file on the build machine, or the PDB checksum), or the module version ID
(MVID, the #GUID metadata heap, which the compiler makes up for each build that isn't deterministic). Any other range
is "other". When a version is given (such as 0.1.8674.29660, which a project with
AssemblyVersion 0.1.* gets from the build's date and time), a range inside that version in the released file, as four
16-bit numbers (the Assembly table), as text or as UTF-16 text (the version attributes and the version resource), is
named "assembly version". The last line says whether every difference lies in those per-build fields.
"""
import struct, sys


def fields(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    out = [(pe + 8, pe + 12, 'PE header TimeDateStamp')]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    opt = pe + 24
    magic = struct.unpack_from('<H', d, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    sh = opt + struct.unpack_from('<H', d, pe + 20)[0]
    secs = []
    for i in range(nsec):
        vsize, va, size, raw = struct.unpack_from('<IIII', d, sh + i * 40 + 8)
        secs.append((va, max(vsize, size), raw))

    def off(rva):
        for va, size, raw in secs:
            if va <= rva < va + size:
                return raw + rva - va
        raise ValueError(hex(rva))

    drva, dsize = struct.unpack_from('<II', d, dd + 6 * 8)
    if dsize:
        o = off(drva)
        for i in range(dsize // 28):
            e = o + 28 * i
            typ, size, _, ptr = struct.unpack_from('<IIII', d, e + 12)
            out.append((e + 4, e + 8, f'debug entry {i} TimeDateStamp'))
            name = {2: 'CodeView record (build ID, PDB path)', 19: 'PDB checksum record'}.get(typ, f'debug record type {typ}')
            if size:
                out.append((ptr, ptr + size, f'debug entry {i}: {name}'))
    crva = struct.unpack_from('<I', d, dd + 14 * 8)[0]
    c = off(crva)
    mrva = struct.unpack_from('<I', d, c + 8)[0]
    m = off(mrva)
    vlen = struct.unpack_from('<I', d, m + 12)[0]
    p = m + 16 + vlen
    n = struct.unpack_from('<H', d, p + 2)[0]
    p += 4
    for _ in range(n):
        so, ss = struct.unpack_from('<II', d, p)
        name = d[p + 8:d.index(b'\0', p + 8)].decode()
        p = p + 8 + ((len(name) + 4) & ~3)
        if name == '#GUID':
            out.append((m + so, m + so + ss, 'metadata #GUID heap (MVID)'))
    return out


def versions(d, v):
    nums = [int(x) for x in v.split('.')]
    out = []
    for pat in (struct.pack('<4H', *nums), v.encode(), v.encode('utf-16-le')):
        i = d.find(pat)
        while i >= 0:
            out.append((i, i + len(pat), 'assembly version'))
            i = d.find(pat, i + 1)
    return out


def main():
    a, b = (open(f, 'rb').read() for f in sys.argv[1:3])
    if len(a) != len(b):
        sys.exit(f'sizes differ: {len(a)} and {len(b)}')
    fa = fields(a) + (versions(a, sys.argv[3]) if len(sys.argv) > 3 else [])
    ranges, i = [], 0
    while i < len(a):
        if a[i] != b[i]:
            j = i
            while j < len(a) and a[j] != b[j]:
                j += 1
            ranges.append((i, j))
            i = j
        i += 1
    other = 0
    for s, e in ranges:
        names = [n for fs, fe, n in fa if fs <= s and e <= fe]
        if not names:
            other += 1
        print(f'{s:#08x} {e - s:4} bytes  {names[0] if names else "other"}')
    print(f'{len(ranges)} ranges differ, {len(a)} bytes compared;',
          'every difference is in a per-build field' if not other else f'{other} ranges are in no per-build field')


main()
