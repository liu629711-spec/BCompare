p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()

old = '''                tops_now = current_tops()
                if m not in tops_now:
                    problems.append(f"[{m}] top item vanished after re-read")
                    continue
                top_el = tops_now[m][0]
                top_el.click_input()
                time.sleep(0.9)
                got = [(x[0], x[1]) for x in children_rows(proc.pid)]'''
new = '''                # open the menu with the keyboard: focus the window and send the
                # access key (Alt+<key>). Mouse clicks on detached UIA refs fail
                # with SetCursorPos errors after WPF popups invalidate them.
                key = (live[m][2] or "").split("+")[-1].lower()
                if not key:
                    problems.append(f"[{m}] no access key to open with")
                    continue
                u32.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                u32.keybd_event(0x12, 0, 0, 0)              # Alt down
                u32.keybd_event(ord(key.upper()), 0, 0, 0)
                u32.keybd_event(ord(key.upper()), 0, 2, 0)
                u32.keybd_event(0x12, 0, 2, 0)              # Alt up
                time.sleep(1.0)
                got = [(x[0], x[1]) for x in children_rows(proc.pid)]'''
assert old in s, 'open anchor missing'
s = s.replace(old, new)

old2 = '''                tops_now = current_tops()
                if m in tops_now:
                    tops_now[m][0].click_input()
                else:
                    top_el.click_input()
                time.sleep(0.4)'''
new2 = '''                # close: Esc (keyboard-opened menus close with it)
                u32.keybd_event(0x1B, 0, 0, 0)
                u32.keybd_event(0x1B, 0, 2, 0)
                time.sleep(0.4)'''
assert old2 in s, 'close anchor missing'
s = s.replace(old2, new2)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('keyboard-open path wired')
