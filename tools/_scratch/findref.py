import pefile,struct,json,sys
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
ents=sorted((int(k,16),v) for k,v in att.items()); keys=[e[0] for e in ents]
import bisect
def owner(va):
    i=bisect.bisect_right(keys,va)-1
    if i<0: return None
    a,v=ents[i]
    return (f'{a:09x}',v) if va<a+v['size'] else None
targets=[int(x,16) for x in sys.argv[1:]]
for t in targets:
    pat=struct.pack('<Q',t)
    print(f'=== qword {hex(t)} occurrences ===')
    n=0
    for s in pe.sections:
        o=s.PointerToRawData; n2=s.SizeOfRawData
        if o==0 or n2==0: continue
        blk=data[o:o+n2]; idx=0
        while n<20:
            i=blk.find(pat,idx)
            if i<0: break
            va=base+s.VirtualAddress+i
            own=owner(va)
            print(f'   {hex(va)} [{s.Name.decode().strip(chr(0))}] '+ (f'in {own[0]} [{own[1]["unit"]}] size={own[1]["size"]}' if own else '(data/no-owner)'))
            idx=i+1; n+=1
