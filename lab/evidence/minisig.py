#!/usr/bin/env -S python3 -I
"""Check a minisign signature: minisig.py <public key base64> <file> <file.minisig>.

The minisign format (https://jedisct1.github.io/minisign/): the public key is "Ed" + 8-byte key ID + 32-byte Ed25519
key; the signature line is "Ed" (the file itself) or "ED" (its BLAKE2b-512 hash) + key ID + 64-byte signature; the
global signature covers the signature and the trusted comment. Prints the key IDs and whether each part verifies.
"""
import base64
import hashlib
import sys

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def verify(key, sig, data):
    try:
        key.verify(sig, data)
        return True
    except InvalidSignature:
        return False


def main():
    pk_b64, path, sig_path = sys.argv[1:4]
    pk = base64.b64decode(pk_b64)
    assert pk[:2] == b"Ed" and len(pk) == 42, "not a minisign public key"
    key_id, key = pk[2:10], Ed25519PublicKey.from_public_bytes(pk[10:])
    lines = open(sig_path, encoding="utf-8").read().splitlines()
    sig = base64.b64decode(lines[1])
    alg, sig_key_id, signature = sig[:2], sig[2:10], sig[10:74]
    trusted = lines[2].split("trusted comment: ", 1)[1]
    global_sig = base64.b64decode(lines[3])
    data = open(path, "rb").read()
    signed = hashlib.blake2b(data, digest_size=64).digest() if alg == b"ED" else data
    print("public key ID:", key_id[::-1].hex().upper())
    print("signature key ID:", sig_key_id[::-1].hex().upper(), "algorithm:", alg.decode())
    print("trusted comment:", trusted)
    print("key IDs match:", key_id == sig_key_id)
    print("file signature valid:", verify(key, signature, signed))
    print("trusted comment signature valid:", verify(key, global_sig, signature + trusted.encode()))


main()
