#!/usr/bin/env -S python3 -I
"""What a release asks of Windows in rights (P10): every program file's requested execution level, the calls that install a
service or a driver, and every place its files ask for administrator rights or check for them. Nothing is run.

usage: privileges.py <release file or folder> ...

Each file given, and every file inside it, is read. Archives are unpacked into a scratch folder first, the same way the
cards' run.sh scripts unpack them: zip (and a PyInstaller program's payload.zip), NSIS and 7z with 7-Zip, PyInstaller
programs with tools/carchive.py, Electron app.asar with asar.py, .NET single-file bundles with netbundle.py. An Inno Setup
installer innoextract can't read is said to be one, and lab/evidence/innosetup.py reads its header.

For each program (a PE file that isn't a DLL; a DLL, a game plugin included, runs with the rights of the program that loads
it): its manifest's requestedExecutionLevel (no manifest means asInvoker: Windows starts it with the rights of whoever
starts it). For every PE file, its imports from the service, driver and device-install APIs. For every file, the
text that asks for or checks administrator rights (the runas verb, PowerShell's -Verb RunAs, an admin-role check, NSIS's
RequestExecutionLevel, Inno's PrivilegesRequired, electron-builder's perMachine, sc create, schtasks /RL HIGHEST,
New-Service), with the line, or for a program file the text found (ASCII and UTF-16), also inside a PyInstaller PYZ archive's
compressed modules. And every driver file (.sys, .inf) shipped. A file is printed only with a program's manifest line or a
match; the last line counts the files read.
"""
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', 'tools')

IMPORTS = re.compile(r'^(CreateService[AW]|ChangeServiceConfig2?[AW]|NtLoadDriver|ZwLoadDriver'
                     r'|SetupCopyOEMInf[AW]|DiInstallDriver[AW]|UpdateDriverForPlugAndPlayDevices[AW]|DriverPackageInstall[AW]'
                     r'|InstallHinfSection[AW]?)$')
TEXT = re.compile(r'\brunas\b|-Verb\s+RunAs|RunAsAdministrator|WindowsBuiltInRole\]?::Administrator|IsUserAnAdmin|'
                  r'IsInRole\(|RequestExecutionLevel\s+\w+|PrivilegesRequired\s*=\s*\w+|perMachine["\']?\s*[:=]\s*true|'
                  r'requireAdministrator|highestAvailable|\bsc(?:\.exe)?\s+create\b|schtasks[^\n]{0,80}/RL\s+HIGHEST|New-Service\b|'
                  r'\bnet\s+session\b', re.I)
TEXT_EXT = ('.ps1', '.psm1', '.bat', '.cmd', '.vbs', '.js', '.mjs', '.cjs', '.json', '.yml', '.yaml', '.ini', '.nsi', '.nsh',
            '.iss', '.py', '.txt', '.md', '.xml', '.manifest', '.html')
DRIVER_EXT = ('.sys', '.inf')


def pe_info(d):
    """(is a DLL, manifest count, manifest levels, service and driver imports) of a PE file, or None if it isn't one."""
    if d[:2] != b'MZ' or len(d) < 0x40:
        return None
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    if d[pe:pe + 4] != b'PE\0\0':
        return None
    nsec, optsize = struct.unpack_from('<H', d, pe + 6)[0], struct.unpack_from('<H', d, pe + 20)[0]
    is_dll = bool(struct.unpack_from('<H', d, pe + 22)[0] & 0x2000)
    opt = pe + 24
    plus = struct.unpack_from('<H', d, opt)[0] == 0x20B
    dd = opt + (112 if plus else 96)
    secs = [struct.unpack_from('<IIII', d, opt + optsize + 40 * i + 8) for i in range(nsec)]

    def off(r):
        for vs, va, rs, raw in secs:
            if va <= r < va + max(vs, rs):
                return raw + r - va
        return None

    names = []
    irva = struct.unpack_from('<I', d, dd + 8)[0]
    o = off(irva) if irva else None
    while o is not None and o + 20 <= len(d):
        oft, _, _, name, ft = struct.unpack_from('<IIIII', d, o)
        if not name:
            break
        t = off(oft or ft)
        while t is not None:
            v = struct.unpack_from('<Q' if plus else '<I', d, t)[0]
            if not v:
                break
            if not v >> (63 if plus else 31):
                h = off(v & 0x7FFFFFFF)
                if h is not None:
                    names.append(d[h + 2:d.index(b'\0', h + 2)].decode('latin-1'))
            t += 8 if plus else 4
        o += 20
    # The manifest: RT_MANIFEST (24) in the resource directory.
    levels = []
    rrva = struct.unpack_from('<I', d, dd + 16)[0]
    base = off(rrva) if rrva else None

    def entries(o):
        n1, n2 = struct.unpack_from('<HH', d, o + 12)
        for i in range(n1 + n2):
            yield struct.unpack_from('<II', d, o + 16 + 8 * i)

    def leaves(o):
        for _, ptr in entries(o):
            if ptr & 0x80000000:
                yield from leaves(base + (ptr & 0x7FFFFFFF))
            else:
                r, size = struct.unpack_from('<II', d, base + ptr)
                p = off(r)
                if p is not None:
                    yield d[p:p + size]

    manifests = 0
    if base is not None:
        for name, ptr in entries(base):
            if name == 24 and ptr & 0x80000000:
                for m in leaves(base + (ptr & 0x7FFFFFFF)):
                    manifests += 1
                    levels += re.findall(r'requestedExecutionLevel[^>]*?level=["\'](\w+)["\'][^>]*?(?:uiAccess=["\'](\w+)["\'])?',
                                         m.decode('utf-8', 'replace'))
    return is_dll, manifests, levels, [n for n in names if IMPORTS.match(n)]


def inflate_all(d):
    """Every zlib stream in a PyInstaller PYZ archive (each module is one), inflated."""
    for m in re.finditer(rb'x[\x01\x5e\x9c\xda]', d):
        try:
            z = zlib.decompressobj()
            out = z.decompress(d[m.start():m.start() + 4 * 1024 * 1024])
            if z.eof and out:
                yield out
        except zlib.error:
            pass


def strings(d):
    for m in re.finditer(rb'[\x20-\x7e]{5,}', d):
        yield m.group().decode()
    for m in re.finditer(rb'(?:[\x20-\x7e]\x00){5,}', d):
        yield m.group().decode('utf-16-le')


def unpack(path, d, work):
    """A folder with what the file holds, or None when it holds nothing this tool unpacks."""
    out = tempfile.mkdtemp(dir=work)
    low = path.lower()
    try:
        if d[:4] == b'PK\x03\x04' and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                for i in z.infolist():
                    name = i.filename.replace('\\', '/')
                    if name.endswith('/') or '..' in name.split('/'):
                        continue
                    dst = os.path.join(out, name.lstrip('/'))
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    with z.open(i) as s, open(dst, 'wb') as t:
                        shutil.copyfileobj(s, t)
            return out
        if low.endswith('.asar'):
            subprocess.run([sys.executable, '-I', os.path.join(HERE, 'asar.py'), path, out], check=True, capture_output=True)
            return out
        if d[:2] == b'MZ':
            if b'MEI\x0c\x0b\x0a\x0b\x0e' in d[-4096:] or d.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e') > 0:
                subprocess.run([sys.executable, '-I', os.path.join(TOOLS, 'carchive.py'), path, out], check=True, capture_output=True)
                return out
            if bytes.fromhex('8b1202b96a612038727b930214d7a03213f5b9e6efae3318ee3b2dce24b36aae') in d:
                subprocess.run([sys.executable, '-I', os.path.join(HERE, 'netbundle.py'), path, out], check=True, capture_output=True)
                return out
            t = subprocess.run(['7z', 'l', path], capture_output=True, text=True).stdout
            if re.search(r'^Type = (Nsis|7z)$', t, re.M):
                subprocess.run(['7z', 'x', '-y', '-o' + out, path], check=True, capture_output=True)
                return out
        elif d[:6] == b"7z\xbc\xaf'\x1c":
            subprocess.run(['7z', 'x', '-y', '-o' + out, path], check=True, capture_output=True)
            return out
    except (subprocess.CalledProcessError, zipfile.BadZipFile, OSError) as e:
        print(f'  (could not unpack: {e})')
    shutil.rmtree(out, ignore_errors=True)
    return None


READ = [0]


def scan(path, shown, work):
    READ[0] += 1
    d = open(path, 'rb').read()
    lines = []
    info = pe_info(d)
    if info:
        is_dll, manifests, levels, imports = info
        if is_dll:
            pass  # a DLL's manifest asks nothing of Windows: it runs with the rights of the program that loads it
        elif levels:
            lines.append('manifest: ' + ', '.join(f'requestedExecutionLevel {lv}' + (f' uiAccess {ui}' if ui else '') for lv, ui in levels))
        else:
            lines.append('manifest: ' + ('one, with no requestedExecutionLevel' if manifests else 'none') + ' (asInvoker)')
        if imports:
            lines.append('service/driver imports: ' + ', '.join(sorted(set(imports))))
        hits = sorted({s.strip() for s in strings(d) if TEXT.search(s) and len(s) < 300})
        lines += ['text: ' + h for h in hits]
    elif path.lower().endswith(TEXT_EXT) or b'\0' not in d[:4096]:
        text = d.decode('utf-8', 'replace')
        for n, line in enumerate(text.splitlines(), 1):
            if TEXT.search(line):
                lines.append(f'line {n}: {line.strip()[:240]}')
    elif path.lower().endswith(('.pyc', '.pyc_raw', '.dll', '.pyd', '.node', '.pyz')):
        if d[:4] == b'PYZ\0':
            d = b''.join(inflate_all(d))
        hits = sorted({s.strip() for s in strings(d) if TEXT.search(s) and len(s) < 300})
        lines += ['text: ' + h for h in hits]
    if path.lower().endswith(DRIVER_EXT):
        lines.append('driver file')
    if lines:
        print(shown)
        for line in lines:
            print('  ' + line)
    if 'Inno Setup Setup Data' in d[:4 * 1024 * 1024].decode('latin-1') and info:
        r = subprocess.run(['innoextract', '-l', path], capture_output=True, text=True)
        if r.returncode:
            print('  an Inno Setup installer that innoextract can\'t read; innosetup.py reads its rights')
    inner = unpack(path, d, work)
    if inner:
        walk(inner, shown + ' > ', work)
        shutil.rmtree(inner, ignore_errors=True)


def walk(folder, prefix, work):
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            scan(p, prefix + os.path.relpath(p, folder), work)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    work = tempfile.mkdtemp()
    try:
        for a in sys.argv[1:]:
            if os.path.isdir(a):
                walk(a, '', work)
            else:
                scan(a, a, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(f'{READ[0]} files read')


main()
