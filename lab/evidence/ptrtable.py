#!/usr/bin/env python3
"""Print a table of entries from a PE file, each entry a run of 8-byte values (64-bit), with the text a value points to.

Usage: ptrtable.py <pe file> <start address, hex> <entries> <bytes per entry>
Each line: the entry's address, then each 8-byte value in hex, with "<text>" when the value is the address of a text in the
file. Used to read tables a compiled program keeps in its data, such as a settings table (name, type, offset, group).
"""
import struct
import sys


def sections(f):
    pe = struct.unpack_from('<I', f, 0x3c)[0]
    n = struct.unpack_from('<H', f, pe + 6)[0]
    opt = struct.unpack_from('<H', f, pe + 20)[0]
    magic = struct.unpack_from('<H', f, pe + 24)[0]
    base = struct.unpack_from('<Q', f, pe + 48)[0] if magic == 0x20b else struct.unpack_from('<I', f, pe + 52)[0]
    out = []
    for i in range(n):
        o = pe + 24 + opt + 40 * i
        vsize, va, rsize, raw = struct.unpack_from('<IIII', f, o + 8)
        out.append((base + va, max(vsize, rsize), raw, rsize))
    return out


def offset(secs, va):
    for start, size, raw, rsize in secs:
        if start <= va < start + size and va - start < rsize:
            return raw + va - start
    return None


def text(f, secs, va):
    o = offset(secs, va)
    if o is None:
        return None
    e = f.find(b'\0', o, o + 200)
    t = f[o:e] if e > o else b''
    return t.decode() if len(t) >= 2 and all(32 <= c < 127 for c in t) else None


def main():
    path, start, count, stride = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]), int(sys.argv[4])
    f = open(path, 'rb').read()
    secs = sections(f)
    for i in range(count):
        va = start + i * stride
        o = offset(secs, va)
        vals = struct.unpack_from('<%dQ' % (stride // 8), f, o)
        cells = []
        for v in vals:
            t = text(f, secs, v)
            cells.append('0x%x' % v + (' "%s"' % t if t else ''))
        print('0x%x  %s' % (va, '  '.join(cells)))


if __name__ == '__main__':
    main()
