#!/usr/bin/env python3
"""List the entries of a Graphics Overhaul shaders.pak ("OVP1"): after the 4-byte magic, the rest is XORed with the low byte
of an xorshift32 stream seeded 0x5eed1f2a (the plugin's pak_lookup); then a u32 count and, per entry, u32 name length, name,
u32 data length, data. Prints each entry's name, size, SHA-256 and first line. Usage: ovpak.py shaders.pak"""
import hashlib, struct, sys
d = open(sys.argv[1], 'rb').read()
assert d[:4] == b'OVP1', 'not an OVP1 pak'
b = bytearray(d[4:]); x = 0x5eed1f2a
for i in range(len(b)):
    x ^= (x << 13) & 0xffffffff; x ^= x >> 17; x ^= (x << 5) & 0xffffffff
    b[i] ^= x & 0xff
n = struct.unpack_from('<I', b, 0)[0]; o = 4
print(f'{n} entries')
for _ in range(n):
    ln = struct.unpack_from('<I', b, o)[0]; name = bytes(b[o + 4:o + 4 + ln]).decode('latin-1'); o += 4 + ln
    sz = struct.unpack_from('<I', b, o)[0]; data = bytes(b[o + 4:o + 4 + sz]); o += 4 + sz
    first = data.split(b'\n', 1)[0][:70].decode('latin-1', 'replace')
    print(f'{name}\t{sz}\t{hashlib.sha256(data).hexdigest()}\t{first}')
print(f'end at {o} of {len(b)} bytes')
