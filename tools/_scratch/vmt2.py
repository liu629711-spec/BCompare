import pefile,struct,json,os
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
def shortstr(va):
    b=rd(va,120)
    if not b: return None
    n=b[0]
    if not (1<=n<100): return None
    s=b[1:1+n].decode('latin1',errors='replace')
    return s if all(32<=ord(c)<127 for c in s) else None
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
PSE=r'D:\Rea\extracted\pseudocode'
def info(v):
    a=f'{v:09x}'
    e=att.get(a)
    if e: return f'size={e["size"]:5d} {e["unit"]}'
    return 'NOT-IN-CORPUS'
for label,cn in [('TDirSession',0x140f57240),('TDirCompareSession',0x140f582e0),('TDirMergeSession',0x140f58868),('TDirBaseSession',0x140e4da98)]:
    print('='*80); print(f'== {label}  ClassNamePtr@{hex(cn)}')
    for va in range(cn, cn+0x28, 8):
        v=u64(va)
        ss=shortstr(v) if v else None
        print(f'  {hex(va)} = {hex(v) if v else None} {ss or ""}')
