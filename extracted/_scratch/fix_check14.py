p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
old = '''                u32.SetCursorPos(cx, cy)
                time.sleep(0.1)
                u32.mouse_event(0x0002, 0, 0, 0, 0)  # LMB down
                u32.mouse_event(0x0004, 0, 0, 0)  # LMB up
                time.sleep(1.0)'''
new = '''                u32.SetCursorPos(cx, cy)
                time.sleep(0.2)
                # MOUSEEVENTF_LEFTDOWN/UP at the CURRENT cursor position (SetCursorPos
                # already aimed it; passing 0,0 without ABSOLUTE would move it).
                u32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.05)
                u32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(1.0)'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('mouse click at cursor position')
