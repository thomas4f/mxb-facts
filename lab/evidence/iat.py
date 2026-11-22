#!/usr/bin/env -S python3 -I
"""Prints the import address table of a Windows program file (32- or 64-bit): one line per slot, its address and the function
the program calls through it, so a `call *...(%rip) # 0x...` line in `objdump -d` can be read as a named call.

usage: iat.py <file.dlo|file.exe>
"""
import struct, sys

d = open(sys.argv[1], 'rb').read()
pe = struct.unpack_from('<I', d, 0x3C)[0]
assert d[pe:pe + 4] == b'PE\0\0', 'not a PE file'
nsec, optsize = struct.unpack_from('<H', d, pe + 6)[0], struct.unpack_from('<H', d, pe + 20)[0]
opt = pe + 24
magic = struct.unpack_from('<H', d, opt)[0]
assert magic in (0x10B, 0x20B), 'not a PE32 or PE32+ file'
w = 8 if magic == 0x20B else 4  # bytes per table slot
base = struct.unpack_from('<Q', d, opt + 24)[0] if w == 8 else struct.unpack_from('<I', d, opt + 28)[0]
imp_rva = struct.unpack_from('<I', d, opt + (112 if w == 8 else 96) + 8)[0]
secs = [struct.unpack_from('<8sIIII', d, opt + optsize + 40 * i) for i in range(nsec)]


def off(rva):
    for _n, vsize, va, rsize, raw in secs:
        if va <= rva < va + max(vsize, rsize): return rva - va + raw
    raise ValueError(hex(rva))


def cstr(o): return d[o:d.index(b'\0', o)].decode('ascii', 'replace')


i = off(imp_rva)
while True:
    ilt, _t, _f, name, iat = struct.unpack_from('<IIIII', d, i)
    if not name: break
    dll, k = cstr(off(name)), 0
    while True:
        e = struct.unpack_from('<Q' if w == 8 else '<I', d, off(ilt or iat) + w * k)[0]
        if not e: break
        fn = f'#{e & 0xFFFF}' if e >> (8 * w - 1) else cstr(off(e & 0x7FFFFFFF) + 2)
        print(f'0x{base + iat + w * k:x}  {dll}!{fn}')
        k += 1
    i += 20
