p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
lines = s.splitlines(True)
start = next(i for i, l in enumerate(lines) if l.startswith('def children_rows('))
end = next(i for i, l in enumerate(lines) if i > start and l.startswith('def main('))
new_block = '''def children_rows(win, pid):
    """Rows of the currently open submenu. The popup materializes inside the
    MAIN window's accessibility tree (WPF popups are not separate visible
    top-level windows), so walk the main window and keep MenuItems that are NOT
    the top-level bar's own items."""
    all_items = []

    def rec(el, d=0):
        if d > 10:
            return
        for c in el.children():
            if c.element_info.control_type == "MenuItem":
                try:
                    acc = c.element_info.element.GetCurrentPropertyValue(UIA_AccessKeyPropertyId) or ""
                except Exception:
                    acc = ""
                name = c.element_info.name or ""
                parts = name.split(chr(9))
                all_items.append((parts[0].replace("&", "").replace("_", ""),
                                  parts[1] if len(parts) > 1 else "",
                                  (acc[4:] if acc.lower().startswith("alt+") else acc),
                                  d))
            rec(c, d + 1)
    rec(win)

    # top bar items sit at the shallowest depth; submenu items are deeper and
    # appear only while a menu is open
    if not all_items:
        return []
    top_depth = min(d for *_x, d in all_items)
    subs = [r for r in all_items if r[3] > top_depth]
    return [(r[0], r[1], r[2]) for r in subs]


'''
lines[start:end] = [new_block]
s = ''.join(lines)
s = s.replace('got = [(x[0], x[1]) for x in children_rows(proc.pid, hwnd)]',
              'got = [(x[0], x[1]) for x in children_rows(win, proc.pid)]')
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('children_rows walks the main window tree')
