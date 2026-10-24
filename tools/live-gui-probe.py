#!/usr/bin/env python3
"""Aggregate live GUI probe: menus + toolbar + statusbar in ONE launch.

Why keyboard/native routes failed (measured 2026-10-20):
 - GetMenu is empty on every window: the menu bar is VCL-drawn (TUiMainMenu).
 - UIA ExpandCollapseState = LeafNode on menu items: Expand() is a no-op.
 - keybd_event Alt/F10 never reaches the app reliably under focus rules.
Working route (proven on Session): click the top MenuBarItem (click_input),
then walk the popup `Menu` element's children via UIA RawViewWalker; nested
submenus materialize on mouse HOVER (SetCursorPos, never a click).

Safety: this script only clicks menubar TOP items (open/close toggle) and
hovers; it never invokes a menu command item. Job Object guarantees cleanup.
Restore cursor + WM_CANCELMODE on exit. Strictly serial with harness runs.

Usage: python tools/live-gui-probe.py <BCompare.exe> <outdir>
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import launch, create_kill_job, top_windows, get_class, get_window_text, shutdown  # noqa: E402

k32 = ctypes.windll.kernel32
u32 = ctypes.windll.user32
k32.AssignProcessToJobObject.restype = wintypes.BOOL
k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.ResumeThread.argtypes = [wintypes.HANDLE]

from pywinauto import Desktop  # noqa: E402
from pywinauto.uia_defines import IUIA  # noqa: E402
from comtypes.gen.UIAutomationClient import (  # noqa: E402
    UIA_AccessKeyPropertyId, UIA_IsEnabledPropertyId, UIA_TogglePatternId,
    IUIAutomationTogglePattern,
)

WM_CANCELMODE = 0x001E


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def hover(el):
    r = el.rectangle()
    pt = POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    u32.SetCursorPos(r.left + r.width() // 2, r.top + r.height() // 2)
    time.sleep(0.9)
    return (pt.x, pt.y)


def walk_menu(menu_el, walker, iuia, depth=0, out=None):
    if out is None:
        out = []
    items = []
    child = walker.GetFirstChildElement(menu_el.element_info.element)
    while child:
        try:
            rec = {
                "name": child.CurrentName,
                "ct": child.CurrentControlType,
                "enabled": bool(child.GetCurrentPropertyValue(UIA_IsEnabledPropertyId)),
                "acc": child.GetCurrentPropertyValue(UIA_AccessKeyPropertyId) or "",
            }
            tog = child.GetCurrentPattern(UIA_TogglePatternId)
            if tog:
                rec["toggle"] = int(tog.QueryInterface(IUIAutomationTogglePattern).CurrentToggleState)
            items.append((child, rec))
        except Exception as e:
            items.append((None, {"error": str(e)[:80]}))
        child = walker.GetNextSiblingElement(child)
    for raw, rec in items:
        out.append(rec)
        if raw is None:
            continue
        # nested submenu? materialize by hovering the item (UIA wrapper for children lookup)
        ct_name = IUIA().known_control_types.get(rec["ct"], str(rec["ct"]))
        if ct_name == "MenuItem" and rec.get("name"):
            try:
                wrap = menu_el.parent_descendants  # not used; build wrapper from raw via children scan
            except Exception:
                wrap = None
            # find matching pywinauto element among menu_el.children()
            target = None
            for c in menu_el.children():
                if c.element_info.name == rec["name"] and c.element_info.control_type == "MenuItem":
                    target = c
                    break
            if target is not None:
                hover(target)
                subs = [c for c in target.children() if c.element_info.control_type == "Menu"]
                if subs:
                    rec["children"] = []
                    walk_menu(subs[0], walker, iuia, depth + 1, rec["children"])
    return out


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    os.makedirs(outdir, exist_ok=True)
    prof = os.path.join(outdir, "_profile")  # outdir-isolated profile per install
    os.makedirs(prof, exist_ok=True)

    task = None
    session_files = []
    rest = sys.argv[3:]
    i = 0
    while i < len(rest):
        if rest[i] == "--task":
            task = rest[i + 1]
            i += 2
        elif rest[i].startswith("--"):
            i += 1
        else:
            session_files.append(rest[i])
            i += 1
    result = {"exe": exe, "session_files": session_files, "tops": {}, "home_tree": []}
    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof}, args=session_files)
    orig = POINT()
    u32.GetCursorPos(ctypes.byref(orig))
    try:
        if not k32.AssignProcessToJobObject(job, k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)):
            k32.TerminateProcess(pi.hProcess, 0)
            raise ctypes.WinError()
        k32.ResumeThread(pi.hThread)
        main_h = None
        t0 = time.time()
        while time.time() - t0 < 25 and not main_h:
            for w in top_windows(pi.dwProcessId):
                if get_class(w) == "TViewForm" and u32.IsWindowVisible(w):
                    main_h = w
                    break
            time.sleep(0.5)
        if not main_h:
            result["error"] = "no visible TViewForm"
        else:
            dsk = Desktop(backend="uia")
            win = dsk.window(handle=main_h).wrapper_object()
            win.set_focus()
            time.sleep(1.0)

            # dismiss stray dialogs (license/update/tab-restore) that steal focus:
            for w in top_windows(pi.dwProcessId):
                cls = get_class(w)
                if w != main_h and u32.IsWindowVisible(w) and ("DIALOG" in cls.upper() or cls == "#32768"):
                    u32.PostMessageW(w, 0x0010, 0, 0)  # WM_CLOSE
                    time.sleep(0.4)
            u32.SetForegroundWindow(main_h)
            time.sleep(0.5)

            def dump(el, d=0, o=None, cap=400):
                if o is None:
                    o = []
                if len(o) >= cap or d > 12:
                    return o
                info = el.element_info
                try:
                    r = el.rectangle()
                    o.append({"d": d, "ct": info.control_type, "name": info.name, "cls": info.class_name,
                              "aid": info.automation_id, "rect": [r.left, r.top, r.width(), r.height()]})
                except Exception as e:
                    o.append({"d": d, "error": str(e)[:60]})
                    return o
                try:
                    for c in el.children():
                        dump(c, d + 1, o, cap)
                except Exception:
                    pass
                return o


            if task:
                # find THomeTaskBtn whose UIA name equals the task, click to open session
                def btn_ok(nm):
                    return nm and task.lower() in nm.replace("&", "").lower()

                found = [n for n in dump(win) if n.get("cls") == "THomeTaskBtn" and btn_ok(n.get("name"))]
                if not found:
                    result["error"] = f"task button not found: {task}; have: {[n.get('name') for n in dump(win) if n.get('cls') == 'THomeTaskBtn']}"
                else:
                    def find_btn(el, d=0):
                        if d > 10:
                            return None
                        if el.element_info.class_name == "THomeTaskBtn" and btn_ok(el.element_info.name):
                            return el
                        for c in el.children():
                            r = find_btn(c, d + 1)
                            if r:
                                return r
                        return None

                    btn = find_btn(win)
                    btn.click_input()
                    time.sleep(2.5)
                    # dismiss any file/browse dialog that popped (WM_CLOSE), view stays
                    for w in top_windows(pi.dwProcessId):
                        if w != main_h and u32.IsWindowVisible(w):
                            cls = get_class(w)
                            if "DIALOG" in cls.upper() or cls == "#32768":
                                u32.PostMessageW(w, 0x0010, 0, 0)
                                time.sleep(0.5)
                    u32.SetForegroundWindow(main_h)
                    time.sleep(0.6)

            def find_menubar(el, d=0):
                if d > 8:
                    return None
                if el.element_info.control_type == "MenuBar" and el.element_info.class_name == "TUiMainMenu":
                    return el
                for c in el.children():
                    r = find_menubar(c, d + 1)
                    if r:
                        return r
                return None

            mb = find_menubar(win)
            result["title"] = get_window_text(main_h)
            if mb is None:
                result["error"] = "no TUiMainMenu"
            else:
                iuia = IUIA().iuia
                walker = iuia.RawViewWalker
                for top in mb.children():
                    name = top.element_info.name
                    rec = []
                    def popup_window():
                        for w in top_windows(pi.dwProcessId):
                            if get_class(w) == "TTBPopupWindow" and u32.IsWindowVisible(w):
                                return w
                        return None

                    def popup_for(item):
                        pw = popup_window()
                        if pw is None:
                            return None
                        tr = item.rectangle()
                        r = wintypes.RECT()
                        u32.GetWindowRect(pw, ctypes.byref(r))
                        # popup must horizontally contain the top item's left edge
                        if r.left - 40 <= tr.left <= r.right + 40:
                            return pw
                        return None

                    try:
                        top.click_input()  # open (first click may only enter menu mode)
                        time.sleep(1.0)
                        pw = None
                        for attempt in range(5):
                            pw = popup_for(top)
                            if pw:
                                break
                            time.sleep(0.5)
                            top.click_input()
                            time.sleep(0.8)
                        if pw is not None:
                            pel = dsk.window(handle=pw).wrapper_object()
                            menus = [c for c in pel.children() if c.element_info.control_type == "Menu"]
                            if not menus:
                                menus = [pel]
                            walk_menu(menus[0], walker, iuia, 0, rec)
                        else:
                            rec = [{"expand_error": "no owned TTBPopupWindow after clicks"}]
                        # close: re-click same top until its popup is gone; ESC + CANCELMODE fallback
                        for _ in range(4):
                            if popup_for(top) is None:
                                break
                            top.click_input()
                            time.sleep(0.5)
                        if popup_window() is not None:
                            win.type_keys("{ESC}")
                            time.sleep(0.4)
                            u32.PostMessageW(main_h, WM_CANCELMODE, 0, 0)
                        time.sleep(0.4)
                    except Exception as e:
                        rec = [{"error": str(e)[:120]}]
                        u32.PostMessageW(main_h, WM_CANCELMODE, 0, 0)
                        u32.keybd_event(0x1B, 0, 0, 0)
                        u32.keybd_event(0x1B, 0, 2, 0)
                    result["tops"][name] = rec

            # full home tree (for toolbar/statusbar inventory)
            tree = dump(win)
            result["home_tree"] = tree
            # identify the ACTIVE view by its main content child class
            def top_content(node, d=0):
                if d > 6:
                    return []
                hits = []
                for c in node.get("children", []):
                    cls = c.get("cls", "")
                    if cls.endswith("View") and cls != "TViewForm":
                        hits.append(cls)
                    hits += top_content(c, d + 1)
                return hits

            result["active_view"] = top_content(tree[0] if tree and "children" not in tree[0] else None)
            # reconstruct nested view classes from flat dump: find ct=Pane with cls *View
            result["active_view"] = sorted({n["cls"] for n in tree if n.get("cls", "").endswith("View")})
            u32.SetCursorPos(orig.x, orig.y)
    finally:
        shutdown(job, pi)
    with open(os.path.join(outdir, "gui-home.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    for k, v in result["tops"].items():
        print(f"{k}: {len(v)} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
