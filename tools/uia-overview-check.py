#!/usr/bin/env python3
"""Live overview-strip gate (docs/20 §6 step 3: TUiThumbnail, docs/19 §6.12B).

Claims under test (positive):
  1. GEOMETRY — the TUiThumbnail slot is a left-edge column: width 40..60 px
     (measured reference 52), height >= 60% of the window (measured 729 of
     864), left edge within 120px of the window's left edge, and its top is
     at/above the pane area's top (the strip starts under the toolbar band).
  2. BANDS — every non-`same` grid row (from the engine ledger, written by
     --dump) has the measured status HUE inside the strip at its proportional
     row position: different/leftorphan -> left tint (255,227,227),
     similar -> (238,238,255), rightorphan -> right tint (252,230,230).
     Sampled with a small tolerance (1px bands anti-alias at high row counts).
  3. JUMP — a physical click on the strip at a `different` row moves the
     SHARED cursor: BOTH footers become `{ltid}: 1` / `{rtid}: 1` for that
     grid row (shared-cursor model, docs/19 §6.12).

Negative (REACMP_OVERVIEW_NEG=1): strip still paints, but the click is not
wired -> footers stay at the initial cursor; the gate MUST catch it.

Usage: python tools/uia-overview-check.py <spec.json> <left> <right> [negative]
Exit 0/1/2 like the other live gates.
"""
import ctypes
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class  # noqa: E402
from live_text_px import capture_window  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
ROOT = r"D:\Rea"
COLORS = os.path.join(ROOT, "extracted", "live", "textcolor-en", "colors.json")
FOOTER_RE = re.compile(r"^\d+: \d+$")
LEDGER = os.path.join(ROOT, "_tmp", "overview-ledger.json")


def find_thumb(win):
    hit = []

    def rec(n, d=0):
        try:
            if d > 20:
                return
            if (n.element_info.class_name or "") == "TUiThumbnail":
                hit.append(n)
                return
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return hit[0] if hit else None


def collect_footers(win):
    ft = []

    def rec(n, d=0):
        try:
            if d > 20:
                return
            nm = n.element_info.name or ""
            if FOOTER_RE.match(nm):
                r = n.rectangle()
                ft.append((r.left, nm))
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return [x[1] for x in sorted(ft)]


def near(p, t, tol=26):
    # int() cast is MANDATORY: arr pixels are numpy uint8 and uint8 subtraction
    # WRAPS (254-255 -> 255), so every antialiased edge pixel below the want
    # channel silently failed the comparison (uia-text-merge-check's near has
    # the same cast for the same reason).
    return max(abs(int(p[0]) - t[0]), abs(int(p[1]) - t[1]),
               abs(int(p[2]) - t[2])) <= tol


def main():
    spec_path, left, right = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    negative = len(sys.argv) > 4 and sys.argv[4] == "negative"
    spec = json.load(open(spec_path, encoding="utf-8"))
    colors = json.load(open(COLORS, encoding="utf-8"))
    tints = colors["status_rows"]

    if os.path.exists(LEDGER):
        os.remove(LEDGER)
    env = dict(os.environ, DOTNET_NOLOGO="1",
               REACMP_OVERVIEW_NEG="1" if negative else "0")
    proc = subprocess.Popen([DLL, "--menu-spec", spec_path, "--dispatch",
                             left, right, "--dump", LEDGER, "--show"], env=env)
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
        time.sleep(2.2)
        from pywinauto import Desktop, mouse
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        for _ in range(25):
            if u32.GetForegroundWindow() == hwnd:
                break
            win.set_focus()
            time.sleep(0.2)
        time.sleep(0.4)

        if not os.path.exists(LEDGER):
            print("engine ledger missing (--dump did not run)", file=sys.stderr)
            return 2
        led = json.load(open(LEDGER, encoding="utf-8"))
        rows = led["content"]["rows"]
        n = len(rows)

        problems = []
        # --- 1. geometry ---
        th = find_thumb(win)
        if th is None:
            problems.append("[geometry] TUiThumbnail slot missing from the UIA tree")
            print("\n".join(problems), file=sys.stderr)
            return 1
        wr = win.rectangle()
        tr = th.rectangle()
        rel_l = tr.left - wr.left
        if not (40 <= tr.width() <= 60):
            problems.append(f"[geometry] width {tr.width()} not in [40,60] (measured 52)")
        if rel_l > 120:
            problems.append(f"[geometry] left offset {rel_l} too far right (measured 8)")
        if tr.height() < wr.height() * 0.6:
            problems.append(f"[geometry] height {tr.height()} < 60% of window {wr.height()}")
        eds = []

        def find_ed(nn):
            try:
                if (nn.element_info.class_name or "") == "TTextEditor":
                    eds.append(nn.rectangle())
                    return
                for c in nn.children():
                    find_ed(c)
            except Exception:
                pass
        find_ed(win)
        if eds and abs(tr.top - min(e.top for e in eds)) > 40:
            problems.append(f"[geometry] strip top {tr.top} not aligned with pane top "
                            f"{min(e.top for e in eds)} (+-40)")

        # --- 2. bands ---
        img, (WX, WY, WW, WH) = capture_window(hwnd)
        import numpy as np
        arr = np.asarray(img.convert("RGB")) if hasattr(img, "convert") else np.asarray(img)
        rh = tr.height() / n
        sx = tr.left - WX + max(12, tr.width() // 2)
        miss = []
        for k, row in enumerate(rows):
            st = row["status"]
            if st == "same":
                continue
            side = "right" if row.get("ltext") is None else "left"
            want = tints.get(st, {}).get(side)
            if not want:
                continue
            # Sample SEVERAL points inside the row's band (band start / center
            # / band end, each +-1px). A single center sample fails whenever
            # the row is ALSO the shared-cursor row: the designed selection
            # marker (§6.14 选中行橙线, a 2px orange rule at the row center)
            # then covers the whole +-1 neighborhood once the strip maps 150
            # rows into ~730px (~4.9px per row — the 2px rule eats the band
            # center). The hue must exist SOMEWHERE in the band; the cursor
            # rule legitimately overpaints its middle.
            y0c = tr.top - WY + k * rh
            y1c = tr.top - WY + (k + 1) * rh
            cand = []
            for base in (y0c + 1, (y0c + y1c) / 2, y1c - 2):
                for dy in (-1, 0, 1):
                    yy = int(base) + dy
                    if 0 <= yy < arr.shape[0] and 0 <= sx < arr.shape[1]:
                        cand.append(yy)
            okp = any(near(arr[yy, sx], want) for yy in cand)
            if not okp:
                ymid = int((y0c + y1c) / 2)
                miss.append(f"row{k}/{st}@y{ymid} want{want} "
                            f"got{tuple(int(v) for v in arr[ymid, sx])}")
        if miss:
            problems.append("[bands] missing status hues: " + "; ".join(miss[:4]))

        # --- 3. jump (shared cursor) ---
        # Only rows that carry text on BOTH sides are meaningful for the
        # footer assertion (an orphan row has no id on its void side, so the
        # live footer renders ': 1' there — measured footer format is
        # `{own id}: {col}` and orphaning leaves one side without an id).
        diff_rows = [k for k, r in enumerate(rows)
                     if r["status"] not in ("same",)
                     and r.get("ltext") is not None and r.get("rtext") is not None]
        if not diff_rows:
            problems.append("[jump] fixture has no both-sided non-same rows")
        else:
            # pick the LAST qualifying row: unambiguously different from the
            # initial cursor (which lands on the first `different` row).
            k = diff_rows[-1]
            before = collect_footers(win)
            y = int(tr.top - WY + (k + 0.5) * rh)
            screen_y = y + WY
            screen_x = tr.left + tr.width() // 2
            want = [f"{rows[k]['ltid']}: 1", f"{rows[k]['rtid']}: 1"]
            after = before
            # First click after a fresh launch can land on an inactive window
            # (same measured platform rule as the other live gates) — retry
            # once after re-asserting the foreground.
            for attempt in range(2):
                win.set_focus()
                time.sleep(0.25)
                mouse.click(coords=(screen_x, screen_y))
                time.sleep(0.9)
                after = collect_footers(win)
                if after == want or negative:
                    break
            if negative:
                if after == want:
                    print("NEGATIVE FAILED: click moved the shared cursor despite injection",
                          file=sys.stderr)
                    return 1
                print(f"NEGATIVE OK: strip click did not move the shared cursor "
                      f"(footers {before} -> {after}) — caught")
                return 0
            if after != want:
                problems.append(f"[jump] click row{k} want {want}, got {after}")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("OK: overview strip geometry(left 52px column) + status-hue bands + "
              "click jump updates BOTH footers (shared cursor)")
        return 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
