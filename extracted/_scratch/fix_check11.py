p = r'D:\Rea\tools\uia-menu-check.py'
s = open(p, encoding='utf-8').read()
lines = s.splitlines(True)
start = next(i for i, l in enumerate(lines) if l.startswith('def children_rows('))
end = next(i for i, l in enumerate(lines) if i > start and l.startswith('def main('))
new_block = '''def children_rows(win, label):
    """Rows of the open submenu for `label`.

    Open with Alt+<accesskey> (clicks on UIA refs die once WPF popups open).
    Then read ONLY the descendants of the matching top item inside the app Menu:
    while a submenu is open it hangs off that item; other top-level siblings
    must be ignored.
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
    top = None
    for t in app.children():
        if t.element_info.control_type != "MenuItem":
            continue
        nm = (t.element_info.name or "").replace("&", "").replace("_", "")
        if nm == label:
            top = t
            break
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
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('children_rows scoped to the opened top item')
