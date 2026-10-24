import pefile,struct,sys,re
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def off(va):
    rva=va-base
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def vcall_slots(va,size):
    """find FF /2 call qword [reg+disp32] and FF /4 jmp"""
    o=off(va); b=data[o:o+size]
    out=[]
    for i in range(len(b)-6):
        if b[i]==0xff and (b[i+1]&0x38)==0x10 and (b[i+1]&0xc7) in (0x80,0x40):
            modrm=b[i+1]; reg=modrm&7
            # mod=10 (disp32): 0x80|reg .. 0x87
            if (modrm&0xc0)!=0x80: continue
            disp=struct.unpack('<i',b[i+2:i+6])[0]
            out.append((va+i,reg,disp))
    return out
def vcall_8disp(va,size):
    """FF 50 disp8 = call [rax+disp8]"""
    o=off(va); b=data[o:o+size]; out=[]
    for i in range(len(b)-2):
        if b[i]==0xff and (b[i+1]&0xc0)==0x40:
            out.append((va+i,b[i+1]&7,b[i+2]))
    return out
if __name__=='__main__':
    for a in sys.argv[1:]:
        va=int(a,16); import json
        att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
        e=att.get(f'{va:09x}')
        size=e['size'] if e else 0x400
        print(f'=== {a} size={size} ===')
        sl=sorted(set(d for _,_,d in vcall_slots(va,size) if 0<d<0x400))
        print('   disp32 slots:',[hex(x) for x in sl])
