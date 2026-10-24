#!/usr/bin/env python3
"""Live Folder Compare gate (docs/20 feature 3 GUI tier-1; measured model
docs/19 §6.20, extracted/live/folderview-en/folderview-findings.json).

Claims under test (positive) — all traced to the probe artifact:
  1. GEOMETRY — one full-width TDirTreeView list (the measured model: ONE
     control drawing BOTH sides), nonzero height.
  2. TINTS (engine-driven statuses) — cursor tint light blue (168,205,241) on
     the FIRST row (initial cursor); zebra (248,250,249) on odd data rows;
     red (255,0,0) diff text; purple (106,0,213) BOTH orphan rows; gray
     (128,128,128) newer-row text.
  3. CURSOR — a click on the b.txt row moves the cursor tint to that row
     (measured: the selection follows the click, C-selcheck).

Negative (TEST-INJECTION env, never set in product use):
  REACMP_FOLDER_NEG=1 — the click is accepted but the cursor never moves;
  the gate MUST catch the tint staying on row 0.

Usage: python tools/uia-folder-check.py [negative]
Fixtures are generated under _tmp/dirgate (the probe fixture family).
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
FXDIR = os.path.join(ROOT, "_tmp", "dirgate")

CURSOR = (168, 205, 241)
ZEBRA = (248, 250, 249)
RED = (255, 0, 0)
PURPLE = (106, 0, 213)
GRAY = (128, 128, 128)
PITCH = 20.5


def near(p, t, tol=8):
    # int() cast MANDATORY (numpy uint8 wrap; see uia-overview-check)
    return max(abs(int(p[0]) - t[0]), abs(int(p[1]) - t[1]),
               abs(int(p[2]) - t[2])) <= tol


def make_fixtures():
    if os.path.exists(FXDIR):
        shutil.rmtree(FXDIR)
    L = os.path.join(FXDIR, "L")
    R = os.path.join(FXDIR, "R")
    os.makedirs(os.path.join(L, "sub"))
    os.makedirs(os.path.join(R, "sub"))

    def w(base, name, content):
        with open(os.path.join(base, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    w(L, "a.txt", "alpha\n"); w(R, "a.txt", "alpha\n")
    w(L, "b.txt", "left-B\n"); w(R, "b.txt", "right-B\n")
    w(L, "c.txt", "leftonly\n")
    w(R, "d.txt", "rightonly\n")
    w(L, "newer.txt", "x\n"); w(R, "newer.txt", "x\n")
    w(L, os.path.join("sub", "s.txt"), "s\n")
    w(R, os.path.join("sub", "s.txt"), "s\n")
    os.utime(os.path.join(L, "newer.txt"), (1580515200, 1580515200))
    os.utime(os.path.join(R, "newer.txt"), (1706745600, 1706745600))
    return L, R


def find_tree(win):
    hit = []

    def rec(n, d=0):
        try:
            if d > 22:
                return
            if (n.element_info.class_name or "") == "TDirTreeView":
                r = n.rectangle()
                if r.width() > 100:  # the collapsed [0,0,0,0] log-list twin
                    hit.append([r.left, r.top, r.width(), r.height(), n])
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return hit[0] if hit else None


def statusbar_texts(win):
    """The TUiStatusBar Text element names, in order (8 cells)."""
    out = []

    def rec(n, d=0):
        try:
            if d > 22:
                return
            if (n.element_info.control_type or "") == "StatusBar":
                for c in n.children():
                    nm = c.element_info.name
                    out.append(nm if nm is not None else "")
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return out


def count_color(arr, rect, color, tol=8):
    x0, y0, w, h = rect
    c = 0
    for y in range(y0, min(y0 + h, arr.shape[0]), 2):
        for x in range(x0, min(x0 + w, arr.shape[1]), 2):
            if near(arr[y, x], color, tol):
                c += 1
    return c


def cursor_y(arr, rect):
    """First y carrying the cursor tint inside the list rect."""
    for y in range(rect[1], min(rect[1] + rect[3], arr.shape[0])):
        for x in range(rect[0], min(rect[0] + rect[2], arr.shape[1]), 3):
            if near(arr[y, x], CURSOR):
                return y
    return None


def main():
    negative = len(sys.argv) > 1 and sys.argv[1] == "negative"
    L, R = make_fixtures()
    env = dict(os.environ, DOTNET_NOLOGO="1",
               REACMP_FOLDER_NEG="1" if negative else "0",
               REACMP_FOLDER_SB_NEG="1" if negative else "0")
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

        # --- 1. geometry: one full-width tree list ---
        tr = find_tree(win)
        if tr is None:
            problems.append("[geometry] TDirTreeView list not found (nonzero)")
            print("\n".join(problems), file=sys.stderr)
            return 1
        img, wrect = capture_window(hwnd)
        WX, WY = wrect[0], wrect[1]
        if tr[2] < 0.9 * wrect[2]:
            problems.append(f"[geometry] list width {tr[2]} < 90% of window {wrect[2]}")

        import numpy as np
        arr = np.asarray(img.convert("RGB"))
        lrect = (tr[0] - WX, tr[1] - WY, tr[2], tr[3])

        # --- 2. tints (engine-driven statuses) ---
        cy0 = cursor_y(arr, lrect)
        if cy0 is None:
            problems.append("[tints] cursor tint missing on the initial row")
        pink = count_color(arr, lrect, ZEBRA)
        if pink < 6:
            problems.append(f"[tints] zebra rows missing (count={pink})")
        red = count_color(arr, lrect, RED)
        if red < 6:
            problems.append(f"[tints] red diff text missing (count={red})")
        purple = count_color(arr, lrect, PURPLE)
        if purple < 6:
            problems.append(f"[tints] purple orphan text missing (count={purple})")
        gray = count_color(arr, lrect, GRAY, tol=6)
        if gray < 6:
            problems.append(f"[tints] gray newer text missing (count={gray})")

        # --- 2b. status-bar census (docs/21 A): engine aggregation, not the
        # static captured string. Fixture: L files a(6)+b(7)+c(9)+newer(2)
        # = 4 file(s), 24 bytes; R a(6)+b(8)+d(10)+newer(2) = 4, 26.
        sb = statusbar_texts(win)
        want_l = "4 file(s), 24 bytes"
        want_r = "4 file(s), 26 bytes"
        if len(sb) < 8:
            problems.append(f"[statusbar] expected 8 cells, got {sb}")
        else:
            if negative:
                if sb[1] != "999 file(s), 999 bytes" or sb[5] != "999 file(s), 999 bytes":
                    print("NEGATIVE FAILED: census still correct despite injection",
                          file=sys.stderr)
                    return 1
                print("NEGATIVE OK: census reports injected garbage — caught")
                return 0
            if sb[1] != want_l:
                problems.append(f"[statusbar] left census want {want_l!r} got {sb[1]!r}")
            if sb[5] != want_r:
                problems.append(f"[statusbar] right census want {want_r!r} got {sb[5]!r}")
            import re as _re
            for k, nm in ((3, sb[3]), (7, sb[7])):
                if not _re.match(r"^\d+ GB free on [A-Za-z]:\\$", nm or ""):
                    problems.append(f"[statusbar] free cell {k} unexpected: {nm!r}")
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1

        # --- 3. click the b.txt row (visible row 2) moves the cursor ---
        img0, _ = capture_window(hwnd)
        arr0 = np.asarray(img0.convert("RGB"))
        y0 = cursor_y(arr0, lrect)
        import pywinauto.mouse as mouse
        click_y = lrect[1] + int(2.5 * PITCH)
        win.set_focus()
        time.sleep(0.25)
        # screen coords straight from the UIA rect (lrect is capture-relative)
        mouse.click(coords=(tr[0] + 100, tr[1] + int(2.5 * PITCH)))
        time.sleep(0.9)
        img1, _ = capture_window(hwnd)
        arr1 = np.asarray(img1.convert("RGB"))
        y1 = cursor_y(arr1, lrect)
        if negative:
            if y1 != y0:
                print("NEGATIVE FAILED: cursor moved despite injection",
                      file=sys.stderr)
                return 1
            print("NEGATIVE OK: cursor tint stayed on row 0 — caught")
            return 0
        expected = lrect[1] + int(2 * PITCH)
        if y1 is None or abs(y1 - expected) > PITCH:
            problems.append(f"[cursor] tint not on row 2 after click: y0={y0} y1={y1} "
                            f"expected~{expected}")
        elif y1 == y0:
            problems.append(f"[cursor] tint did not move: {y0}")
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"OK: full-width folder list + engine status tints "
              f"(zebra/red/purple/gray) + cursor follows click ({y0}->{y1})")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
