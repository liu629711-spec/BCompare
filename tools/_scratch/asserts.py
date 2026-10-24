import json,os,re,sys
BASE=r'D:\Rea'; PSE=os.path.join(BASE,'extracted','pseudocode')
idx=json.load(open(os.path.join(BASE,'tools','_scratch','idx.json'),encoding='utf-8'))
ubf=idx['unit_by_file']
pat=sys.argv[1] if len(sys.argv)>1 else 'DirSession'
tail=re.compile(r'",\s*(0x[0-9a-fA-F]+)\s*\)')
rows=[]
for f in os.listdir(PSE):
    if not f.endswith('.c'): continue
    t=open(os.path.join(PSE,f),encoding='utf-8',errors='replace').read()
    if (pat+'') not in t: continue
    for m in re.finditer(r'Source[^"]*'+re.escape(pat)+r'[^"]*', t):
        seg=t[m.end():m.end()+40]
        mm=tail.search(seg)
        if mm:
            line=int(mm.group(1),16)
            rows.append((f[:-2], line, ubf.get(f[:-2],'?')))
seen=set(); out=[]
for a,l,u in rows:
    if (a,l) in seen: continue
    seen.add((a,l)); out.append((a,l,u))
out.sort(key=lambda r:r[1])
print(f'=== assertions referencing *{pat}* : {len(out)} sites / {len(set(r[0] for r in out))} funcs ===')
for a,l,u in out: print(f'{a} [{u}] line {l} = 0x{l:x}')
