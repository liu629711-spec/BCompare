p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
lines = s.splitlines(True)
start = next(i for i, l in enumerate(lines) if l.startswith('def children_rows('))
end = next(i for i, l in enumerate(lines) if i > start and l.startswith('def main('))
new_block = '''def menu_state(win):
    """(appMenu, {label: topItemWrapper}) read FRESH from the window each time.
    WPF popups invalidate cached UIA refs, so every interaction re-reads."""
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
        return None, {}
    app = max(bars, key=lambda b: len(b.children()))
    tops = {}
    for t in app.children():
        if t.element_info.control_type == "MenuItem":
            nm = (t.element_info.name or "").replace("&", "").replace("_", "")
            tops[nm] = t
    return app, tops


def children_rows(win, label):
    """Rows of the open submenu: re-read the tree, find the top item, read its
    submenu children (a nested Menu container once open)."""
    app, tops = menu_state(win)
    top = tops.get(label)
    if top is None:
        return []
    out = []

    def rec(el, d=0):
        if d > 8:
            return
        for c in el.children():
            if c.element_info.control_type == "MenuItem":
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
    rec(top)
    return out


'''
lines[start:end] = [new_block]
s = ''.join(lines)

# open: fresh-read top item, then click (the ref is used immediately)
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
new_open = '''                u32.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                _app, tops_now = menu_state(win)
                if m not in tops_now:
                    problems.append(f"[{m}] top item not found for open")
                    continue
                tops_now[m].click_input()
                time.sleep(1.0)
                got = [(x[0], x[1]) for x in children_rows(win, m)]'''
assert old_open in s, 'open anchor missing'
s = s.replace(old_open, new_open)

# close: fresh read + click, else Esc
old_close = '''                u32.keybd_event(0x1B, 0, 0, 0)
                u32.keybd_event(0x1B, 0, 2, 0)
                time.sleep(0.4)'''
new_close = '''                _a2, tops2 = menu_state(win)
                if m in tops2:
                    try:
                        tops2[m].click_input()
                    except Exception:
                        u32.keybd_event(0x1B, 0, 0, 0)
                        u32.keybd_event(0x1B, 0, 2, 0)
                time.sleep(0.4)'''
assert old_close in s, 'close anchor missing'
s = s.replace(old_close, new_close)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('fresh-read click open/close wired')
