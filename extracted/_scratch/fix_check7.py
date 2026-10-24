p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
old = '''def children_rows(pid):
    """Rows of the open submenu. WPF renders an open menu as a SEPARATE popup
    window (class 'SendMessageMenu'), not as children of the top item - the same
    shape the BC probe captured via TTBPopupWindow. Scan the process windows."""
    out = []'''
new = '''def children_rows(pid, main_hwnd):
    """Rows of the open submenu. WPF renders an open menu as a SEPARATE popup
    window (class 'SendMessageMenu'), not as children of the top item - the same
    shape the BC probe captured via TTBPopupWindow. Scan the process windows,
    excluding the main window (its own top-level items would pollute the rows)."""
    out = []'''
assert old in s
s = s.replace(old, new)

old2 = '''    for w in top_windows(pid):
        cls = get_class(w)
        if not (cls.startswith("HwndWrapper") or "Menu" in cls or "Popup" in cls):
            continue'''
new2 = '''    for w in top_windows(pid):
        if w == main_hwnd:
            continue
        cls = get_class(w)
        if not (cls.startswith("HwndWrapper") or "Menu" in cls or "Popup" in cls):
            continue'''
assert old2 in s
s = s.replace(old2, new2)

old3 = 'got = [(x[0], x[1]) for x in children_rows(proc.pid)]'
new3 = 'got = [(x[0], x[1]) for x in children_rows(proc.pid, hwnd)]'
assert old3 in s
s = s.replace(old3, new3)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('popup scan excludes main window')
