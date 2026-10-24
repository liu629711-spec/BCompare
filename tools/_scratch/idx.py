import json,os,re,collections
BASE=r'D:\Rea'
PSE=os.path.join(BASE,'extracted','pseudocode')
att=json.load(open(os.path.join(BASE,'extracted','function-attribution.json'),encoding='utf-8'))
fns=att['functions']
reff=re.compile(r'FUN_([0-9a-f]{7,9})')
unit_by_file={}; incoming=collections.defaultdict(set)
for f in os.listdir(PSE):
    if not f.endswith('.c'): continue
    a=f[:-2]
    txt=open(os.path.join(PSE,f),encoding='utf-8',errors='replace').read()
    m=re.search(r'^note:\s*(.*)$',txt,re.M)
    unit_by_file[a]=(m.group(1).strip() if m else '?')
    for c in set(reff.findall(txt)):
        incoming[c].add(a)
json.dump({'incoming':{k:sorted(v) for k,v in incoming.items()},
           'unit_by_file':unit_by_file},open(os.path.join(BASE,'tools','_scratch','idx.json'),'w'))
print('ok',len(incoming),len(unit_by_file))
