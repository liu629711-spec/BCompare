import pefile,struct,json,sys,bisect
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
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
ents=sorted((int(k,16),v) for k,v in att.items()); keys=[e[0] for e in ents]
def owner(va):
    i=bisect.bisect_right(keys,va)-1
    if i<0: return None
    a,v=ents[i]
    return (f'{a:09x}',v) if va<a+v['size'] else None
# classref = VMT-0x28. Given classref, VMT = classref+0x28
CLASSREF={'TDirSession':0x140f571d8,'TDirCompareSession':0x140f582a0-0x28,'TDirMergeSession':0x140f58828-0x28}
for k,v in CLASSREF.items(): print(k,hex(v))
def scan(t,limit=12):
    pat=struct.pack('<Q',t); out=[]
    for s in pe.sections:
        o=s.PointerToRawData; n=s.SizeOfRawData
        if o==0 or n==0: continue
        blk=data[o:o+n]; idx=0
        while len(out)<limit:
            i=blk.find(pat,idx)
            if i<0: break
            va=base+s.VirtualAddress+i
            own=owner(va)
            out.append((va,s.Name.decode().strip('\x00'),own))
            idx=i+1
    return out
for label,cref in [('TDirSession',0x140f571b0),('TDirBaseSession',0x140e4da30)]:
    print(f'\n=== qword refs to {label} (classref candidate {hex(cref)}) ===')
    for va,sn,own in scan(cref):
        print(f'   {hex(va)} [{sn}] '+(f'in {own[0]} [{own[1]["unit"]}] size={own[1]["size"]}' if own else '(no owner)'))
