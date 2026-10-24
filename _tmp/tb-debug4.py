import ctypes, os, subprocess, sys, time
from collections import Counter
sys.path.insert(0, r"D:\Rea\tools")
from live_probe_job import top_windows, get_class
from live_text_px import capture_window
u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
SPEC = r"D:\Rea\product\gui\spec\menu-spec.json"
env = dict(os.environ, DOTNET_NOLOGO="1", REACMP_TB_NEG="0")
proc = subprocess.Popen([DLL, "--menu-spec", SPEC, "--dispatch",
    r"D:\Rea\_tmp\layout-left.txt", r"D:\Rea\_tmp\layout-right.txt", "--show"], env=env)
try:
    hwnd = None
    t0 = time.time()
    while time.time() - t0 < 20:
        for w in top_windows(proc.pid):
            if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w):
                hwnd = w; break
        if hwnd: break
        time.sleep(0.4)
    time.sleep(2.5)
    from pywinauto import Desktop
    win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
    win.set_focus(); time.sleep(1.0)
    img, rect = capture_window(hwnd)
    WX, WY = rect[0], rect[1]
    arr = __import__("numpy").asarray(img.convert("RGB"))
    print("img size:", img.size)
    # census the whole window
    c = Counter()
    for yy in range(0, arr.shape[0], 3):
        for xx in range(0, arr.shape[1], 3):
            c[tuple(int(v) for v in arr[yy, xx, :3])] += 1
    print("whole-window census:", c.most_common(10))
    # find a TTextEditor and sample its first rows
    eds = []
    def find(el, d=0):
        try:
            if d > 22: return
            if (el.element_info.class_name or "") == "TTextEditor":
                r = el.rectangle(); eds.append((r.left, r.top, r.width(), r.height()))
            for ch in el.children(): find(ch, d+1)
        except Exception: pass
    find(win)
    print("editors:", eds)
    for i, (x, y, w, h) in enumerate(eds):
        c2 = Counter()
        for yy in range(y - WY + 5, min(y - WY + 60, arr.shape[0])):
            for xx in range(x - WX + 5, min(x - WX + 200, arr.shape[1]), 2):
                c2[tuple(int(v) for v in arr[yy, xx, :3])] += 1
        print(f"editor{i} top-left census:", c2.most_common(5))
finally:
    proc.terminate(); proc.wait(timeout=8)
