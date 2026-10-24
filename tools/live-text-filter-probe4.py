#!/usr/bin/env python3
"""Consolidated filter-bar probe #4: button rects + selection tint + Rules +
linked footers. One launch, serial, Job Object.

Reads, per step:
  - UIA rects + (ct,cls,name) of MainBar filter buttons (All/Diffs/Same/
    Context/Minor/Rules/Home/Next Section/Prev Section/Swap/Reload);
  - PrintWindow tint sampled INSIDE each button rect (selection appearance);
  - pane status-bar footer Text names (the '1: 1' elements, both panes);
Steps: initial; click Diffs; click Rules; click left-pane row 4; click
right-pane row 6 (footer linkage question); click Same.

Usage: python tools/live-text-filter-probe4.py <exe> <outdir> <L> <R>
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import launch, create_kill_job, top_windows, get_class, shutdown  # noqa: E402
from live_text_px import capture_window  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
k32.AssignProcessToJobObject.restype = wintypes.BOOL
k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.ResumeThread.argtypes = [wintypes.HANDLE]

FILTERS = ("All", "Diffs", "Same", "Context", "Minor", "Rules")


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


def find_editors(win, out=None):
    if out is None:
        out = []
    try:
        if (win.element_info.class_name or "") == "TTextEditor":
            out.append(win)
        for c in win.children():
            find_editors(c, out)
    except Exception:
        pass
    return out


def pane_footers(win):
    """Text elements inside TUiStatusBar under each TTextEditor (footer)."""
    out = []
    for ed in find_editors(win):
        names = [t.element_info.name or "" for t in by_ct(ed, "Text")]
        out.append(names)
    return out


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    left, right = os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    meta = {"exe": exe, "steps": []}
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
            print(json.dumps(meta))
            return 1
        from pywinauto import Desktop
        from collections import Counter
        dsk = Desktop(backend="uia")
        win = dsk.window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(1.5)

        def step(tag):
            img, (wx, wy, ww, wh) = capture_window(main_h)
            png = f"{tag}.png"
            img.save(os.path.join(outdir, png))
            px = img.load()
            rec = {"tag": tag, "png": png, "buttons": [], "footers": pane_footers(win)}
            for b in by_ct(win, "Button"):
                n = b.element_info.name or ""
                if n in FILTERS:
                    r = b.rectangle()
                    # tint = mode color INSIDE the button rect (window-relative)
                    c = Counter()
                    for y in range(r.top - wy + 2, r.bottom - wy - 2):
                        for x in range(r.left - wx + 2, r.right - wx - 2):
                            if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
                                c[px[x, y]] += 1
                    rec["buttons"].append({
                        "name": n, "rect": [r.left - wx, r.top - wy, r.width(), r.height()],
                        "top_colors": [[list(k), v] for k, v in c.most_common(3)]})
            meta["steps"].append(rec)
            print(tag, "| buttons:", [(b["name"], b["top_colors"][0][0] if b["top_colors"] else None)
                                       for b in rec["buttons"]])
            print("     footers:", rec["footers"])

        step("initial")
        btns = {b.element_info.name or "": b for b in by_ct(win, "Button")}
        for name in ("Diffs", "Rules", "Same"):
            btns[name].click_input(); time.sleep(1.0)
            step(f"click-{name}")
        # click rows: left editor row 4 and right editor row 6 (grid pitch 15,
        # first row 0, content top from editor rect + gutter offset)
        eds = find_editors(win)
        for label, ed, k in (("left-row4", eds[1], 3), ("right-row6", eds[0], 5)):
            r = ed.rectangle()
            u32.SetCursorPos(r.left + 200, r.top + 8 + 15 * k + 7)
            time.sleep(0.2)
            u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.05)
            u32.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(1.0)
            step(label)
    finally:
        shutdown(job, pi)
    with open(os.path.join(outdir, "probe4-meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
