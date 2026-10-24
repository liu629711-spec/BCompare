p = r'D:\Rea\tools\uia-menu-check.py'
lines = open(p, encoding='utf-8').read().splitlines(True)

# locate children_rows block
start = next(i for i, l in enumerate(lines) if l.startswith('def children_rows('))
end = next(i for i, l in enumerate(lines) if i > start and l.startswith('def main('))
new_block = '''def children_rows(pid):
    """Rows of the open submenu. WPF renders an open menu as a SEPARATE popup
    window (class 'SendMessageMenu'), not as children of the top item - the same
    shape the BC probe captured via TTBPopupWindow. Scan the process windows."""
    out = []

    def scan(el, depth=0):
        if depth > 6:
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
                scan(c, depth + 1)
            else:
                scan(c, depth)

    for w in top_windows(pid):
        cls = get_class(w)
        if not (cls.startswith("HwndWrapper") or "Menu" in cls or "Popup" in cls):
            continue
        try:
            pel = Desktop(backend="uia").window(handle=w).wrapper_object()
            scan(pel)
        except Exception:
            continue
    seen = set()
    uniq = []
    for row in out:
        if row in seen:
            continue
        seen.add(row)
        uniq.append(row)
    return uniq


'''
lines[start:end] = [new_block]
s = ''.join(lines)

# update the caller
old2 = '''                top_el.click_input()
                time.sleep(0.8)
                tops_open = current_tops()
                if m in tops_open:
                    got = [(x[0], x[1]) for x in children_rows(tops_open[m][0])]
                else:
                    got = [(x[0], x[1]) for x in children_rows(top_el)]'''
new2 = '''                top_el.click_input()
                time.sleep(0.9)
                got = [(x[0], x[1]) for x in children_rows(proc.pid)]'''
assert old2 in s, 'caller anchor missing'
s = s.replace(old2, new2)

if 'from pywinauto import Desktop' not in s.split('def main')[0]:
    s = s.replace('u32 = ctypes.windll.user32',
                  'u32 = ctypes.windll.user32\nfrom pywinauto import Desktop', 1)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('children_rows rewritten by line range')
