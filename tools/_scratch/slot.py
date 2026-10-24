import pefile,struct,json,sys,re,collections
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
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
PSE=r'D:\Rea\extracted\pseudocode'
def ann(v):
    a=f'{v:09x}'; e=att.get(a)
    return f'{e["size"]:5d}B {e["unit"]}' if e else '—'
# collect *param_1 + 0xNNN used in DirSession.pas
offs=collections.Counter()
for k,v in att.items():
    if v['unit']!='DirSession.pas': continue
    t=open(f'{PSE}\{k}.c',encoding='utf-8',errors='replace').read()
    for m in re.finditer(r'\*param_1 \+ (0x[0-9a-f]+)', t):
        offs[int(m.group(1),16)]+=1
print('DirSession.pas virtual slot offsets used:', sorted(hex(o) for o in offs))
for cref in (0x140f57200,0x140f57298):
    print(f'\n=== assuming classref = {hex(cref)} ===')
    for o in sorted(offs):
        v=u64(cref+o)
        print(f'   VMT+{o:#06x} = {hex(v) if v else None:>18}  {ann(v) if v else ""}')
