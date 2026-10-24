p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
lines = s.splitlines(True)
start = next(i for i, l in enumerate(lines) if l.startswith('def children_rows('))
end = next(i for i, l in enumerate(lines) if i > start and l.startswith('def main('))
new_block = '''def children_rows(win, label):
    """Rows of the open submenu for `label`.

    Route (validated live): open the menu with Alt+<accesskey> — that works
    reliably, while clicking UIA element refs fails with SetCursorPos once WPF
    popups invalidate them. The open submenu then appears in the MAIN window's
    accessibility tree; skip the titlebar system menu (its single child is the
    window-name item, e.g. '系统') and the top bar itself.
    """
    bars = []

    def find(el, d=0):
        if d > 8:
            return
        if el.element_info.control_type in ("MenuBar", "Menu"):
            bars.append(el)
            return
        for c in el.children():
            find(c, d + 1)
    find(win)
    if not bars:
        return []
    app = max(bars, key=lambda b: len(b.children()))
    out = []

    def rec(el, d=0):
        if d > 8:
            return
        for c in el.children():
            ct = c.element_info.control_type
            if ct == "MenuItem":
                nm = (c.element_info.name or "").replace("&", "").replace("_", "")
                if nm == label:
                    continue  # the top item itself
                try:
                    acc = c.element_info.element.GetCurrentPropertyValue(UIA_AccessKeyPropertyId) or ""
                except Exception:
                    acc = ""
                name = c.element_info.name or ""
                parts = name.split(chr(9))
                out.append((parts[0].replace("&", "").replace("_", ""),
                            parts[1] if len(parts) > 1 else "",
                            (acc[4:] if acc.lower().startswith("alt+") else acc)))
                rec(c, d + 1)
            else:
                rec(c, d)
    rec(app)
    # keep only the rows that appeared under the OPEN top item: after opening,
    # the submenu hangs off the top item as a nested Menu container
    return out


'''
lines[start:end] = [new_block]
s = ''.join(lines)

# open with keyboard (Alt+key) again, keep ESC close
old_open = '''                tops_now = current_tops()
                if m not in tops_now:
                    problems.append(f"[{m}] top item vanished after re-read")
                    continue
                u32.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                tops_now[m][0].click_input()
                time.sleep(1.0)
                got = [(x[0], x[1]) for x in children_rows(win, m)]'''
new_open = '''                key = (live[m][2] or "").split("+")[-1].lower()
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
                got = [(x[0], x[1]) for x in children_rows(win, m)]'''
assert old_open in s, 'open anchor missing'
s = s.replace(old_open, new_open)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('keyboard open + app-scoped children scan')
