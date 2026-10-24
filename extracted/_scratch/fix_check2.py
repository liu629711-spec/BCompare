p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()

old = '''def children_rows(top):
    """Rows of the submenu under a top item, after it has been opened (clicked)."""
    out = []
    for c in top.children():
        if c.element_info.control_type != "MenuItem":
            continue
        try:
            acc = c.element_info.element.GetCurrentPropertyValue(UIA_AccessKeyPropertyId) or ""
        except Exception:
            acc = ""
        name = c.element_info.name or ""
        parts = name.split("\\t")
        out.append((parts[0].replace("&", "").replace("_", ""),
                    parts[1] if len(parts) > 1 else "",
                    (acc[4:] if acc.lower().startswith("alt+") else acc)))
    return out'''
new = '''def children_rows(pid):
    """Rows of the open submenu. WPF renders an open menu as a SEPARATE popup
    window (class 'SendMessageMenu'), not as children of the top item — the same
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
                parts = name.split("\\t")
                out.append((parts[0].replace("&", "").replace("_", ""),
                            parts[1] if len(parts) > 1 else "",
                            (acc[4:] if acc.lower().startswith("alt+") else acc)))
                scan(c, depth + 1)
            else:
                scan(c, depth)

    # popup windows owned by our process
    for w in top_windows(pid):
        cls = get_class(w)
        if not (cls.startswith("HwndWrapper") or "Menu" in cls or "Popup" in cls):
            continue
        try:
            pel = Desktop(backend="uia").window(handle=w).wrapper_object()
            scan(pel)
        except Exception:
            continue
    # dedupe (same popup may surface under multiple window classes)
    seen = set()
    uniq = []
    for row in out:
        if row in seen:
            continue
        seen.add(row)
        uniq.append(row)
    return uniq'''
assert old in s, 'anchor missing'
s = s.replace(old, new)

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
assert old2 in s, 'second anchor missing'
s = s.replace(old2, new2)

old3 = '''                tops_now = current_tops()
                if m in tops_now:
                    tops_now[m][0].click_input()
                time.sleep(0.4)'''
new3 = '''                tops_now = current_tops()
                if m in tops_now:
                    tops_now[m][0].click_input()
                else:
                    top_el.click_input()
                time.sleep(0.4)'''
assert old3 in s
s = s.replace(old3, new3)

if 'from pywinauto import Desktop' not in s.split('def main')[0]:
    s = s.replace('u32 = ctypes.windll.user32',
                  'u32 = ctypes.windll.user32\nfrom pywinauto import Desktop')
open(p, 'w', encoding='utf-8').write(s)
print('children_rows reads the popup window')
