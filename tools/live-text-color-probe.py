#!/usr/bin/env python3
"""Live text-pane capture: screenshot + UIA dynamic-state snapshot of a
BC text session WITH CONTENT (engine-wiring color/dynamic-face ground truth).

Launches the reference BCompare with a two-file text pair, waits for the
TViewForm, then:
  - PrintWindow(PW_RENDERFULLCONTENT) the full window to PNG;
  - crops the two TTextEditor panes (left/right) to PNGs;
  - records UIA dynamic state: MainBar filter-button names, status-bar text
    names (Load time / pane footers), window title.
NO color analysis here — sampling reads the stored PNGs offline (probe /
analysis separation, same discipline as the menu/chrome probes).

Usage: python tools/live-text-color-probe.py <BCompare.exe> <outdir> <left> <right>
       [--profile <dir>]
Safety: Job Object kill-on-close; strictly serial; zero residue expected.
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import launch, create_kill_job, top_windows, get_class, get_window_text, shutdown  # noqa: E402

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
    """PrintWindow into a top-down RGB PIL image (physical pixels)."""
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


def find_by_class(root, cls, out):
    try:
        if (root.element_info.class_name or "") == cls:
            out.append(root)
        for c in root.children():
            find_by_class(c, cls, out)
    except Exception:
        pass
    return out


def find_text(root, out):
    try:
        if (root.element_info.control_type or "") == "Text":
            out.append(root)
        for c in root.children():
            find_text(c, out)
    except Exception:
        pass
    return out


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    left, right = os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
    prof = None
    if "--profile" in sys.argv:
        prof = os.path.abspath(sys.argv[sys.argv.index("--profile") + 1])
    if prof is None:
        prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    meta = {"exe": exe, "left": left, "right": right, "profile": prof}
    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof}, args=[left, right])
    try:
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)
        if not k32.AssignProcessToJobObject(job, h):
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
            meta["error"] = "no visible TViewForm within 25s"
            print(json.dumps(meta, ensure_ascii=False))
            return 1

        from pywinauto import Desktop
        dsk = Desktop(backend="uia")
        win = dsk.window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(1.5)
        meta["title"] = get_window_text(main_h)

        img, (wx, wy, ww, wh) = capture_window(main_h)
        img.save(os.path.join(outdir, "window.png"))
        meta["window_rect"] = [wx, wy, ww, wh]
        meta["png_size"] = [img.width, img.height]

        # the two main text panes (tree order: left, right)
        editors = find_by_class(win, "TTextEditor", [])
        details = find_by_class(win, "TTextDetailsEditor", [])
        meta["editor_count"], meta["details_count"] = len(editors), len(details)

        # --click-pane N: activate the Nth editor (UIA tree order) BEFORE the
        # second capture. Active/inactive dimming vs capture artifact test:
        # if the 0.8-blend tint follows focus, it is a real per-pane-state rule.
        if "--click-pane" in sys.argv:
            idx = int(sys.argv[sys.argv.index("--click-pane") + 1])
            if idx < len(editors):
                editors[idx].click_input()
                time.sleep(1.0)
                img = capture_window(main_h)[0]
                img.save(os.path.join(outdir, "window-after-click.png"))
                meta["clicked_pane"] = idx
        crops = []
        for i, e in enumerate(editors[:2]):
            r = e.rectangle()
            box = (r.left - wx, r.top - wy, r.right - wx, r.bottom - wy)
            box = tuple(max(0, v) for v in box)
            try:
                crop = img.crop(box)
                name = f"editor{i}.png"
                crop.save(os.path.join(outdir, name))
                crops.append({"png": name, "screen_rect": [r.left, r.top, r.width(), r.height()],
                              "crop_box": list(box)})
            except Exception as ex:
                crops.append({"error": str(ex)[:100],
                              "screen_rect": [r.left, r.top, r.width(), r.height()]})
        meta["editors"] = crops

        # dynamic state: filter-bar buttons (MainBar) + all Text elements
        # (status-bar runtime labels: 'Load time ...', pane footers '1: 1')
        texts = [t.element_info.name or "" for t in find_text(win, [])]
        meta["text_names"] = texts
        buttons = [b.element_info.name or "" for b in find_by_class(win, "", [])
                   if (b.element_info.control_type or "") in ("Button", "MenuItem")]
        meta["button_names"] = buttons
    finally:
        shutdown(job, pi)
    with open(os.path.join(outdir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("OK title:", meta.get("title"), "| editors:", meta.get("editor_count"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
