import json,os,sys
BASE=r'D:\Rea'; PSE=os.path.join(BASE,'extracted','pseudocode')
att=json.load(open(os.path.join(BASE,'extracted','function-attribution.json'),encoding='utf-8'))
fns=att['functions']
unit=sys.argv[1]; lo=int(sys.argv[2]); hi=int(sys.argv[3])
ds={k:v for k,v in fns.items() if v.get('unit')==unit and lo<=v['size']<=hi}
for a,v in sorted(ds.items(), key=lambda kv:-kv[1]['size']):
    print('='*84); print(f'### {a} size={v["size"]} conf={v["confidence"]}')
    print(open(os.path.join(PSE,a+'.c'),encoding='utf-8',errors='replace').read().split('\n\n',2)[-1])
