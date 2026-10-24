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
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if b else None
def u16(va):
    b=rd(va,2); return struct.unpack('<H',b)[0] if b else None
def dstr_at(va):
    """Delphi UnicodeString const at va: [-0xc]=codepage u16? Actually: [-0x8]=len? try len at -4 (u32) then -8"""
    for back in (-0xc,-0x8,-0x4):
        ln=u32(va+back)
        if ln and 0<ln<200:
            b=rd(va,ln*2)
            try:
                s=b.decode('utf-16-le')
                if s.isprintable(): return f'[-{abs(back):#x} len={ln}] {s!r}'
            except: pass
    return None
names=sys.argv[1:]
for nm in names:
    va=int(nm,16)
    v=u64(va); u=u32(va); w=u16(va)
    print(f'--- {nm}: u64={hex(v) if v else None}  u32={hex(u) if u else None}  u16={hex(w)}')
    if v and 0x140000000<=v<0x144000000:
        # try: array of char* -> strings
        print('    as char* array:')
        for i in range(6):
            p=u64(v+8*i)
            if not p: break
            ss=rd(p,120)
            if ss:
                n=ss[0]
                s=ss[1:1+n].decode('latin1',errors='replace') if 1<=n<100 else None
                print(f'      [{i}] {hex(p)} {s!r}' if s else f'      [{i}] {hex(p)} (nonstr)')
        print('    as byte table:', rd(v,16).hex() if rd(v,16) else None)
        print('    as qword table:', [hex(u64(v+8*i)) for i in range(6)] if u64(v) else None)
