"""Shared PrintWindow capture (top-down RGB PIL image) for the live text
checks. PW_RENDERFULLCONTENT(2) renders layered DirectComposition windows —
the route proven to capture a real BC text session (extracted/live/
textcolor-en, 2026-10-21) and therefore valid for the product window too."""
import ctypes
from ctypes import wintypes

u32 = ctypes.windll.user32
g32 = ctypes.windll.gdi32
PW_RENDERFULLCONTENT = 0x00000002


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


def capture_window(hwnd):
    """Returns (PIL RGB image of the window, (x, y, w, h) screen rect)."""
    from PIL import Image
    r = RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc_win = u32.GetWindowDC(hwnd)
    try:
        mem = g32.CreateCompatibleDC(hdc_win)
        bmp = g32.CreateCompatibleBitmap(hdc_win, w, h)
        old = g32.SelectObject(mem, bmp)
        ok = u32.PrintWindow(hwnd, mem, PW_RENDERFULLCONTENT)
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth, bmi.biHeight, bmi.biPlanes = w, -h, 1
        bmi.biBitCount, bmi.biCompression = 32, 0
        buf = ctypes.create_string_buffer(w * h * 4)
        got = g32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bmi), 0)
        g32.SelectObject(mem, old)
        g32.DeleteObject(bmp)
        g32.DeleteDC(mem)
        if not ok or got != h:
            raise RuntimeError(f"PrintWindow/GetDIBits failed: ok={ok} lines={got}")
        img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
        return img, (r.left, r.top, w, h)
    finally:
        u32.ReleaseDC(hwnd, hdc_win)
