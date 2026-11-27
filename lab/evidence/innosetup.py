#!/usr/bin/env -S python3 -I
"""Reads the setup header of an Inno Setup 6.7 installer, which innoextract 1.9 (its newest release) can't read: the
installer's name and version strings, its default folder, and the rights it asks Windows for (PrivilegesRequired and
PrivilegesRequiredOverridesAllowed, P10). Nothing is run.

usage: innosetup.py <setup.exe>

The loader's offset table (marked "rDlPtS", revision 2) gives where the setup data starts. There, after the 64-byte ID
"Inno Setup Setup Data (6.7.0)" and Inno's encryption header, comes a compressed block: a CRC32 over its size (8 bytes)
and its compressed flag, then 4096-byte chunks, each after its own CRC32, holding LZMA data (5 bytes of properties, then
the raw stream). Unpacked, it starts with TSetupHeader: 39 String and 4 AnsiString fields, each a 32-bit length then its
bytes, then the fixed fields. The layout is Inno Setup 6.7.0's own, from Projects/Src/Shared.Struct.pas at its tag is-6_7_0
(https://github.com/jrsoftware/issrc/blob/is-6_7_0/Projects/Src/Shared.Struct.pas, TSetupHeader); every CRC is checked.
"""
import lzma
import struct
import sys
import zlib

STRINGS = ('AppName AppVerName AppId AppCopyright AppPublisher AppPublisherURL AppSupportPhone AppSupportURL AppUpdatesURL '
           'AppVersion DefaultDirName DefaultGroupName BaseFilename UninstallFilesDir UninstallDisplayName UninstallDisplayIcon '
           'AppMutex DefaultUserInfoName DefaultUserInfoOrg DefaultUserInfoSerial AppReadmeFile AppContact AppComments '
           'AppModifyPath CreateUninstallRegKey Uninstallable CloseApplicationsFilter SetupMutex ChangesEnvironment '
           'ChangesAssociations ArchitecturesAllowed ArchitecturesInstallIn64BitMode CloseApplicationsFilterExcludes '
           'SevenZipLibraryName UsePreviousAppDir UsePreviousGroup UsePreviousSetupType UsePreviousTasks '
           'UsePreviousUserInfo').split()
ANSI = 4
PRIVILEGES = ('none', 'poweruser', 'admin', 'lowest')
SHOWN = ('AppName', 'AppVersion', 'DefaultDirName', 'UsePreviousAppDir')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = open(sys.argv[1], 'rb').read()
    j = d.find(b'rDlPtS\xcd\xe6\xd7\x7b\x0b\x2a')
    if j < 0 or struct.unpack_from('<I', d, j + 12)[0] != 2:
        sys.exit('no Inno Setup loader offset table, revision 2')
    i = struct.unpack_from('<Q', d, j + 40)[0]
    sid = d[i:i + 64].rstrip(b'\0').decode('latin-1')
    print(f'setup data at {i}: {sid}')
    if sid != 'Inno Setup Setup Data (6.7.0)':
        sys.exit('not Inno Setup 6.7.0 setup data; this layout is 6.7.0\'s')
    for p in range(i + 64, i + 256):
        if zlib.crc32(d[p + 4:p + 13]) == struct.unpack_from('<I', d, p)[0]:
            break
    else:
        sys.exit('no compressed block header after the ID')
    size, compressed = struct.unpack_from('<QB', d, p + 4)
    if not compressed:
        sys.exit('the header block is stored uncompressed; not handled')
    q, left, raw = p + 13, size, b''
    while left > 0:
        n = min(4096, left - 4)
        if zlib.crc32(d[q + 4:q + 4 + n]) != struct.unpack_from('<I', d, q)[0]:
            sys.exit('chunk CRC mismatch')
        raw, q, left = raw + d[q + 4:q + 4 + n], q + 4 + n, left - 4 - n
    lc, r = raw[0] % 9, raw[0] // 9
    h = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA1, 'lc': lc, 'lp': r % 5, 'pb': r // 5,
                                                         'dict_size': struct.unpack_from('<I', raw, 1)[0]}]).decompress(raw[5:])
    print(f'header block: {size} bytes stored, {len(h)} unpacked, every CRC matches')
    o, values = 0, {}
    for k in range(len(STRINGS) + ANSI):
        n = struct.unpack_from('<I', h, o)[0]
        if k < len(STRINGS):
            values[STRINGS[k]] = h[o + 4:o + 4 + n].decode('utf-16-le')
        o += 4 + n
    for k in SHOWN:
        print(f'{k}: {values[k]!r}')
    # The fixed fields, in TSetupHeader's order, up to the two this reads.
    o += 17 * 4            # NumLanguageEntries .. NumUninstallRunEntries
    o += 2 * 10            # MinVersion, OnlyBelowVersion (TSetupVersionData: 2 Cardinal, 1 Word)
    o += 2 * 4             # WizardSizePercentX, WizardSizePercentY
    o += 1 + 1             # WizardDarkStyle, WizardImageAlphaFormat
    o += 3 * 4 + 3 * 4     # the six wizard colours
    o += 2 + 1             # WizardImageOpacity, WizardBackImageOpacity, WizardLightControlStyling
    o += 8 + 4             # ExtraDiskSpaceRequired, SlicesPerDisk
    o += 1 + 1             # UninstallLogMode, DirExistsWarning
    pr, over = h[o], h[o + 1]
    names = [n for b, n in ((1, 'commandline'), (2, 'dialog')) if over & b] or ['none']
    print(f'PrivilegesRequired: {PRIVILEGES[pr] if pr < len(PRIVILEGES) else pr} (byte {o} of the header: {pr})')
    print(f'PrivilegesRequiredOverridesAllowed: {", ".join(names)} (byte {o + 1}: {over})')


main()
