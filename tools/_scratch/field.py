import json,os,re,sys,collections
BASE=r'D:\Rea'; PSE=os.path.join(BASE,'extracted','pseudocode')
idx=json.load(open(os.path.join(BASE,'tools','_scratch','idx.json'),encoding='utf-8'))
ubf=idx['unit_by_file']
pat=sys.argv[1]
rx=re.compile(pat)
hits=collections.defaultdict(list)
n=0
for f in os.listdir(PSE):
    if not f.endswith('.c'): continue
    a=f[:-2]
    txt=open(os.path.join(PSE,f),encoding='utf-8',errors='replace').read()
    n+=1
    if rx.search(txt):
        hits[ubf.get(a,'?')].append(a)
print('scanned',n,'regex',repr(pat))
for u in sorted(hits):
    print(f'{u}: {len(hits[u])} :: '+' '.join(sorted(hits[u])))
