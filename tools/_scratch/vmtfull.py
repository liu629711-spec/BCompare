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
    if not va: return None
    b=rd(va,80)
    if not b: return None
    n=b[0]
    if not(1<=n<70): return None
    s=b[1:1+n].decode('latin1',errors='replace')
    return s if all(32<=ord(c)<127 for c in s) else None
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
def ann(v):
    a=f'{v:09x}'; e=att.get(a)
    return f'{e["size"]:5d}B {e["unit"]}' if e else '—'
def info(clsname):
    # find classnameptr
    for va in range(0x140e00000,0x142100000,8):
        v=u64(va)
        if v and 0x140e00000<v<0x141c9d000:
            s=sstr(v)
            if s==clsname:
                vmt=va+0x88
                return vmt,sstr(u64(vmt-0x88)),u64(vmt-0x80),u64(vmt-0x78)
    return None,None,None,None
for name in sys.argv[1:]:
    vmt,cn,isz,par=info(name)
    if not vmt: print(f'{name}: not found'); continue
    pn=sstr(u64(par-0x88)) if par else None
    print(f'== {name} VMT={hex(vmt)} size={hex(isz) if isz else None} parent={pn}')
    for o2 in range(0,0x260,8):
        v=u64(vmt+o2)
        if v and 0x140001000<=v<0x141c9d000:
            print(f'    +{o2:#05x} {hex(v):>18} {ann(v)}')
