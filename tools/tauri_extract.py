"""Extract the web assets a Tauri app embeds in its .exe, without running it.

Usage: python3 -I tools/tauri_extract.py <app.exe> <output folder>
Needs pefile and brotli (pip install pefile brotli; not in requirements.txt, since only this script uses them).

Tauri keeps each asset as a (pointer, length) pair to its path ("/index.html", ...) followed by a (pointer, length) pair
to its brotli-compressed bytes. This scans .rdata and .data for such pairs and writes each asset under its path.
"""
import sys,struct,pefile,brotli,os
exe,out=sys.argv[1],sys.argv[2]
pe=pefile.PE(exe,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
d=open(exe,'rb').read()
secs=[(s.VirtualAddress+base,s.VirtualAddress+base+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s) for s in pe.sections]
def off(va):
    for a,b,r,s in secs:
        if a<=va<b and va-a<s.SizeOfRawData: return r+va-a
    return None
n=0
for s in pe.sections:
    name=s.Name.rstrip(b'\0')
    if name not in (b'.rdata',b'.data'): continue
    st=s.PointerToRawData; en=st+s.SizeOfRawData
    for i in range(st,en-32,8):
        p,l=struct.unpack_from('<QQ',d,i)
        if not (2<=l<300): continue
        o=off(p)
        if o is None: continue
        k=d[o:o+l]
        if not k.startswith(b'/') or not all(32<=c<127 for c in k): continue
        p2,l2=struct.unpack_from('<QQ',d,i+16)
        o2=off(p2)
        if o2 is None or not (0<l2<60_000_000): continue
        try: data=brotli.decompress(d[o2:o2+l2])
        except Exception: continue
        path=os.path.join(out,k.decode().lstrip('/'))
        os.makedirs(os.path.dirname(path) or out,exist_ok=True)
        if not os.path.exists(path):
            open(path,'wb').write(data); n+=1
print(n,'assets')
