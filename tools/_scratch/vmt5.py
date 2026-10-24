import pefile,struct,json,sys
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
    b=rd(va,120)
    if not b: return None
    n=b[0]
    if not(1<=n<100): return None
    s=b[1:1+n].decode('latin1',errors='replace')
    return s if all(32<=ord(c)<127 for c in s) else None
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
def ann(v):
    a=f'{v:09x}'; e=att.get(a)
    return f'{e["size"]:5d}B {e["unit"]}' if e else '—'
def vmt_from_classnameptr(cnp):
    """walk back to find vmtSelfPtr slot (contains VMTbase)"""
    for back in range(0x40,0x160,8):
        slot=cnp-back
        v=u64(slot)
        if v==slot+0xc8 and u64(slot+0xc8+0x40-back*0+0x40-0x40) is not None:
            # verify ClassName at VMTbase-0x88 == cnp
            if u64(v-0x88)==cnp: return v,slot
    return None,None
DEF={0x28:'vmtSafeCallException?',0x30:'vmtAfterConstruction?',0x38:'vmtBeforeDestruction?',
     0x40:'vmtDispatch?',0x48:'vmtDefaultHandler?',0x50:'vmtNewInstance?',0x58:'vmtFreeInstance?',
     0x60:'vmtDestroy?'}
for label,cnp in [('TDirSession',0x140f57240),('TDirCompareSession',0x140f582e0),('TDirMergeSession',0x140f58868),
                  ('TDirBaseSession',0x140e4da98),('TDirSessionState',0x140f33648),('TDirCompareSessionState',0x140f342b0),
                  ('TDirMergeSessionState',0x140f344e0)]:
    v,s=vmt_from_classnameptr(cnp)
    if not v: print(f'{label}: vmtSelfPtr not found'); continue
    parent=u64(v-0x78)
    print(f'== {label}: VMT={hex(v)} vmtSelfPtr@{hex(s)} TClass={hex(s)} InstanceSize={hex(u64(v-0x80))} Parent={hex(parent) if parent else None} ({sstr(u64(parent)) if parent else ""})')
