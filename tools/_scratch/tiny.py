import sys,struct
raw=open(r'D:\bc-official\app\BCompare.exe','rb').read()
TEXT_VA=0x140001000; TEXT_RAW=0x400
def off(va): return TEXT_RAW+(va-TEXT_VA)
def u64(va): return struct.unpack('<Q',raw[off(va):off(va)+8])[0]
def sstr(va):
    o=off(va); n=raw[o]
    return raw[o+1:o+1+n].decode('latin1',errors='replace') if 1<=n<70 else None
def disp16(va):
    o=off(va); n=0
    while n<200:
        ch=struct.unpack('<H',raw[o+n*2:o+n*2+2])[0]
        if ch==0: break
        n+=1
    return raw[o:o+n*2].decode('utf-16-le',errors='replace')
for a in sys.argv[1:]:
    va=int(a,16)
    # decode LEA rip-relative inside first 40 bytes
    b=raw[off(va):off(va)+48]
    info=[]
    for i in range(len(b)-7):
        if b[i] in (0x48,0x4c) and b[i+1]==0x8d and (b[i+2]&0xc7)==0x05:
            d=struct.unpack('<i',b[i+3:i+7])[0]
            tgt=va+i+7+d
            info.append((hex(tgt), disp16(tgt)[:60]))
    print(f'{a}: {b[:24].hex()}')
    for t,s in info: print(f'     lea -> {t}  {s!r}')
