import pefile,struct,sys
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase
data=pe.__data__
def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def rd(va,n):
    o=rva2off(va-base); return None if o is None else data[o:o+n]
def u64(va):
    b=rd(va,8); return struct.unpack('<Q',b)[0] if b else None
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if b else None
def delphi_str(ptr):
    ln=u32(ptr-4); rc=u32(ptr-8)
    if ln is None or not (0<ln<300): return None
    b=rd(ptr,ln*2)
    if b is None: return None
    try: return b.decode('utf-16-le')
    except: return None
def shortstr(va):
    b=rd(va,255)
    if not b: return None
    n=b[0]
    return b[1:1+n].decode('latin1',errors='replace') if n<255 else None
# find vtables: scan .data and .rdata for pointers in DirSession range
lo,hi=0x140f58000,0x140f5c000
found={}
for s in pe.sections:
    if s.Name.decode().strip('\x00') not in ('.data','.rdata'): continue
    o=s.PointerToRawData; n=min(s.SizeOfRawData,len(data)-o)
    blk=data[o:o+n]
    for i in range(0,n-8,8):
        v=struct.unpack('<Q',blk[i:i+8])[0]
        if lo<=v<hi:
            va=base+s.VirtualAddress+i
            # count run
            found.setdefault(va,[]).append(v)
# neighbor detection: vtables are contiguous runs of code ptrs
runs=[]
cands=sorted(found)
for va in cands:
    pass
# simpler: for each candidate addr, check the 8 preceding slots are also code ptrs from 0x140001000..0x141c9b844
def is_code(v):
    return v is not None and 0x140001000<=v<0x141c9b844
res=[]
for va in cands:
    k=0
    while k<40 and is_code(u64(va-8*(k+1))): k+=1
    if k>=4: res.append((va,k))
res=sorted(set(res))
# merge adjacent
merged=[]
for va,k in res:
    if merged and va-merged[-1][0]<0x100: continue
    merged.append((va,k))
for va,k in merged[:20]:
    print(f'vtable-ish @ {hex(va)} ({k} preceding code ptrs)')
    for pre in (0x30,0x28,0x20,0x18,0x10):
        ss=shortstr(va-pre)
        if ss and ss.isprintable() and 3<len(ss)<80:
            print(f'    -{hex(pre)}: {ss!r}')
