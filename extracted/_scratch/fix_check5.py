p = r'D:\Rea\tools\uia-menu-check.py'
lines = open(p, encoding='utf-8').read().splitlines(True)

# find the close block (after the expand try) — lines 211..214 region
idx = None
for i, l in enumerate(lines):
    if 'tops_now = current_tops()' in l and i > 200:
        idx = i
        break
assert idx is not None, 'close block not found'
# replace through the following time.sleep(0.4)
end = idx
while end < len(lines) and 'time.sleep(0.4)' not in lines[end]:
    end += 1
lines[idx:end + 1] = ['''                u32.keybd_event(0x1B, 0, 0, 0)
                u32.keybd_event(0x1B, 0, 2, 0)
                time.sleep(0.4)
''']
s = ''.join(lines)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('close block replaced with Esc')
