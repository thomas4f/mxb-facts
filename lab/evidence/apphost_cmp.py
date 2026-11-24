#!/usr/bin/env -S python3 -I
"""Compare a .NET single-file program with the apphost.exe it was made from (the .NET host template from Microsoft's
NuGet package Microsoft.NETCore.App.Host.<rid>).

usage: apphost_cmp.py <apphost.exe> <program.exe>

For each section of the template, says whether the program's section of the same name has the same bytes; for a section
that differs, lists the differing offsets and says whether they all lie in the two fields the SDK writes into the
template: the 8 bytes just before the bundle marker (the offset of the bundle header) and the app's file name, written
over the template's placeholder (the text of the SHA-256 of "foobar", 64 bytes); it prints that name. Then lists the sections only the program has
(.rsrc: the icon, version and manifest resources the SDK copies in from the app's assembly on Windows).
"""
import struct, sys

PLACEHOLDER = b'c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2'
MARKER = bytes.fromhex('8b1202b96a612038727b930214d7a03213f5b9e6efae3318ee3b2dce24b36aae')


def sections(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec, optsize = struct.unpack_from('<H', d, pe + 6)[0], struct.unpack_from('<H', d, pe + 20)[0]
    out = {}
    for i in range(nsec):
        o = pe + 24 + optsize + 40 * i
        name = d[o:o + 8].rstrip(b'\0').decode()
        size, raw = struct.unpack_from('<II', d, o + 16)
        out[name] = (raw, d[raw:raw + size])
    return out


def main():
    a, b = (open(f, 'rb').read() for f in sys.argv[1:3])
    sa, sb = sections(a), sections(b)
    field = b.find(MARKER) - 8
    ph = a.find(PLACEHOLDER)
    fields = [(field, field + 8)] + ([(ph, ph + len(PLACEHOLDER))] if ph >= 0 else [])
    if ph >= 0:
        print('app name written over the placeholder:', b[ph:b.index(b'\0', ph)].decode())
    for name, (raw, data) in sa.items():
        if name not in sb:
            print(f'{name:8} missing from the program')
            continue
        rb, other = sb[name]
        if data == other:
            print(f'{name:8} {len(data):7} bytes: same')
            continue
        diff = [i for i in range(min(len(data), len(other))) if data[i] != other[i]]
        inside = all(any(s <= rb + i < e for s, e in fields) for i in diff) and len(data) == len(other)
        runs = []
        for i in diff:
            if runs and runs[-1][1] == i - 1:
                runs[-1][1] = i
            else:
                runs.append([i, i])
        print(f'{name:8} {len(data):7} bytes: {len(diff)} bytes differ, at file offsets',
              ', '.join(f'{rb + x:#x}-{rb + y:#x}' if y > x else f'{rb + x:#x}' for x, y in runs),
              '- all in those two fields' if inside else '- NOT only in those two fields')
    for name in sb:
        if name not in sa:
            print(f'{name:8} {len(sb[name][1]):7} bytes: only in the program')


main()
