p = r'D:\Rea\tools\uia-menu-check.py'
lines = open(p, encoding='utf-8').read().splitlines(True)

# replace the click-open block (lines with top_el.click_input + sleep(0.9))
start = None
for i, l in enumerate(lines):
    if 'top_el = tops_now[m][0]' in l:
        start = i
        break
assert start is not None
end = start
while end < len(lines) and 'children_rows(proc.pid)]' not in lines[end]:
    end += 1
lines[start:end + 1] = ['''                # open with the keyboard (mouse clicks on UIA refs die after WPF
                # popups invalidate them -> SetCursorPos errors)
                key = (live[m][2] or "").split("+")[-1].lower()
                if not key:
                    problems.append(f"[{m}] no access key to open with")
                    continue
                u32.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                u32.keybd_event(0x12, 0, 0, 0)
                u32.keybd_event(ord(key.upper()), 0, 0, 0)
                u32.keybd_event(ord(key.upper()), 0, 2, 0)
                u32.keybd_event(0x12, 0, 2, 0)
                time.sleep(1.0)
                got = [(x[0], x[1]) for x in children_rows(proc.pid)]
''']
s = ''.join(lines)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('open block replaced by keyboard path')
