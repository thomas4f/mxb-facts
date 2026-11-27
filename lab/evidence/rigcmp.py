#!/usr/bin/env python3
"""Compare the meshes of Graphics Overhaul's rig_default_mx.bin with files of the game (e.g. rider.edf and c_rider.edf from
rider/riders/default_mx/ in the MX Bikes demo's rider.pkz). Each mesh in the rig is a 32-byte name, a u32 vertex count, then,
from 88 bytes after the count, vertices of 44 bytes (position 3 floats, normal 3 floats, bone data). For every vertex it looks
for its 12-byte position, and its 24-byte position and normal, anywhere in each game file.
Usage: rigcmp.py rig_default_mx.bin <game file>..."""
import struct, sys
rig = open(sys.argv[1], 'rb').read()
for path in sys.argv[2:]:
    g = open(path, 'rb').read()
    pos = set(g[i:i + 12] for i in range(len(g) - 12)); pn = set(g[i:i + 24] for i in range(len(g) - 24))
    print(f'== {path}')
    for name in (b'lod0', b'lod1', b'lod2', b'cockpit', b'shadow'):
        o = rig.find(name + b'\0'); n = struct.unpack_from('<I', rig, o + 32)[0]; v = o + 120
        hp = sum(rig[v + 44 * k:v + 44 * k + 12] in pos for k in range(n))
        hn = sum(rig[v + 44 * k:v + 44 * k + 24] in pn for k in range(n))
        print(f'{name.decode()}: {n} vertices; position found: {hp}; position and normal found: {hn}')
