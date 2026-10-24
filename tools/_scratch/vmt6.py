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
NAMES={0x140f57240:'TDirSession',0x140f582e0:'TDirCompareSession',0x140f58868:'TDirMergeSession',
       0x140e4da98:'TDirBaseSession',0x140f33648:'TDirSessionState',0x140f342b0:'TDirCompareSessionState',
       0x140f344e0:'TDirMergeSessionState',0x141b58110:'TDirSyncSessionState',0x141b58d38:'TDirSyncSession',
       0x141b42e38:'TDirView',0x141b3c620:'TDirTree'}
out={}
for cnp,name in NAMES.items():
    vmt=cnp+0x88
    parent=u64(vmt-0x78); isz=u64(vmt-0x80)
    pn=sstr(u64(parent)) if parent else None
    print(f'== {name}: TClass={hex(cnp-0x28)} VMT={hex(vmt)} InstanceSize={hex(isz) if isz else None} Parent={hex(parent) if parent else None} ({pn})')
    slots={}
    for o2 in range(0,0x280,8):
        v=u64(vmt+o2)
        if v and 0x140001000<=v<0x141c9d000: slots[o2]=v
    out[name]=(vmt,slots,parent,pn)
    for o2,v in slots.items():
        if o2>=0xb0:
            print(f'     +{o2:#05x} {hex(v):>18} {ann(v)}')
    print()
