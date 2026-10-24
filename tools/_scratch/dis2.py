import json,sys,os
# raw-file disassembler-lite for DirSession functions
f=open(r'D:\bc-official\app\BCompare.exe','rb')
raw=f.read(); f.close()
BASE=0x140000000
TEXT_VA=0x140001000; TEXT_RAW=0x400
def off(va): return TEXT_RAW+(va-TEXT_VA)
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
def slots(va,size):
    o=off(va); b=raw[o:o+size]; out=[]
    i=0
    while i < len(b)-6:
        if b[i]==0x48 and b[i+1]==0x8b and 0xc0<=(b[i+2]&0xc0)==0x80 and b[i+2]<0xc0:
            pass
        # FF /2 with mod=10 reg=2 -> call qword [reg+disp32]
        if b[i]==0xff and (b[i+1]&0x38)==0x10 and (b[i+1]&0xc0)==0x80:
            d=int.from_bytes(b[i+2:i+6],'little',signed=True)
            out.append((va+i,'disp32',d))
        if b[i]==0xff and (b[i+1]&0x38)==0x10 and (b[i+1]&0xc0)==0x40:
            out.append((va+i,'disp8',b[i+2]))
        i+=1
    return out
for a in sys.argv[1:]:
    va=int(a,16); e=att.get(f'{va:09x}')
    if not e: print(a,'not attributed'); continue
    print(f'=== {a} {e["unit"]} size={e["size"]}')
    seen=set()
    for site,kind,d in slots(va,e['size']):
        if kind=='disp32' and 0xd0<=d<=0x280:
            if d not in seen: print(f'    {hex(site)} call [reg+{hex(d)}]'); seen.add(d)
        if kind=='disp8' and d>=0x40: print(f'    {hex(site)} call [reg+{hex(d)}]')
