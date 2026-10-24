#!/usr/bin/env python3
"""Live filter-button probe: BC toolbar display modes, one launch.

Clicks the sequence of MainBar display buttons (default BC term: All/Diffs/
Same/Context/Minor) on a REAL text session, capturing after each step:
  - full-window PrintWindow PNG (row-visibility is a pixel fact: the panes
    expose no line content to UIA),
  - status-bar Text element names (mode label? cursor-status label?),
  - every MainBar button's UIA identity + Toggle pattern state + legacy
    pressed state (HOW selected-ness is exposed is itself the measurement).
Final step clicks a text row to see cursor-following status text.

Safety: view-only clicks on toolbar/pane (no commands, no file mutation);
Job Object containment; strictly serial; zero residue expected.

Usage: python tools/live-text-filter-probe.py <BCompare.exe> <outdir> <L> <R>
       [--buttons Diffs,Same,Context,Minor,All] [--row-click 3]
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import launch, create_kill_job, top_windows, get_class, get_window_text, shutdown  # noqa: E402
from live_text_px import capture_window  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
k32.AssignProcessToJobObject.restype = wintypes.BOOL
k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.ResumeThread.argtypes = [wintypes.HANDLE]

UIA_TogglePatternId = 10009


def by_ct(win, ct, out=None, d=0):
    if out is None:
        out = []
    if d > 14:
        return out
    try:
        if (win.element_info.control_type or "") == ct:
            out.append(win)
        for c in win.children():
            by_ct(c, ct, out, d + 1)
    except Exception:
        pass
    return out


def btn_state(el):
    """identity + toggle state + legacy pressed state (measured exposure)."""
    raw = el.element_info.element
    info = {"name": el.element_info.name or "",
            "ct": el.element_info.control_type or "",
            "cls": el.element_info.class_name or ""}
    try:
        pat = raw.GetCurrentPattern(UIA_TogglePatternId)
        if pat:
            from comtypes.gen.UIAutomationClient import IUIAutomationTogglePattern
            info["toggle"] = pat.QueryInterface(IUIAutomationTogglePattern).CurrentToggleState
        else:
            info["toggle"] = None
    except Exception as e:
        info["toggle_err"] = str(e)[:60]
    try:
        # LegacyIAccessible CurrentState bit 0x0008 = pressed? record raw value.
        LEGACY_ID = 10021
        lp = raw.GetCurrentPattern(LEGACY_ID)
        if lp:
            from comtypes.gen.UIAutomationClient import IUIAutomationLegacyIAccessiblePattern
            info["legacy_state"] = lp.QueryInterface(IUIAutomationLegacyIAccessiblePattern).CurrentState
    except Exception:
        pass
    return info


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    left, right = os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
    buttons = ["Diffs", "Same", "Context", "Minor", "All"]
    if "--buttons" in sys.argv:
        buttons = sys.argv[sys.argv.index("--buttons") + 1].split(",")
    row_click = 3
    if "--row-click" in sys.argv:
        row_click = int(sys.argv[sys.argv.index("--row-click") + 1])
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    meta = {"exe": exe, "left": left, "right": right, "buttons": buttons, "steps": []}
    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof}, args=[left, right])
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
            meta["error"] = "no TViewForm"
            print(json.dumps(meta, ensure_ascii=False))
            return 1
        from pywinauto import Desktop
        dsk = Desktop(backend="uia")
        win = dsk.window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(1.5)

        def snapshot(tag):
            img, (wx, wy, ww, wh) = capture_window(main_h)
            png = f"{tag}.png"
            img.save(os.path.join(outdir, png))
            texts = [t.element_info.name or "" for t in by_ct(win, "Text")]
            steps = []
            for b in by_ct(win, "Button"):
                s = b.element_info.name or ""
                if s in buttons or s in ("All", "Diffs", "Same", "Context", "Minor", "Rules"):
                    steps.append(btn_state(b))
            rec = {"tag": tag, "png": png, "win_rect": [wx, wy, ww, wh],
                   "title": get_window_text(main_h),
                   "text_names": texts, "filter_buttons": steps}
            meta["steps"].append(rec)
            print(tag, "| texts:", [x for x in texts if x][:6])

        snapshot("step0-initial")

        for name in buttons:
            els = [b for b in by_ct(win, "Button") if (b.element_info.name or "") == name]
            if not els:
                meta["steps"].append({"tag": f"click-{name}", "error": "button not found"})
                print(f"click-{name}: NOT FOUND")
                continue
            els[0].click_input()
            time.sleep(1.0)
            snapshot(f"click-{name}")

        # cursor-following test: click the Nth row band in the right pane
        if row_click:
            editors = [e for e in by_ct(win, "Pane") if (e.element_info.class_name or "") == "TTextEditor"]
            # tree order right-first (measured); pick the 2nd = left pane for a
            # stable left click? click CENTER pane of the FIRST editor (right)
            if editors:
                r = editors[0].rectangle()
                x = r.left + r.width() // 2
                y = r.top + 15 * row_click + 7   # measured pitch 15, first row y=0
                u32.SetCursorPos(x, y)
                time.sleep(0.3)
                u32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.05)
                u32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(1.0)
                snapshot(f"row-click-{row_click}")
    finally:
        shutdown(job, pi)
    with open(os.path.join(outdir, "filter-meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
