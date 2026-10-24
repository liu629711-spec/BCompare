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
    print("capture rect:", rect, "img size:", img.size)
    WX, WY = rect[0], rect[1]
    arr = __import__("numpy").asarray(img.convert("RGB"))
    # find TUiDock rect and 'All' button via UIA
    dock = None; allr = None
    def find(el, d=0):
        global dock, allr
        try:
            if d > 22: return
            ei = el.element_info
            if (ei.class_name or "") == "TUiDock" and dock is None:
                r = el.rectangle(); dock = (r.left, r.top, r.width(), r.height())
            if (ei.name or "") == "All" and allr is None:
                r = el.rectangle(); allr = (r.left, r.top, r.width(), r.height())
            for c in el.children(): find(c, d+1)
        except Exception: pass
    find(win)
    print("TUiDock:", dock, "All:", allr)
    # census entire dock band
    x, y, w, h = dock
    c = Counter()
    for yy in range(y - WY, y - WY + h):
        for xx in range(x - WX, x - WX + w):
            if 0 <= yy < arr.shape[0] and 0 <= xx < arr.shape[1]:
                c[tuple(int(v) for v in arr[yy, xx, :3])] += 1
    print("dock band census:", c.most_common(6))
    # also sample the screen directly at the All button center via GetPixel
    g32 = ctypes.windll.gdi32
    dc = u32.GetDC(0)
    px = g32.GetPixel(dc, allr[0] + allr[2]//2, allr[1] + allr[3]//2)
    print("GetPixel at All center: B=%d G=%d R=%d" % (px & 255, (px >> 8) & 255, (px >> 16) & 255))
    u32.ReleaseDC(0, dc)
finally:
    proc.terminate(); proc.wait(timeout=8)
