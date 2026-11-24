#!/usr/bin/env -S python3.12 -I
"""Compares the Python code a PyInstaller program carries with the code compiled from a source file, without running either.

usage: pycmp.py raw <module.pyc_raw> <source.py>          a module tools/carchive.py wrote (marshalled code, no header)
       pycmp.py pyz <PYZ.pyz> <module> <source.py>        a module in the PYZ archive

Must run under the Python version the program bundles (its pythonXY.dll): it compiles <source.py> with compile(), loads the
bundled code with marshal (never executes it), and compares the two code objects field by field, nested functions and
classes included. Only co_filename is left out, because it holds the path of the machine that built it. Prints MATCH, or
each difference with the qualified name of the function it is in.
"""
import marshal, struct, sys, zlib

FIELDS = ('co_code', 'co_names', 'co_varnames', 'co_freevars', 'co_cellvars', 'co_argcount', 'co_posonlyargcount',
          'co_kwonlyargcount', 'co_nlocals', 'co_stacksize', 'co_flags', 'co_firstlineno', 'co_qualname', 'co_name',
          'co_linetable', 'co_exceptiontable')


def diff(a, b, out):
    for f in FIELDS:
        if getattr(a, f) != getattr(b, f):
            out.append('%s: %s differs' % (a.co_qualname, f))
    if len(a.co_consts) != len(b.co_consts):
        out.append('%s: number of constants differs' % a.co_qualname)
        return
    for x, y in zip(a.co_consts, b.co_consts):
        if hasattr(x, 'co_code') and hasattr(y, 'co_code'):
            diff(x, y, out)
        elif type(x) is not type(y) or x != y:
            out.append('%s: constant %r differs from %r' % (a.co_qualname, x, y))


def main():
    if sys.argv[1:2] == ['raw'] and len(sys.argv) == 4:
        built, src = marshal.loads(open(sys.argv[2], 'rb').read()), sys.argv[3]
    elif sys.argv[1:2] == ['pyz'] and len(sys.argv) == 5:
        d = open(sys.argv[2], 'rb').read()
        assert d[:4] == b'PYZ\0', 'not a PYZ archive'
        toc = dict(marshal.loads(d[struct.unpack('!i', d[8:12])[0]:]))
        _, pos, ln = toc[sys.argv[3]]
        built, src = marshal.loads(zlib.decompress(d[pos:pos + ln])), sys.argv[4]
    else:
        sys.exit(__doc__)
    fresh = compile(open(src, 'rb').read(), src, 'exec', dont_inherit=True)
    out = []
    diff(built, fresh, out)
    print('\n'.join(out) if out else 'MATCH')
    return 1 if out else 0


if __name__ == '__main__':
    sys.exit(main())
