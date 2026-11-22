"""Unpack a PyInstaller program (its CArchive) without running it.

Usage: python3 -I tools/carchive.py <program.exe> <output folder>

Finds the archive by its magic bytes at the end of the file and writes every entry to the output folder; Python modules
get the suffix .pyc_raw (marshalled code without a .pyc header). Prints each entry's type code, name and size.
"""
import sys,struct,zlib,os
exe,out=sys.argv[1],sys.argv[2]
d=open(exe,'rb').read()
i=d.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e')
pkglen,toc,toclen,pyver=struct.unpack('!iiii',d[i+8:i+24])
base=i+24+64-pkglen
print('pyver',pyver,'entries at',toc)
p=base+toc;end=p+toclen
while p<end:
    es,pos,cs,_us,cf,tc=struct.unpack('!iiiiBc',d[p:p+18]); name=d[p+18:p+es].rstrip(b'\0').decode()
    p+=es
    blob=d[base+pos:base+pos+cs]
    if cf: blob=zlib.decompress(blob)
    fn=os.path.join(out,name.replace('\\','/'))
    os.makedirs(os.path.dirname(fn) or out,exist_ok=True)
    open(fn+('.pyc_raw' if tc in (b's',b'm',b'M') else ''),'wb').write(blob)
    print(tc.decode(),name,len(blob))
