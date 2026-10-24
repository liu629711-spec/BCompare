import sys,struct
raw=open(r'D:\bc-official\app\BCompare.exe','rb').read()
BASE=0x140000000
def off(va):
    rva=va-BASE
    # scan section table manually
    for (n,va0,vs,pr,rs) in SEC:
        if va0<=rva<va0+vs:
            return pr+(rva-va0)
    return None
import pefile
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
SEC=[(s.Name.decode().strip('\x00'),s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def u32(va):
    o=off(va); return struct.unpack('<I',raw[o:o+4])[0] if o is not None else None
def u64(va):
    o=off(va); return struct.unpack('<Q',raw[o:o+8])[0] if o is not None else None
def delphi_ustr_ptr(va):
    """va holds pointer to UnicodeString chars; len at chars-4"""
    p=u64(va)
    if not p: return None
    ln=u32(p-4)
    if ln is None or not(0<ln<120): return None
    o=off(p)
    try:
        s=raw[o:o+ln*2].decode('utf-16-le')
        return s if s.isprintable() else None
    except: return None
def inline16(va,maxn=80):
    o=off(va); n=0
    while n<maxn:
        ch=struct.unpack('<H',raw[o+n*2:o+n*2+2])[0]
        if ch==0 or ch==0xffff: break
        n+=1
    return raw[o:o+n*2].decode('utf-16-le',errors='replace') if n else None
for a in sys.argv[1:]:
    va=int(a,16)
    print(f'{a}: ustr_ptr={delphi_ustr_ptr(va)!r}  inline16={inline16(va)!r}  u64={hex(u64(va)) if u64(va) else None}')
