"""Shared live UIA readers (extracted verbatim from tools/uia-menu-check.py so
the self-golden gate and the Oracle gate walk the tree with identical rules).
UIA_AccessKeyPropertyId is a fixed protocol constant (30007), not per-app data."""
import ctypes
from ctypes import wintypes

u32 = ctypes.windll.user32
UIA_AccessKeyPropertyId = 30007


def read_live_chrome(win):
    """Product chrome rows: PanelHost wrappers carry AutomationId 'chrome:SEC:i';
    children are ChromeElements whose peer reports the exact (ct, cls, name)
    triple the Oracle captured. Returns {'tb': [[..],..], 'sb': [[..],..]} in
    index order (tree order can differ from DOM order under DockPanel)."""
    found = {}

    def walk(el, d=0):
        if d > 12:
            return
        aid = el.element_info.automation_id or ""
        if aid.startswith("chrome:"):
            parts = aid.split(":")
            found.setdefault(parts[1], {})[int(parts[2])] = [
                (c.element_info.control_type, c.element_info.class_name,
                 c.element_info.name or "")
                for c in el.children()]
        for c in el.children():
            walk(c, d + 1)
    walk(win)
    return {sec: [v[k] for k in sorted(v)] for sec, v in found.items()}

def live_skeleton_preorder(win):
    """Preorder (ct, cls, name) of the product's content-view UIA control tree.
    Skip rules mirror the skeleton prune: the window root is not emitted (WPF
    reports HwndWrapper for TViewForm); menu bars are skipped entirely (menu
    axis = gate 6.6); titlebar/system-menu skipped (OS chrome); a chrome row
    host emits its OWN triple but does not descend — its item children live in
    the chrome ledger, not the skeleton."""
    out = []

    def walk(el, d=0):
        if d > 20:
            return
        ct = el.element_info.control_type or ""
        if ct in ("MenuBar", "Menu") or ct == "TitleBar":
            return
        cls = el.element_info.class_name or ""
        if cls == "TextPane":
            # D3 accessibility subtree (docs/20 §5): row peers ARE control
            # elements (measured 2026-10-22: the WPF UIA bridge does not
            # expose false-control peers to tree navigation at all), but
            # they are not part of the measured BC layout skeleton — carve
            # the subtree out of the structural walk. The D3 gate
            # (uia-d3-check.py) walks and asserts it explicitly.
            return
        out.append((ct, cls, el.element_info.name or ""))
        if (el.element_info.automation_id or "").startswith("chrome:"):
            return
        for c in el.children():
            walk(c, d + 1)
    for c in win.children():
        walk(c)
    return out

def live_menu_rows(win):
    """Find the app menu (NOT the OS titlebar system menu — same trap as the BC
    probe: it also reports MenuBar) and return {topLabel: (element, label, accKey)}."""
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
        return None
    # WPF's Menu reports 'Menu'; the OS system menu reports 'MenuBar' with 1 item.
    menubar = max(bars, key=lambda b: len(b.children()))
    rows = {}
    for top in menubar.children():
        if top.element_info.control_type != "MenuItem":
            continue
        raw = top.element_info.element
        acc = raw.GetCurrentPropertyValue(UIA_AccessKeyPropertyId) or ""
        label = (top.element_info.name or "").replace("&", "").replace("_", "")
        rows[label] = (top, label, acc)
    return rows
