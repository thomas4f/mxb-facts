#!/usr/bin/env -S python3.15 -I
"""Reads the Python code of a PyInstaller program without running it, after tools/carchive.py has unpacked it.

usage: pyinst.py code <module.pyc_raw> [<function> ...]   every function of the module, one line per source line: the line
                                                          number, then its bytecode instructions with their names and
                                                          constants (all functions, or only those named, by qualified name)
       pyinst.py pyz <PYZ.pyz>                            every module in the PYZ archive (the bundled Python modules)
       pyinst.py consts <PYZ.pyz> <module>                the text constants of one module in the PYZ archive
       pyinst.py pyzcode <PYZ.pyz> <module> [<function> ...]  like code, for a module in the PYZ archive

Must run under the Python version the program bundles (its pythonXY.dll), because bytecode changes between versions. It only
loads code objects with marshal and lists them with dis; it never executes them.
"""
import dis, marshal, struct, sys, zlib

SKIP = {'RESUME', 'NOT_TAKEN', 'CACHE', 'POP_TOP', 'NOP', 'PUSH_NULL', 'COPY', 'SWAP', 'POP_EXCEPT', 'END_FOR', 'POP_ITER', 'TO_BOOL'}


def show(co, only):
    if not only or co.co_qualname in only:
        print('=== %s (line %d)' % (co.co_qualname, co.co_firstlineno))
        cur, parts = None, []
        for ins in dis.get_instructions(co):
            if ins.opname in SKIP:
                continue
            ln = ins.positions.lineno if ins.positions else None
            if ln != cur and ln is not None:
                if parts:
                    print('  %s: %s' % (cur, ' | '.join(parts)))
                cur, parts = ln, []
            a = ins.argrepr
            if hasattr(ins.argval, 'co_code'):
                a = '<code %s>' % ins.argval.co_qualname
            parts.append((ins.opname + (' ' + a if a else '')).replace(' + NULL|self', '').replace(' + NULL', ''))
        if parts:
            print('  %s: %s' % (cur, ' | '.join(parts)))
    for k in co.co_consts:
        if hasattr(k, 'co_code'):
            show(k, only)


def pyz(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'PYZ\0', 'not a PYZ archive'
    toc = marshal.loads(d[struct.unpack('!i', d[8:12])[0]:])
    return d, dict(toc)


cmd = sys.argv[1]
if cmd == 'code':
    show(marshal.loads(open(sys.argv[2], 'rb').read()), set(sys.argv[3:]))
elif cmd == 'pyz':
    for name in sorted(pyz(sys.argv[2])[1]):
        print(name)
elif cmd == 'pyzcode':
    d, toc = pyz(sys.argv[2])
    _, pos, ln = toc[sys.argv[3]]
    show(marshal.loads(zlib.decompress(d[pos:pos + ln])), set(sys.argv[4:]))
elif cmd == 'consts':
    d, toc = pyz(sys.argv[2])
    _, pos, ln = toc[sys.argv[3]]
    co = marshal.loads(zlib.decompress(d[pos:pos + ln]))
    for k in co.co_consts:
        if isinstance(k, str):
            print(repr(k))
else:
    sys.exit(__doc__)
