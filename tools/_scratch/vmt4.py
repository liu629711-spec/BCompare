import pefile,struct,json,sys
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
def shortstr(va):
    b=rd(va,120)
    if not b: return None
    n=b[0]
    if not (1<=n<100): return None
    s=b[1:1+n].decode('latin1',errors='replace')
    return s if all(32<=ord(c)<127 for c in s) else None
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
def ann(v):
    a=f'{v:09x}'; e=att.get(a)
    if e: return f'{e["size"]:5d}B {e["unit"]}'
    ss=shortstr(v)
    return f'STR {ss!r}' if ss else '—'
def vmt_of(classnameptr):
    """classname at base+0x40 -> base = ptr-0x40"""
    b=classnameptr-0x40
    cn=shortstr(u64(classnameptr))
    isz=u64(classnameptr+8)
    parent=u64(classnameptr+0x10)
    return b,cn,isz,parent
for cnptr in [int(x,16) for x in sys.argv[1:]]:
    b,cn,isz,parent=vmt_of(cnptr)
    pn=shortstr(u64(parent+0x40)) if parent else None
    print(f'=== {cn}  VMTbase={hex(b)} InstanceSize={hex(isz) if isz else None} Parent={hex(parent) if parent else None} ({pn}) ===')
    # walk slots 0..0x1f0
    for off in range(0xb0,0x240,8):
        v=u64(b+off)
        if not v: continue
        print(f'   +{off:#05x}  {hex(v):>18}  {ann(v)}')
    print()
