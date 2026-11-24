#!/usr/bin/env -S python3 -I
"""Check a raw Ed25519 signature: ed25519_sig.py <public key hex> <file> <file.sig>.

The .sig file holds the base64 of the 64-byte signature over the file's exact bytes (the format Pitbox's
actualizar.verificar_firma reads). Prints "valid" or "INVALID" for the file.
"""
import base64
import sys

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

key_hex, path, sig_path = sys.argv[1:4]
key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(key_hex))
sig = base64.b64decode(open(sig_path, 'rb').read().strip(), validate=True)
try:
    key.verify(sig, open(path, 'rb').read())
    print(f'{path}: valid Ed25519 signature ({len(sig)} bytes) for key {key_hex}')
except InvalidSignature:
    print(f'{path}: INVALID signature')
    sys.exit(1)
