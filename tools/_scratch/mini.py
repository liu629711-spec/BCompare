import pefile,struct,sys,json
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
d=pe.__data__
def off(va):
    rva=va-pe.OPTIONAL_HEADER.ImageBase
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
R64={0:'rax',1:'rcx',2:'rdx',3:'rbx',4:'rsp',5:'rbp',6:'rsi',7:'rdi'}
R64E={0:'r8',1:'r9',2:'r10',3:'r11',4:'r12',5:'r13',6:'r14',7:'r15'}
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
def decode(va,n):
    o=off(va); b=d[o:o+n]; i=0; out=[]
    while i<len(b)-2:
        p=va+i
        c=b[i]
        if c==0xE8:
            t=p+5+struct.unpack('<i',b[i+1:i+5])[0]
            out.append((p,f'call {hex(t)}')); i+=5; continue
        if c==0x48 and b[i+1]==0x89:
            m=b[i+2]
            if (m&0xc0)==0xc0:
                out.append((p,f'mov {R64[(m>>3)&7]},{R64[m&7]}')); i+=3; continue
        if c==0x48 and b[i+1]==0x8b and (b[i+2]&0xc0)==0xc0:
            m=b[i+2]; out.append((p,f'mov {R64[(m>>3)&7]},{R64[m&7]}')); i+=3; continue
        if c==0x48 and b[i+1]==0x83 and b[i+2] in (0xec,0xc4):
            out.append((p,f'sub rsp,{b[i+3]}')); i+=4; continue
        if c==0x48 and b[i+1]==0x8d and (b[i+2]&0xc7)==0x05:
            dd=struct.unpack('<i',b[i+3:i+7])[0]
            out.append((p,f'lea {R64[(b[i+2]>>3)&7]},[rip+{dd:#x}] -> {hex(p+7+dd)}')); i+=7; continue
        if c==0x48 and b[i+1]==0x8d and (b[i+2]&0xc7)==0x45:
            dd=struct.unpack('<i',b[i+3:i+7])[0]
            out.append((p,f'lea {R64[(b[i+2]>>3)&7]},[rbp+{dd:#x}]')); i+=7; continue
        if c==0x48 and b[i+1]==0x8b and (b[i+2]&0xc7)==0x05:
            dd=struct.unpack('<i',b[i+3:i+7])[0]
            out.append((p,f'mov {R64[(b[i+2]>>3)&7]},[rip+{dd:#x}] -> {hex(p+7+dd)}')); i+=7; continue
        i+=1
    return out
for a in sys.argv[1:]:
    va=int(a,16); e=att.get(f'{va:09x}')
    print(f'=== {a} size={e["size"] if e else "?"} ===')
    for p,s in decode(va, e['size'] if e else 200):
        print(f'   {hex(p)} {s}')
