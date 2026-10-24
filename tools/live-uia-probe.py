#!/usr/bin/env python3
"""Live UIA accessibility-tree probe for the BCompare GUI oracle (docs/19 §3).

The first probe (live-menu-probe.py) proved the main window has NO native
HMENU (GetMenu empty on every window): the menu bar is the VCL child window
`TUiMainMenu`, owner-drawn. So menu/toolbar structure must be captured via the
accessibility layer. This script:

 1. launches BCompare.exe under a kill-on-close Job Object (containment),
 2. waits for the visible TViewForm top window,
 3. walks the UIA tree (pywinauto backend='uia') of that window,
 4. for each MenuBar child (top menu), tries ExpandCollapse + child dump,
 5. writes a JSON snapshot to <outdir>/uia-snapshot.json,
 6. closes the job (process tree killed).

Usage: python tools/live-uia-probe.py <BCompare.exe> <outdir> [--wait S] [--dump-dialogs]
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (  # noqa: E402  (shared job/launch helpers)
    launch, create_kill_job, top_windows, get_class, get_window_text,
)

from pywinauto import Desktop  # noqa: E402


def dump_element(el, depth=0, max_depth=12, out=None, counter=None):
    if out is None:
        out = []
    if counter is None:
        counter = [0]
    if counter[0] > 20000 or depth > max_depth:
        return out
    counter[0] += 1
    try:
        ct = el.element_info.control_type
        name = el.element_info.name
        aaid = el.element_info.automation_id
        cls = el.element_info.class_name
        rect = el.rectangle()
        rec = {
            "d": depth,
            "ct": ct,
            "name": name,
            "aid": aaid,
            "cls": cls,
            "rect": [rect.left, rect.top, rect.width(), rect.height()],
        }
        out.append(rec)
        for c in el.children():
            dump_element(c, depth + 1, max_depth, out, counter)
    except Exception as e:  # element vanished / unsupported
        out.append({"d": depth, "error": str(e)[:120]})
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    wait = float(sys.argv[sys.argv.index("--wait") + 1]) if "--wait" in sys.argv else 20.0
    os.makedirs(outdir, exist_ok=True)
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)

    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof})
    k32 = ctypes.windll.kernel32
    if not k32.AssignProcessToJobObject(job, k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)):
        k32.TerminateProcess(pi.hProcess, 0)
        raise ctypes.WinError()
    k32.ResumeThread(pi.hThread)
    snap = {"exe": exe, "pid": pi.dwProcessId, "windows": [], "tree": []}
    try:
        t0 = time.time()
        main_hwnd = None
        while time.time() - t0 < wait:
            for w in top_windows(pi.dwProcessId):
                if get_class(w) == "TViewForm" and ctypes.windll.user32.IsWindowVisible(w):
                    main_hwnd = w
                    break
            if main_hwnd:
                time.sleep(2.0)  # let first-run dialogs paint
                break
            time.sleep(0.5)
        if not main_hwnd:
            snap["error"] = "no visible TViewForm within wait"
        else:
            win = Desktop(backend="uia").window(handle=main_hwnd)
            snap["windows"].append({
                "hwnd": main_hwnd, "class": get_class(main_hwnd), "title": get_window_text(main_hwnd),
            })
            snap["tree"] = dump_element(win.wrapper_object())
        with open(os.path.join(outdir, "uia-snapshot.json"), "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=1)
        print("nodes:", len(snap["tree"]))
        # concise menu summary
        menubar_idx = [i for i, n in enumerate(snap["tree"]) if n.get("ct") == "MenuBar"]
        print("MenuBar nodes:", len(menubar_idx))
        for i in menubar_idx[:3]:
            parent_d = snap["tree"][i]["d"]
            kids = []
            for n in snap["tree"][i + 1:]:
                if n["d"] <= parent_d:
                    break
                if n["d"] == parent_d + 1:
                    kids.append(n.get("name") or n.get("ct"))
            print("  menu children:", kids)
    finally:
        ctypes.windll.kernel32.CloseHandle(job)
    if pi.hProcess:
        ctypes.windll.kernel32.WaitForSingleObject(pi.hProcess, 5000)
        ctypes.windll.kernel32.CloseHandle(pi.hProcess)
        ctypes.windll.kernel32.CloseHandle(pi.hThread)
    return 0


if __name__ == "__main__":
    sys.exit(main())
