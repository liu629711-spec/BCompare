import pefile,struct
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
d=pe.__data__
def off(va):
    rva=va-pe.OPTIONAL_HEADER.ImageBase
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def u64(va):
    o=off(va); return struct.unpack('<Q',d[o:o+8])[0] if o is not None else None
def sstr(va):
    if not va: return None
    o=off(va)
    if o is None: return None
    n=d[o]
    if not(1<=n<70): return None
    s=d[o+1:o+1+n].decode('latin1',errors='replace')
    return s if all(32<=ord(c)<127 for c in s) else None
for VMT,label in [(0x140f572c8,'TDirSession'),(0x140f336d0,'TDirSessionState')]:
    print(f'=== {label} VMT={hex(VMT)} header ===')
    for o2 in range(-0xc8,0,8):
        v=u64(VMT+o2)
        name=sstr(v) if v and 0x140e00000<v<0x141c9d000 else None
        print(f'   {o2:+#06x} = {hex(v) if v is not None else "None":>18} {name or ""}')
    print()
