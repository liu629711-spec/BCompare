import json,os,re,sys,collections
BASE=r'D:\Rea'; PSE=os.path.join(BASE,'extracted','pseudocode')
idx=json.load(open(os.path.join(BASE,'tools','_scratch','idx.json'),encoding='utf-8'))
ubf=idx['unit_by_file']
pats=sys.argv[1:]
rxs=[(p,re.compile(p)) for p in pats]
files=sorted(f for f in os.listdir(PSE) if f.endswith('.c'))
data={}
for f in files:
    data[f]=open(os.path.join(PSE,f),encoding='utf-8',errors='replace').read()
for p,rx in rxs:
    hits=collections.defaultdict(list)
    for f,txt in data.items():
        if rx.search(txt):
            hits[ubf.get(f[:-2],'?')].append(f[:-2])
    tot=sum(len(v) for v in hits.values())
    print(f'### pattern {p!r} -> {tot} files')
    for u in sorted(hits):
        print(f'   {u}: {len(hits[u])} :: '+' '.join(sorted(hits[u])))
