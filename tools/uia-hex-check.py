#!/usr/bin/env python3
"""Live Hex Compare gate (docs/20 feature 5 GUI tier; measured model docs/19
§6.19, extracted/live/hexview-en/hexview-findings.json).

Claims under test (positive) — all traced to the probe artifact:
  1. GEOMETRY — two THexEditor panes side by side (tree-first = screen right,
     measured preorder), tops aligned.
  2. TINTS (per-BYTE, engine slot stream) — the changed bytes' hex slots carry
     the measured pink band (255,227,227) with red (255,0,0) text; the partial
     tail row shows the light-gray hatch (230,230,230) where a side has no
     byte; the caret is the measured cyan block (0,255,255) in BOTH panes
     (shared cursor, initial = first changed slot).
  3. CURSOR — a click on a left-pane hex cell moves the shared cursor: the
     cyan caret moves to the clicked row in BOTH panes (text-view shared
     model; BC measured cyan on the ascii cell).

Negative (TEST-INJECTION env, never set in product use):
  REACMP_HEX_NEG=1 — the click is accepted but the cursor never moves; the
  gate MUST catch the caret staying put.

Usage: python tools/uia-hex-check.py [negative]
Fixtures are generated under _tmp/hexgate (docs/19 §6.19 probe family).
Exit 0/1/2 like the other live gates.
"""
import ctypes
import os
import shutil
import subprocess
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class  # noqa: E402
from live_text_px import capture_window  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
SPEC = r"D:\Rea\product\gui\spec\menu-spec.json"
ROOT = r"D:\Rea"
FXDIR = os.path.join(ROOT, "_tmp", "hexgate")

PINK = (255, 227, 227)   # changed_byte_band (merge/text family, measured)
RED = (255, 0, 0)        # changed_byte_text
HATCH = (230, 230, 230)  # empty_slot_hatch
CYAN = (0, 255, 255)     # caret


def near(p, t, tol=8):
    # int() cast MANDATORY: numpy uint8 subtraction wraps (254-255 -> 255)
    return max(abs(int(p[0]) - t[0]), abs(int(p[1]) - t[1]),
               abs(int(p[2]) - t[2])) <= tol


def make_fixtures():
    if os.path.exists(FXDIR):
        shutil.rmtree(FXDIR)
    os.makedirs(FXDIR, exist_ok=True)
    L = list(range(0x00, 0x30)); L[8:12] = [0xAA, 0xBB, 0xCC, 0xDD]
    L += [0x30, 0x31, 0x32, 0x33]
    R = list(range(0x00, 0x30)); R[8:12] = [0x11, 0x22, 0x33, 0x44]
    R += [0xF0, 0xF1]
    lp = os.path.join(FXDIR, "h-small-L.bin")
    rp = os.path.join(FXDIR, "h-small-R.bin")
    open(lp, "wb").write(bytes(L))
    open(rp, "wb").write(bytes(R))
    return lp, rp


def find_editors(win):
    eds = []

    def rec(n, d=0):
        try:
            if d > 22:
                return
            if (n.element_info.class_name or "") == "THexEditor":
                r = n.rectangle()
                eds.append([r.left, r.top, r.width(), r.height(), n])
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return eds


def count_color(arr, rect, color, tol=8):
    x0, y0, w, h = rect
    c = 0
    for y in range(y0, min(y0 + h, arr.shape[0]), 2):
        for x in range(x0, min(x0 + w, arr.shape[1]), 2):
            if near(arr[y, x], color, tol):
                c += 1
    return c


def find_cyan_x(arr, rect):
    xs = [x for y in range(rect[1], min(rect[1] + rect[3], arr.shape[0]), 2)
          for x in range(rect[0], min(rect[0] + rect[2], arr.shape[1]), 2)
          if near(arr[y, x], CYAN)]
    return (min(xs), max(xs)) if xs else None


def main():
    negative = len(sys.argv) > 1 and sys.argv[1] == "negative"
    L, R = make_fixtures()
    env = dict(os.environ, DOTNET_NOLOGO="1",
               REACMP_HEX_NEG="1" if negative else "0")
    proc = subprocess.Popen([DLL, "--menu-spec", SPEC, "--dispatch", L, R,
                             "--show"], env=env)
    problems = []
    try:
        hwnd = None
        t0 = time.time()
        while time.time() - t0 < 20:
            for w in top_windows(proc.pid):
                if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w):
                    hwnd = w
                    break
            if hwnd:
                break
            time.sleep(0.4)
        if not hwnd:
            print("product window not found", file=sys.stderr)
            return 2
        time.sleep(2.4)
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        for _ in range(25):
            if u32.GetForegroundWindow() == hwnd:
                break
            win.set_focus()
            time.sleep(0.2)
        time.sleep(0.5)

        # --- 1. geometry: two editors side by side ---
        eds = find_editors(win)
        if len(eds) != 2:
            problems.append(f"[geometry] expected 2 THexEditor, found {len(eds)}")
            print("\n".join(problems), file=sys.stderr)
            return 1
        # tree-first = screen right (measured preorder, same mirror as text)
        rightEd, leftEd = eds
        if not (leftEd[0] < rightEd[0]):
            problems.append(f"[geometry] editors not side-by-side L={leftEd[:2]} R={rightEd[:2]}")
        if abs(leftEd[1] - rightEd[1]) > 4:
            problems.append(f"[geometry] editor tops not aligned: {leftEd[1]} vs {rightEd[1]}")

        img, rect = capture_window(hwnd)
        WX, WY = rect[0], rect[1]
        import numpy as np
        arr = np.asarray(img.convert("RGB"))

        def rel(e):
            return (e[0] - WX, e[1] - WY, e[2], e[3])

        lrect, rrect = rel(leftEd), rel(rightEd)
        # --- 2. tints (engine-driven, per byte) ---
        pinkL = count_color(arr, lrect, PINK)
        redL = count_color(arr, lrect, RED)
        if pinkL < 6:
            problems.append(f"[tints] left pane pink band missing (count={pinkL})")
        if redL < 6:
            problems.append(f"[tints] left pane red changed text missing (count={redL})")
        hatchL = count_color(arr, lrect, HATCH, tol=6)
        if hatchL < 6:
            problems.append(f"[tints] left pane hatch (empty slots) missing (count={hatchL})")
        pinkR = count_color(arr, rrect, PINK)
        if pinkR < 6:
            problems.append(f"[tints] right pane pink band missing (count={pinkR})")
        cyanL0 = find_cyan_x(arr, lrect)
        cyanR0 = find_cyan_x(arr, rrect)
        if not cyanL0 or not cyanR0:
            problems.append(f"[caret] cyan caret missing: L={cyanL0} R={cyanR0}")
            print("\n".join(problems), file=sys.stderr)
            return 1

        # --- 3. click moves the SHARED cursor ---
        img0, _ = capture_window(hwnd)
        arr0 = np.asarray(img0.convert("RGB"))
        cy0 = find_cyan_x(arr0, lrect)
        # click inside the left editor's hex zone, row 0: a fixed +100px lands
        # past the gray offset column into byte slot ~1 (our own metrics)
        import pywinauto.mouse as mouse
        cx = leftEd[0] + 100
        cy = leftEd[1] + 8
        win.set_focus()
        time.sleep(0.25)
        mouse.click(coords=(cx, cy))
        time.sleep(0.9)
        img1, _ = capture_window(hwnd)
        arr1 = np.asarray(img1.convert("RGB"))
        cy1 = find_cyan_x(arr1, lrect)
        ry1 = find_cyan_x(arr1, rrect)
        if negative:
            moved = cy1 != cy0
            if not moved:
                pass  # expected: cursor frozen
            else:
                print("NEGATIVE FAILED: caret moved despite injection", file=sys.stderr)
                return 1
            print("NEGATIVE OK: caret stayed despite click — caught")
            return 0
        if cy1 == cy0:
            problems.append(f"[cursor] caret did not move after click at ({cx},{cy}): {cy0}")
        if not ry1 or not cy1:
            problems.append(f"[cursor] caret lost after click: L={cy1} R={ry1}")
        else:
            # shared cursor: the caret's ROW must match across panes (y within
            # one row pitch of each other, both pane-local)
            ly = cy1[0] and None  # x-range only; derive y via a fresh scan
            def cyan_y(arr2, r):
                for y in range(r[1], min(r[1] + r[3], arr2.shape[0])):
                    for x in range(r[0], min(r[0] + r[2], arr2.shape[1]), 2):
                        if near(arr2[y, x], CYAN):
                            return y
                return None
            ly = cyan_y(arr1, lrect)
            ryy = cyan_y(arr1, rrect)
            if ly is None or ryy is None or abs(ly - ryy) > 20:
                problems.append(f"[cursor] caret rows diverge: L y={ly} R y={ryy}")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("OK: hex 2-pane geometry + per-byte pink/red tints + hatch + "
              f"shared cyan caret (moved {cy0}->{cy1} on click)")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
