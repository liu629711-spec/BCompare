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
    def find(el, out, d=0):
        try:
            if d > 22: return
            ei = el.element_info
            nm = ei.name or ""
            if (ei.control_type or "") in ("Button","MenuItem") and nm in ("All","Diffs","Same","Context"):
                r = el.rectangle(); out.append((nm, r.left, r.top, r.width(), r.height()))
            for c in el.children(): find(c, out, d+1)
        except Exception: pass
    out = []
    find(win, out)
    for nm, x, y, w, h in out:
        c = Counter()
        for yy in range(y - WY, y - WY + h):
            for xx in range(x - WX, x - WX + w):
                if 0 <= yy < arr.shape[0] and 0 <= xx < arr.shape[1]:
                    c[tuple(int(v) for v in arr[yy, xx, :3])] += 1
        print(nm, (x,y,w,h), c.most_common(4))
finally:
    proc.terminate(); proc.wait(timeout=8)
