import os,sys
PSE=r'D:\Rea\extracted\pseudocode'
for a in sys.argv[1:]:
    p=os.path.join(PSE,a+'.c')
    print('#'*70); print(f'# {a}')
    if not os.path.exists(p): print('  MISSING'); continue
    print(open(p,encoding='utf-8',errors='replace').read().split('\n\n',2)[-1].strip())
