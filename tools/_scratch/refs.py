import pefile,struct,json,sys
pe=pefile.PE(r'D:\bc-official\app\BCompare.exe',fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize:
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
att=json.load(open(r'D:\Rea\extracted\function-attribution.json',encoding='utf-8'))['functions']
targets=[int(x,16) for x in sys.argv[1:]]
text=[s for s in pe.sections if s.Name.decode().strip('\x00')=='.text'][0]
o=text.PointerToRawData; blk=data[o:o+text.SizeOfRawData]
for t in targets:
    print(f'=== candidate {hex(t)} ===')
    pats=[('mov rcx,imm64',b'\x48\xb9'+struct.pack('<Q',t)),
          ('lea rcx,[rip]',None),
          ('mov ecx,imm32',b'\xb9'+struct.pack('<I',t&0xffffffff))]
    for form,pat in pats:
        if pat is None: continue
        idx=0; n=0
        while n<12:
            i=blk.find(pat,idx)
            if i<0: break
            va=base+text.VirtualAddress+i
            a=f'{va:09x}'; e=att.get(a)
            print(f'  {hex(va)} {form:16s} {a} {("["+e["unit"]+"] size="+str(e["size"])) if e else "(not fn entry)"}')
            idx=i+1; n+=1
