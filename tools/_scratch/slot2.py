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
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
def ann(v):
    a=f'{v:09x}'; e=att.get(a)
    return f'{e["size"]:5d}B {e["unit"]}' if e else '—'
slots={'0x178':None,'0x188':None,'0x1a8':None,'0x1d8':None,'0x1e0':None,'0x1e8':None,'0x1f0':None,'0x220':None,'0x228':None,'0xe8':None}
for label,vmt in [('TDirSession@140f57200',0x140f57200),('TDirCompareSession@140f582a0',0x140f582a0),('TDirMergeSession@140f58828',0x140f58828),('TDirBaseSession@140e4da58',0x140e4da58)]:
    print(f'=== {label} ===')
    for s in slots:
        off=int(s,16); v=u64(vmt+off)
        print(f'  +{s}: {hex(v) if v else None:>18}  {ann(v) if v else ""}')
