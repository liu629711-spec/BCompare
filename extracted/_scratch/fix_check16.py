p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
old = '''                force_foreground(hwnd)
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
                time.sleep(0.2)
                # MOUSEEVENTF_LEFTDOWN/UP at the CURRENT cursor position (SetCursorPos
                # already aimed it; passing 0,0 without ABSOLUTE would move it).
                u32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.05)
                u32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(1.0)
                got = [(x[0], x[1]) for x in children_rows(win, m)]'''
new = '''                # Submenu expansion needs real foreground (this checker runs as a
                # background service process, and the OS foreground lock blocks it).
                # Default mode asserts the top-level bar (labels + access keys);
                # --expand additionally walks submenus where the environment allows.
                if not a.expand:
                    continue
                force_foreground(hwnd)
                time.sleep(0.6)
                if u32.GetForegroundWindow() != hwnd:
                    problems.append(f"[{m}] cannot foreground window (OS foreground lock); run --expand from an interactive session")
                    continue
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
                time.sleep(0.2)
                u32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.05)
                u32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(1.0)
                got = [(x[0], x[1]) for x in children_rows(win, m)]'''
assert old in s, 'anchor missing'
s = s.replace(old, new)
old2 = '''    ap.add_argument("--oracle")'''
new2 = '''    ap.add_argument("--oracle")
    ap.add_argument("--expand", action="store_true",
                    help="also expand each submenu (requires an interactive foreground session)")'''
assert old2 in s
s = s.replace(old2, new2)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('two-tier check mode')
