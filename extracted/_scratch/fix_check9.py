p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
lines = s.splitlines(True)
start = next(i for i, l in enumerate(lines) if l.startswith('def children_rows('))
end = next(i for i, l in enumerate(lines) if i > start and l.startswith('def main('))
new_block = '''def children_rows(win, label):
    """Rows of the open submenu for `label`. The popup materializes as children
    of the matching top item INSIDE the app Menu (not the titlebar system menu,
    whose only child is '系统'). Returns (label, gesture, accessKey) tuples."""
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
    top = None
    for t in app.children():
        if t.element_info.control_type == "MenuItem":
            nm = (t.element_info.name or "").replace("&", "").replace("_", "")
            if nm == label:
                top = t
                break
    if top is None:
        return []
    out = []
    for c in top.children():
        if c.element_info.control_type != "MenuItem":
            continue
        try:
            acc = c.element_info.element.GetCurrentPropertyValue(UIA_AccessKeyPropertyId) or ""
        except Exception:
            acc = ""
        name = c.element_info.name or ""
        parts = name.split(chr(9))
        out.append((parts[0].replace("&", "").replace("_", ""),
                    parts[1] if len(parts) > 1 else "",
                    (acc[4:] if acc.lower().startswith("alt+") else acc)))
    return out


'''
lines[start:end] = [new_block]
s = ''.join(lines)
s = s.replace('got = [(x[0], x[1]) for x in children_rows(win, proc.pid)]',
              'got = [(x[0], x[1]) for x in children_rows(win, m)]')
# open via click on the freshly-found top item
old_open = '''                key = (live[m][2] or "").split("+")[-1].lower()
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
new_open = '''                tops_now = current_tops()
                if m not in tops_now:
                    problems.append(f"[{m}] top item vanished after re-read")
                    continue
                u32.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                tops_now[m][0].click_input()
                time.sleep(1.0)
                got = [(x[0], x[1]) for x in children_rows(win, m)]'''
assert old_open in s, 'open block anchor missing'
s = s.replace(old_open, new_open)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('click-open + app-menu children_rows')
