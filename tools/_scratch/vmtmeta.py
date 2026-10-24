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
def shortstr(va):
    b=rd(va,120)
    if not b: return None
    n=b[0]
    if not (1<=n<100): return None
    s=b[1:1+n].decode('latin1',errors='replace')
    return s if all(32<=ord(c)<127 for c in s) else None
def show(label,vmt,lo,hi):
    print(f'--- {label} VMT={hex(vmt)}')
    for off in range(lo,hi,8):
        v=u64(vmt+off)
        tag=shortstr(v) if v else None
        h=hex(v) if v is not None else 'None'
        print(f'    {off:+#07x} = {h:>18} {tag or ""}')
show('TDirBaseSession',0x140e4dab8,-0x68,0x8)
show('TDirSession(classnameptr 140f57240)',0x140f57240-0x40,-0x40,0x8)
