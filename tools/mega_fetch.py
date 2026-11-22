#!/usr/bin/env python3
"""Download a public MEGA file link and decrypt it, as the MEGA web client does.

MEGA encrypts files end to end; the key is the part of the link after '#'.
This asks MEGA's public API for the download URL (no account), downloads the
encrypted bytes, decrypts them with AES-128-CTR and prints the file's name,
size and SHA-256. It checks MEGA's CBC-MAC of the file, so a wrong key or a
changed download fails.

  python3 -I tools/mega_fetch.py 'https://mega.nz/file/<id>#<key>' OUTDIR
"""
import base64, hashlib, json, os, struct, sys, urllib.request
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def b64(s):
    s = s.replace('-', '+').replace('_', '/').replace(',', '')
    return base64.b64decode(s + '=' * (-len(s) % 4))

def main(link, outdir):
    path, key = link.split('#', 1)
    fid = path.rstrip('/').split('/')[-1]
    a = struct.unpack('>8I', b64(key))
    k = struct.pack('>4I', a[0] ^ a[4], a[1] ^ a[5], a[2] ^ a[6], a[3] ^ a[7])
    iv = struct.pack('>2I', a[4], a[5]) + b'\0' * 8
    meta_mac = struct.pack('>2I', a[6], a[7])
    req = urllib.request.Request('https://g.api.mega.co.nz/cs?id=1',
        data=json.dumps([{'a': 'g', 'g': 1, 'p': fid}]).encode(),
        headers={'Content-Type': 'application/json'})
    info = json.load(urllib.request.urlopen(req, timeout=60))[0]
    if isinstance(info, int):
        sys.exit(f'MEGA API error {info}')
    at = Cipher(algorithms.AES(k), modes.CBC(b'\0' * 16)).decryptor().update(b64(info['at']))
    if not at.startswith(b'MEGA'):
        sys.exit('wrong key: attributes do not decrypt')
    name = json.loads(at[4:].rstrip(b'\0').decode())['n']
    enc = urllib.request.urlopen(info['g'], timeout=300).read()
    if len(enc) != info['s']:
        sys.exit(f'size {len(enc)} != {info["s"]}')
    data = Cipher(algorithms.AES(k), modes.CTR(iv)).decryptor().update(enc)
    # MEGA's chunked CBC-MAC (chunks of 128K, 256K, ... up to 1M)
    ecb = Cipher(algorithms.AES(k), modes.ECB()).encryptor()
    mac = b'\0' * 16
    pos, size, step = 0, len(data), 0x20000
    while pos < size:
        end = min(pos + step, size)
        cm = iv[:8] * 2
        for i in range(pos, end, 16):
            blk = data[i:i + 16].ljust(16, b'\0')
            cm = ecb.update(bytes(x ^ y for x, y in zip(cm, blk)))
        mac = ecb.update(bytes(x ^ y for x, y in zip(mac, cm)))
        pos = end
        if step < 0x100000:
            step += 0x20000
    m = struct.unpack('>4I', mac)
    if struct.pack('>2I', m[0] ^ m[1], m[2] ^ m[3]) != meta_mac:
        sys.exit('MAC mismatch: file does not match the link key')
    safe = os.path.basename(name)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, safe), 'wb') as f:
        f.write(data)
    print(f'{safe}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
