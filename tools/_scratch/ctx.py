import json,os,sys,re
BASE=r'D:\Rea'; PSE=os.path.join(BASE,'extracted','pseudocode')
idx=json.load(open(os.path.join(BASE,'tools','_scratch','idx.json'),encoding='utf-8'))
inc=idx['incoming']; ubf=idx['unit_by_file']
target=sys.argv[1]
ctxn=int(sys.argv[2]) if len(sys.argv)>2 else 6
callers=inc.get(target,[])
print(f'== callers of FUN_{target}: {len(callers)} ==')
for c in callers:
    p=os.path.join(PSE,c+'.c')
    if not os.path.exists(p): continue
    lines=open(p,encoding='utf-8',errors='replace').read().split('\n')
    print(f'--- {c} [{ubf.get(c,"?")}] ---')
    for i,l in enumerate(lines):
        if 'FUN_'+target in l:
            lo=max(0,i-ctxn); hi=min(len(lines),i+ctxn+1)
            print('\n'.join(lines[lo:hi]))
            print('  ......')
            break
