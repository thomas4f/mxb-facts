#!/usr/bin/env -S python3 -I
"""Prints the SHA-256 of each section of Windows program files (PE32 or PE32+), to compare the code of a program with the
prebuilt file it was made from (for example a PyInstaller program with PyInstaller's bootloader, whose icon and resources
the build changes but whose code it doesn't).

usage: pesect.py <file> [<file> ...]
"""
import hashlib, struct, sys

for path in sys.argv[1:] or sys.exit(__doc__):
    d = open(path, 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    assert d[pe:pe + 4] == b'PE\0\0', 'not a PE file'
    nsec, optsize = struct.unpack_from('<H', d, pe + 6)[0], struct.unpack_from('<H', d, pe + 20)[0]
    print(path)
    for i in range(nsec):
        name, vsize, _va, rawsize, rawptr = struct.unpack_from('<8sIIII', d, pe + 24 + optsize + 40 * i)
        print('  %-8s %10d %s' % (name.rstrip(b'\0').decode(), rawsize, hashlib.sha256(d[rawptr:rawptr + rawsize]).hexdigest()))
