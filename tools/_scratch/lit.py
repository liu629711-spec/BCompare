import pefile,struct,sys
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def off(va):
    rva=va-base
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def u16(va):
    b=data[off(va):off(va)+2]; return struct.unpack('<H',b)[0]
def u32(va):
    b=data[off(va):off(va)+4]; return struct.unpack('<I',b)[0]
def u64(va):
    b=data[off(va):off(va)+8]; return struct.unpack('<Q',b)[0]
def disp_str(va):
    """Delphi inline UTF-16 string literal: optional len? try raw utf16 until 0x0000"""
    o=off(va); blk=data[o:o+400]
    n=0
    while n<200:
        ch=struct.unpack('<H',blk[n*2:n*2+2])[0]
        if ch==0: break
        n+=1
    if n==0: return None
    return blk[:n*2].decode('utf-16-le',errors='replace')
for a in sys.argv[1:]:
    va=int(a,16)
    print(f'{a}: raw={data[off(va):off(va)+16].hex()}  disp16={disp_str(va)!r}  u32={u32(va)} u64={u64(va)}')
