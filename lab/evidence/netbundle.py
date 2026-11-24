#!/usr/bin/env python3
"""List or unpack the files of a .NET single-file bundle (an apphost .exe with the app's files appended).

Usage: netbundle.py <bundle.exe> [<out folder>]
It finds the bundle header through the 32-byte marker the .NET host searches for (the 8 bytes before it give the
header's offset), then prints each file's offset, size, compressed size, type and path, with its SHA-256, and writes it
to <out folder> when one is given (compressed entries are inflated). Nothing in the file is run.
Format: dotnet/runtime src/installer/managed/Microsoft.NET.HostModel/Bundle (header versions 1 to 6).
"""
import hashlib, os, struct, sys, zlib

MARKER = bytes.fromhex('8b1202b96a612038727b930214d7a03213f5b9e6efae3318ee3b2dce24b36aae')
TYPES = {0: 'Unknown', 1: 'Assembly', 2: 'NativeBinary', 3: 'DepsJson', 4: 'RuntimeConfigJson', 5: 'Symbols'}


def string(d, p):
    n = s = 0
    while True:
        b = d[p]; p += 1
        n |= (b & 0x7f) << s; s += 7
        if b < 0x80:
            break
    return d[p:p + n].decode('utf-8'), p + n


def main():
    d = open(sys.argv[1], 'rb').read()
    out = sys.argv[2] if len(sys.argv) > 2 else None
    i = d.find(MARKER)
    if i < 8:
        sys.exit('no bundle marker')
    hdr = struct.unpack_from('<q', d, i - 8)[0]
    major, minor, count = struct.unpack_from('<IIi', d, hdr)
    bid, p = string(d, hdr + 12)
    print(f'bundle header at {hdr:#x}: version {major}.{minor}, {count} files, bundle ID {bid}')
    if major >= 2:
        p += 8 * 4 + 8  # deps.json and runtimeconfig.json locations, flags
    for _ in range(count):
        off, size = struct.unpack_from('<qq', d, p); p += 16
        csize = 0
        if major >= 6:
            csize = struct.unpack_from('<q', d, p)[0]; p += 8
        typ = d[p]; p += 1
        path, p = string(d, p)
        raw = d[off:off + (csize or size)]
        data = zlib.decompress(raw, -15) if csize else raw
        assert len(data) == size, path
        print(f'{off:#010x} {size:9} {csize:9} {TYPES.get(typ, typ):17} {hashlib.sha256(data).hexdigest()}  {path}')
        if out:
            f = os.path.join(out, *path.split('/'))
            os.makedirs(os.path.dirname(f) or out, exist_ok=True)
            open(f, 'wb').write(data)


main()
