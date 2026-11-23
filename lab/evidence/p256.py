#!/usr/bin/env -S python3 -I
"""ECDSA P-256 checks for release signatures, with openssl doing the verifying.

usage: p256.py find <hex start of the key> <file>...     every place a raw 64-byte public key (X then Y) starting
                                                         with those bytes sits in each file, and the whole key
       p256.py verify <key hex> <signature file> <signed file>
                                                         verifies a raw r||s signature (written as hex) of the file's
                                                         SHA-256, as Windows BCryptVerifySignature does
       p256.py verify-der <key hex> <DER signature file> <text>
                                                         verifies a DER-encoded signature of the SHA-256 of the text
                                                         (written to a temporary file as it is, with no newline)
"""
import os, re, subprocess, sys, tempfile


def der_int(b):
    b = b.lstrip(b'\0')
    if not b or b[0] & 0x80: b = b'\0' + b
    return b'\x02' + bytes([len(b)]) + b


if sys.argv[1] == 'find':
    pre = bytes.fromhex(sys.argv[2])
    for f in sys.argv[3:]:
        d = open(f, 'rb').read()
        hits = [m.start() for m in re.finditer(re.escape(pre), d)]
        for i in hits: print(f'{f}: offset 0x{i:x}: {d[i:i + 64].hex()}')
        if not hits: print(f'{f}: not found')
elif sys.argv[1] == 'verify-der':
    key, der, text = bytes.fromhex(sys.argv[2]), open(sys.argv[3], 'rb').read(), sys.argv[4]
    assert len(key) == 64, 'a P-256 key is 64 bytes'
    spki = bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d030107034200') + b'\x04' + key
    with tempfile.TemporaryDirectory() as t:
        open(os.path.join(t, 'k.der'), 'wb').write(spki)
        open(os.path.join(t, 'm.txt'), 'wb').write(text.encode())
        r = subprocess.run(['openssl', 'dgst', '-sha256', '-verify', os.path.join(t, 'k.der'), '-keyform', 'DER',
                            '-signature', sys.argv[3], os.path.join(t, 'm.txt')], capture_output=True, text=True)
    print(f'message: {text}')
    print((r.stdout + r.stderr).strip())
    sys.exit(r.returncode)
else:
    key, sig, msg = bytes.fromhex(sys.argv[2]), bytes.fromhex(open(sys.argv[3]).read().strip()), sys.argv[4]
    assert len(key) == 64 and len(sig) == 64, 'a P-256 key and signature are 64 bytes each'
    spki = bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d030107034200') + b'\x04' + key
    body = der_int(sig[:32]) + der_int(sig[32:])
    with tempfile.TemporaryDirectory() as t:
        open(os.path.join(t, 'k.der'), 'wb').write(spki)
        open(os.path.join(t, 's.der'), 'wb').write(b'\x30' + bytes([len(body)]) + body)
        r = subprocess.run(['openssl', 'dgst', '-sha256', '-verify', os.path.join(t, 'k.der'), '-keyform', 'DER',
                            '-signature', os.path.join(t, 's.der'), msg], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip())
    sys.exit(r.returncode)
