#!/usr/bin/env python3
"""Dump the live UIA rect tree (first levels) to locate the non-stretched layer."""
import ctypes, os, subprocess, sys, time
sys.path.insert(0, r"D:\Rea\tools")
from live_probe_job import top_windows, get_class

u32 = ctypes.windll.user32
EXE = r"D:\Rea\product\gui\WpfHost\bin\Release\net8.0-windows\reacmp-gui.exe"
spec = r"D:\Rea\product\gui\spec\menu-spec.json"
left = os.path.abspath(r"D:\Rea\_tmp\c_L.txt")
right = os.path.abspath(r"D:\Rea\_tmp\c_R.txt")

proc = subprocess.Popen([EXE, "--menu-spec", spec, "--dispatch", left, right, "--show"])
try:
    hwnd = None; t0 = time.time()
    while time.time() - t0 < 20:
        for w in top_windows(proc.pid):
            if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w):
                hwnd = w; break
        if hwnd: break
        time.sleep(0.4)
    time.sleep(2.2)
    from pywinauto import Desktop
    win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
    wr = win.rectangle()
    print("WINDOW:", wr)

    def rec(n, d=0):
        try:
            if d > 6:
                return
            ei = n.element_info
            cls = ei.class_name or ""
            ct = ei.control_type or ""
            r = n.rectangle()
            rel = (r.left - wr.left, r.top - wr.top, r.width(), r.height())
            if cls:
                print("  " * d + f"{ct:10} {cls:22} {str(ei.name)[:20]!r:22} rel={rel}")
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
finally:
    proc.terminate(); proc.wait(timeout=8)
