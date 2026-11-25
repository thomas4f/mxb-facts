#!/usr/bin/env -S python3 -I
"""Lists the files in the MXBP payload an installer keeps as its RT_RCDATA resource (MXB Ragdoll's setup): for each, its
name, size, whether its CRC-32 matches the one stored beside it, and its SHA-256. The payload is: "MXBP", a 32-bit file
count, then per file a 16-bit name length, the name, a 32-bit size, a 32-bit CRC-32 and the bytes, stored as they are.

usage: mxbp.py <setup.exe>
"""
import hashlib, struct, sys, zlib


def rcdata(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec, optsize = struct.unpack_from('<H', d, pe + 6)[0], struct.unpack_from('<H', d, pe + 20)[0]
    opt = pe + 24
    dd = opt + (112 if struct.unpack_from('<H', d, opt)[0] == 0x20B else 96)
    rva = struct.unpack_from('<I', d, dd + 2 * 8)[0]
    secs = [struct.unpack_from('<IIII', d, opt + optsize + 40 * i + 8) for i in range(nsec)]

    def off(r):
        return next(raw + r - va for vs, va, rs, raw in secs if va <= r < va + max(vs, rs))

    base = off(rva)

    def entries(o):
        n1, n2 = struct.unpack_from('<HH', d, o + 12)
        for i in range(n1 + n2):
            yield struct.unpack_from('<II', d, o + 16 + 8 * i)

    for t, p1 in entries(base):
        if t != 10:  # RT_RCDATA
            continue
        for _, p2 in entries(base + (p1 & 0x7fffffff)):
            for _, p3 in entries(base + (p2 & 0x7fffffff)):
                r, size = struct.unpack_from('<II', d, base + p3)
                yield d[off(r):off(r) + size]


def main():
    for blob in rcdata(open(sys.argv[1], 'rb').read()):
        print(f'RT_RCDATA resource, {len(blob)} bytes, starts with {blob[:4]!r}')
        if blob[:4] != b'MXBP':
            continue
        n, o = struct.unpack_from('<I', blob, 4)[0], 8
        for _ in range(n):
            ln = struct.unpack_from('<H', blob, o)[0]
            name = blob[o + 2:o + 2 + ln].decode()
            o += 2 + ln
            size, crc = struct.unpack_from('<II', blob, o)
            data = blob[o + 8:o + 8 + size]
            o += 8 + size
            print(f'{hashlib.sha256(data).hexdigest()}  {name}  ({size} bytes, CRC-32 {"matches" if zlib.crc32(data) == crc else "differs"})')
        print(f'{n} files, {o} of {len(blob)} bytes read')


main()
