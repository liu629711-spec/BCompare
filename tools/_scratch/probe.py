import pefile,struct,sys
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def off(va):
    rva=va-base
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def rd(va,n):
    o=off(va); return None if o is None else data[o:o+n]
def u64(va):
    b=rd(va,8); return struct.unpack('<Q',b)[0] if b else None
def sstr(va):
    if not va: return None
    b=rd(va,80)
    if not b: return None
    n=b[0]
    if not(1<=n<70): return None
    s=b[1:1+n].decode('latin1',errors='replace')
    return s if all(32<=ord(c)<127 for c in s) else None
def probe(vmt,label):
    v1=u64(vmt-0xc8); v2=u64(vmt-0x88); v3=u64(vmt-0x80); v4=u64(vmt-0x78)
    pcn=sstr(u64(v4-0x88)) if v4 else None
    print(f'{label}: VMT={hex(vmt)}')
    print(f'    selfptr(-0xc8)={hex(v1) if v1 else None} ClassName(-0x88)={sstr(v2)!r} InstanceSize(-0x80)={hex(v3) if v3 else None}')
    print(f'    ParentVMT(-0x78)={hex(v4) if v4 else None} -> {pcn!r}')
for a in sys.argv[1:]:
    probe(int(a,16),sys.argv[0])
