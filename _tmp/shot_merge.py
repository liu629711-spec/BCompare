#!/usr/bin/env python3
"""Screenshot the shipping LiuCompare Text Merge window (conflict fixture)."""
import ctypes, os, subprocess, sys, time
sys.path.insert(0, r"D:\Rea\tools")
from live_probe_job import top_windows, get_class
from live_text_px import capture_window

u32 = ctypes.windll.user32
EXE = r"D:\Rea\product\gui\WpfHost\bin\Release\net8.0-windows\reacmp-gui.exe"
SPEC = r"D:\Rea\product\gui\spec\menu-spec.json"
L = os.path.abspath(r"D:\Rea\_scratch_merge\lc.txt")
R = os.path.abspath(r"D:\Rea\_scratch_merge\rc.txt")
C = os.path.abspath(r"D:\Rea\_scratch_merge\base.txt")
OUT = r"D:\Rea\_tmp\liucompare-merge.png"

proc = subprocess.Popen([EXE, "--menu-spec", SPEC, "--merge", L, R, C, "--show"])
try:
    hwnd=None;t0=time.time()
    while time.time()-t0<20:
        for w in top_windows(proc.pid):
            if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w): hwnd=w;break
        if hwnd: break
        time.sleep(0.4)
    if not hwnd: print("no window"); sys.exit(2)
    time.sleep(2.5)
    img, rect = capture_window(hwnd)
    img.save(OUT)
    print("saved", OUT, img.size)
finally:
    proc.terminate(); proc.wait(timeout=8)
