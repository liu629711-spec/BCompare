import pefile,struct,json
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
def ann(v):
    a=f'{v:09x}'
    e=att.get(a)
    if e: return f'{e["size"]:5d}B {e["unit"]}'
    ss=shortstr(v)
    if ss: return f'STR {ss!r}'
    return '—'
lo,hi=0x140f57200,0x140f57600
for va in range(lo,hi,8):
    v=u64(va)
    if v is None: print(hex(va),'<no data>'); continue
    mark='*' if 0x140f5a000<=v<0x140f5c000 else ' '
    print(f'{hex(va)} {mark} {hex(v):>18}  {ann(v)}')
