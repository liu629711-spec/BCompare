p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
old = '''                u32.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                _app, tops_now = menu_state(win)
                if m not in tops_now:
                    problems.append(f"[{m}] top item not found for open")
                    continue
                tops_now[m].click_input()
                time.sleep(1.0)'''
new = '''                # bring the window truly to the foreground before interacting:
                # a background window yields invalid element rects and the click
                # dies in SetCursorPos (file-not-found) inside pywinauto.
                u32.ShowWindow(hwnd, 9)  # SW_RESTORE
                u32.SetForegroundWindow(hwnd)
                if u32.GetForegroundWindow() != hwnd:
                    # ALT nudge is the documented bypass for the foreground lock
                    u32.keybd_event(0x12, 0, 0, 0)
                    u32.keybd_event(0x12, 0, 2, 0)
                    u32.SetForegroundWindow(hwnd)
                time.sleep(0.6)
                _app, tops_now = menu_state(win)
                if m not in tops_now:
                    problems.append(f"[{m}] top item not found for open")
                    continue
                r = tops_now[m].rectangle()
                cx, cy = int(r.left + r.width() / 2), int(r.top + r.height() / 2)
                if r.width() <= 0 or r.height() <= 0 or cx <= 0 or cy <= 0:
                    problems.append(f"[{m}] invalid rect {r}, skipping")
                    continue
                u32.SetCursorPos(cx, cy)
                time.sleep(0.1)
                u32.mouse_event(0x0002, 0, 0, 0, 0)  # LMB down
                u32.mouse_event(0x0004, 0, 0, 0)  # LMB up
                time.sleep(1.0)'''
assert old in s, 'anchor missing'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('foreground + raw mouse click wired')
