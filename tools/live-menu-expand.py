#!/usr/bin/env python3
"""Expand each top-level menu of the BCompare main window and dump items.

Uses pywinauto UIA backend; for each MenuBarItem under the app's TUiMainMenu,
tries the ExpandCollapse pattern (comtypes GetCurrentPattern(10005)); after a
successful expand, re-walks the desktop for the BC popup window (or the menu
item's own children) and dumps MenuItem names/accelerators/toggle states.
Collapses afterwards. Read-only otherwise (no Invoke on dangerous items).

Usage: python tools/live-menu-expand.py <BCompare.exe> <outdir> [--wait S]
"""
import ctypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import launch, create_kill_job, top_windows, get_class, get_window_text  # noqa: E402

from pywinauto import Desktop  # noqa: E402
from comtypes.gen.UIAutomationClient import (  # noqa: E402
    UIA_ExpandCollapsePatternId, IUIAutomationExpandCollapsePattern,
)

UIA_TogglePatternId = 10012
k32 = ctypes.windll.kernel32


def expand(el_raw):
    pat = el_raw.GetCurrentPattern(UIA_ExpandCollapsePatternId)
    if not pat:
        return False
    p = pat.QueryInterface(IUIAutomationExpandCollapsePattern)
    p.Expand()
    return True


def collapse(el_raw):
    try:
        pat = el_raw.GetCurrentPattern(UIA_ExpandCollapsePatternId)
        p = pat.QueryInterface(IUIAutomationExpandCollapsePattern)
        p.Collapse()
    except Exception:
        pass


def dump(el, depth=0, out=None, max_depth=14):
    if out is None:
        out = []
    try:
        info = el.element_info
        raw = getattr(info, 'element', None)
        rec = {
            "d": depth,
            "ct": info.control_type,
            "name": info.name,
            "cls": info.class_name,
            "aid": info.automation_id,
        }
        if raw is not None:
            try:
                tog = raw.GetCurrentPattern(UIA_TogglePatternId)
                if tog:
                    from comtypes.gen.UIAutomationClient import IUIAutomationTogglePattern
                    rec["toggle"] = int(tog.QueryInterface(IUIAutomationTogglePattern).CurrentToggleState)
            except Exception:
                pass
        out.append(rec)
        for c in el.children():
            dump(c, depth + 1, out, max_depth)
    except Exception as e:
        out.append({"d": depth, "error": str(e)[:100]})
    return out


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    wait = float(sys.argv[sys.argv.index("--wait") + 1]) if "--wait" in sys.argv else 25.0
    os.makedirs(outdir, exist_ok=True)
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)

    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof})
    result = {"exe": exe, "top_menus": {}}
    try:
        if not k32.AssignProcessToJobObject(job, k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)):
            k32.TerminateProcess(pi.hProcess, 0)
            raise ctypes.WinError()
        k32.ResumeThread(pi.hThread)
        t0 = time.time()
        main_hwnd = None
        while time.time() - t0 < wait:
            for w in top_windows(pi.dwProcessId):
                if get_class(w) == "TViewForm" and ctypes.windll.user32.IsWindowVisible(w):
                    main_hwnd = w
                    break
            if main_hwnd:
                time.sleep(2.5)
                break
            time.sleep(0.5)
        if not main_hwnd:
            result["error"] = "no visible TViewForm"
        else:
            dsk = Desktop(backend="uia")
            win = dsk.window(handle=main_hwnd).wrapper_object()

            def find_menubar(el, depth=0):
                if depth > 8:
                    return None
                if el.element_info.control_type == "MenuBar" and el.element_info.class_name == "TUiMainMenu":
                    return el
                for c in el.children():
                    r = find_menubar(c, depth + 1)
                    if r:
                        return r
                return None

            menubar_el = find_menubar(win)
            if menubar_el is None:
                result["error"] = "no TUiMainMenu MenuBar"
            else:
                for item in menubar_el.children():
                    nm = item.element_info.name
                    raw = item.element_info.element
                    entry = {"children": [], "expand_error": None}
                    try:
                        ok = expand(raw)
                        if not ok:
                            entry["expand_error"] = "no ExpandCollapse pattern"
                        else:
                            time.sleep(1.2)
                            # popup may appear as a separate window: scan all windows of pid
                            found = []
                            for w2 in top_windows(pi.dwProcessId):
                                cls2 = get_class(w2)
                                if cls2 not in ("TViewForm", "TApplication", "TPUtilWindow") and ctypes.windll.user32.IsWindowVisible(w2):
                                    try:
                                        pw = dsk.window(handle=w2).wrapper_object()
                                        found.append({"hwnd_cls": cls2, "tree": dump(pw)})
                                    except Exception as e:
                                        found.append({"hwnd_cls": cls2, "error": str(e)[:80]})
                            if found:
                                entry["popup"] = found
                            else:
                                entry["children"] = dump(item)
                            collapse(raw)
                            time.sleep(0.5)
                    except Exception as e:
                        entry["expand_error"] = str(e)[:120]
                        # recover: press ESC to close any stuck popup
                        try:
                            ctypes.windll.user32.keybd_event(0x1B, 0, 0, 0)
                            ctypes.windll.user32.keybd_event(0x1B, 0, 2, 0)
                        except Exception:
                            pass
                    result["top_menus"][nm] = entry
        with open(os.path.join(outdir, "menu-expand.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        for nm, e in result["top_menus"].items():
            tag = "popup" if "popup" in e else ("ERR:" + str(e.get("expand_error")) if e.get("expand_error") else "inline")
            n_items = len(e.get("children", [])) or sum(len(x.get("tree", [])) for x in e.get("popup", []))
            print(f"{nm}: {tag}, nodes={n_items}")
    finally:
        k32.CloseHandle(job)
    if pi.hProcess:
        k32.WaitForSingleObject(pi.hProcess, 5000)
        k32.CloseHandle(pi.hProcess)
        k32.CloseHandle(pi.hThread)
    return 0


if __name__ == "__main__":
    sys.exit(main())
