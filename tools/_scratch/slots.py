import pefile,struct,json,sys,re,os,collections
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def off(va):
    rva=va-base
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def vcall_slots(va,size):
    o=off(va); b=data[o:o+size]; out=set()
    for i in range(len(b)-6):
        if b[i]==0xff and (b[i+1]&0x38)==0x10 and (b[i+1]&0xc0)==0x80:
            out.add(struct.unpack('<i',b[i+2:i+6])[0])
    for i in range(len(b)-2):
        if b[i]==0xff and (b[i+1]&0xc0)==0x40:
            out.add(b[i+2])
    return {x for x in out if 0<x<0x600}
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
PSE=r'D:\Rea\extracted\pseudocode'
VC={0x28:'AfterConstruction?',0x30:'SafeCall?',0x38:'??',0x40:'??',0x48:'??',0x50:'NewInstance?',0x58:'FreeInstance?',0x60:'Destroy?'}
# collect all slots used by DirSession.pas code AND by DirTree.pas code that references DirSession
slots=collections.Counter()
for k,v in att.items():
    if v['unit']!='DirSession.pas': continue
    t=open(f'{PSE}\{k}.c',encoding='utf-8',errors='replace').read()
    for m in re.finditer(r'\*param_1 \+ (0x[0-9a-f]+)',t): slots[int(m.group(1),16)]+=1
    for s in vcall_slots(int(k,16),v['size']): slots[s]+=1
print('all virtual slots referenced by DirSession.pas functions:')
for s in sorted(slots): print(f'   {s:#06x}  x{slots[s]}')
