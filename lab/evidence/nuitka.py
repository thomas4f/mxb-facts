#!/usr/bin/env python3
"""Reads the constants of a Nuitka program without running it.

usage: nuitka.py blocks <program.exe>            every module's block of constants: its offset in the file, name and size
       nuitka.py consts <program.exe> <module>   the text in one module's block, one constant per line, in the order
                                                  the block holds them
       nuitka.py raw <program.exe> <module> <text> <n>  <n> bytes of one module's block from the first <text> in it, as
                                                  Python shows bytes (for constants that aren't text: True is 't', False
                                                  'F', an empty text 's', an empty list 'L' and a 0, a number 'l' and its
                                                  digits)

Nuitka compiles Python modules to C, so their code is machine code, but each module keeps its constants (names of the
functions and attributes it uses, its texts, numbers) in a block of its own: the module name, a NUL, a 4-byte size, then
that many bytes ending in '.'. Each text constant there starts with a one-letter type ('a' a name, 'u' a text, 'c' a
C string, 'w' one character) and ends with a NUL. This lists them as they are; it never runs the program.
"""
import re, struct, sys


def blocks(d):
    for m in re.finditer(rb'(?<=\.)([A-Za-z_][\w.\-]{0,100})\x00', d):
        j = m.end() - 1
        size = struct.unpack('<I', d[j + 1:j + 5])[0]
        if 0 < size < 5_000_000 and d[j + 5 + size - 1:j + 5 + size] == b'.':
            yield m.start(), m.group(1).decode(), j + 5, size


def consts(blob):
    for m in re.finditer(rb'[\x09\x20-\x7e\x80-\xff]{3,}', blob):
        s = m.group().decode('utf-8', 'replace')
        for line in s.split('\n'):
            if line.strip():
                print(line)


cmd, exe = sys.argv[1], sys.argv[2]
d = open(exe, 'rb').read()
if cmd == 'blocks':
    for off, name, start, size in blocks(d):
        print('%d %s %d' % (off, name, size))
elif cmd == 'consts':
    for off, name, start, size in blocks(d):
        if name == sys.argv[3]:
            consts(d[start:start + size])
            break
    else:
        sys.exit('no such module')
elif cmd == 'raw':
    for off, name, start, size in blocks(d):
        if name == sys.argv[3]:
            b = d[start:start + size]
            i = b.find(sys.argv[4].encode())
            if i < 0:
                sys.exit('not found')
            print(b[i:i + int(sys.argv[5])])
            break
