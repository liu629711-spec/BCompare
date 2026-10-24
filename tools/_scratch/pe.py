import pefile,sys,struct
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase
def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def read(va,n):
    off=rva2off(va-base)
    if off is None: return None
    return pe.__data__[off:off+n]
def u64(va): 
    b=read(va,8); return struct.unpack('<Q',b)[0] if b else None
def u32(va):
    b=read(va,4); return struct.unpack('<I',b)[0] if b else None
def u16(va):
    b=read(va,2); return struct.unpack('<H',b)[0] if b else None
def ptr_str(va):
    """Delphi string ptr: ptr -> len(u32) + refcount(u16) + chars(utf16)"""
    p=u64(va)
    if not p: return None
    ln=u32(p-0xc); rc=u16(p-8)
    if ln is None or ln>400: return ('?len',ln)
    b=read(p,ln*2)
    if b is None: return ('?nodata',)
    return b.decode('utf-16-le',errors='replace')
if __name__=='__main__':
    for a in sys.argv[1:]:
        va=int(a,16)
        print(f'{a}: u64={u64(va)} u32={u32(va)} u16={u16(va)} str={ptr_str(va)}')

def arr(va,n):
    return [u64(va+8*i) for i in range(n)]
