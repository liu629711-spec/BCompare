import pefile,struct,sys
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def rd(va,n):
    o=rva2off(va-base); return None if o is None else data[o:o+n]
def u64(va):
    b=rd(va,8); return struct.unpack('<Q',b)[0] if b else None
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if b else None
def ustr(p):
    """Delphi UnicodeString: p->chars, len at p-4 (u32)"""
    if not p: return None
    ln=u32(p-4)
    if ln is None or not (0<ln<200): return None
    b=rd(p,ln*2)
    try:
        s=b.decode('utf-16-le')
        return s if s.isprintable() else None
    except: return None
def arr(va,n):
    return [(i, u64(va+8*i), ustr(u64(va+8*i)) if u64(va+8*i) else None) for i in range(n)]
for a in sys.argv[1:]:
    va=int(a,16)
    print(f'=== {a} -> {hex(u64(va)) if u64(va) else None} ===')
    for i,p,s in arr(u64(va),8):
        print(f'   [{i}] {hex(p) if p else None}  {s!r}')
    print(f'   raw16: {rd(va,16).hex() if rd(va,16) else None}')
