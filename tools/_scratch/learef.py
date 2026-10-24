import pefile,struct,json,sys
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
text=[s for s in pe.sections if s.Name.decode().strip('\x00')=='.text'][0]
o=text.PointerToRawData; blk=data[o:o+text.SizeOfRawData]; tva=base+text.VirtualAddress
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
# build sorted fn entry list for containing-function lookup
ents=sorted((int(k,16),v) for k,v in att.items())
import bisect
keys=[e[0] for e in ents]
def owner(va):
    i=bisect.bisect_right(keys,va)-1
    if i<0: return None
    a,v=ents[i]
    if va < a+v['size']: return (f'{a:09x}',v)
    return None
# RIP-relative: lea r64,[rip+disp32] = 48/4C 8D modrm(05/0D/15/1D/25/2D/35/3D) disp32
res={}
for i in range(len(blk)-7):
    b=blk[i]
    if b not in (0x48,0x4c): continue
    if blk[i+1]!=0x8d: continue
    m=blk[i+2]
    if (m&0xc7)!=0x05: continue
    disp=struct.unpack('<i',blk[i+3:i+7])[0]
    tgt=tva+i+7+disp
    res.setdefault(tgt,[]).append(tva+i)
lohi=[(0x140f57180,0x140f57280),(0x140f58220,0x140f58320),(0x140f587f0,0x140f588a0),(0x140f33600,0x140f336c0),(0x140e4da20,0x140e4dac0)]
for lo,hi in lohi:
    print(f'===== LEAs targeting {hex(lo)}..{hex(hi)}')
    for tgt in sorted(res):
        if not (lo<=tgt<hi): continue
        for site in res[tgt]:
            own=owner(site)
            s=f'{own[0]} [{own[1]["unit"]}] size={own[1]["size"]}' if own else '(no owner)'
            print(f'  site {hex(site)} -> {hex(tgt)}   in {s}')
