#!/usr/bin/env python3
"""Live Text Merge gate (docs/20 §6 step 4, D4; measured model docs/19 §6.15).

Product-side assertions of the measured merge behavior:
  1. GEOMETRY — three source panes side by side (class MergePane, names
     left/center/right) + one output pane (class MergeOutput) below; the
     measured Take group present (Conflict / Left / Center / Right /
     Next Conflict / Prev Conflict as UIA button names).
  2. STATUS — the conflict fixture's status line reads the measured
     `# N conflict section(s)` form (engine count, not a GUI re-classify).
  3. TAKE — initial shared cursor sits on the first conflict row (measured:
     a fresh view positions at the first actionable section); invoking the
     `Left` button resolves that section: the `# ... conflict` marker
     disappears AND the output band at that row flips from the measured
     unresolved red (255,227,227) to took-left (213,255,255).

Negative (REACMP_MERGE_NEG=1): Take is accepted by the UI but never changes
the resolution — the gate MUST catch the status/band staying unchanged.
Proves the take-wiring assertions have teeth.

Usage: python tools/uia-text-merge-check.py <L> <R> <C> [negative]
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
SPEC = r"D:\Rea\product\gui\spec\menu-spec.json"
ROOT = r"D:\Rea"
PAL = os.path.join(ROOT, "extracted", "live", "textmerge-en", "merge-palette.json")
PITCH = 15  # colors.json row_pitch_px (same face as the text view)

TAKE_NAMES = {"Conflict", "Left", "Center", "Right", "Next Conflict", "Prev Conflict"}
SECTION_RE = re.compile(r"(# (\d+) conflict section)|(\d+) difference section")


def near(p, t, tol=8):
    # owner-drawn band rects are anti-alias-FREE (SolidColorBrush fills), so
    # the measured RGB is exact; a tight tolerance only forgives the odd
    # text glyph edge. A loose one would read plain white (255,255,255) as a
    # red band (255,227,227) — caught in the first live run.
    return max(abs(int(p[0]) - t[0]), abs(int(p[1]) - t[1]), abs(int(p[2]) - t[2])) <= tol


def collect(win):
    panes, btns, status = {}, {}, []

    def rec(n, d=0):
        try:
            if d > 22:
                return
            ei = n.element_info
            cls = ei.class_name or ""
            nm = ei.name or ""
            if cls in ("MergePane", "MergeOutput"):
                r = n.rectangle()
                panes[nm] = (r.left, r.top, r.width(), r.height())
            if (ei.control_type or "") == "Button" and nm in TAKE_NAMES:
                r = n.rectangle()
                btns[nm] = (r.left, r.top, r.width(), r.height(), n)
            m = SECTION_RE.search(nm)
            if m:
                status.append(nm)
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return panes, btns, status


def output_band(arr, rect, row_index, WY, WX):
    """Dominant saturated color in the output pane at grid row `row_index`."""
    x0, y0, w, h = rect
    y = int(y0 - WY + (row_index + 0.5) * PITCH)
    c = Counter()
    for xx in range(int(x0 - WX + 10), int(x0 - WX + w - 12), 2):
        if 0 <= y < arr.shape[0] and 0 <= xx < arr.shape[1]:
            c[tuple(int(v) for v in arr[y, xx, :3])] += 1
    return c


def main():
    left, right, center = (os.path.abspath(sys.argv[i]) for i in (1, 2, 3))
    negative = len(sys.argv) > 4 and sys.argv[4] == "negative"
    full_pal = json.load(open(PAL, encoding="utf-8"))
    pal = full_pal["tint_measured"]
    RED = tuple(full_pal["conflict_measured"]["output_band"])
    OUTL = tuple(pal["output_took_left_band"])
    LEFTB = tuple(pal["left_change_band"])

    env = dict(os.environ, DOTNET_NOLOGO="1",
               REACMP_MERGE_NEG="1" if negative else "0")
    proc = subprocess.Popen([DLL, "--menu-spec", SPEC, "--merge",
                             left, right, center, "--show"], env=env)
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

        problems = []
        # --- 1. geometry + Take group ---
        panes, btns, status = collect(win)
        for side in ("left", "center", "right"):
            if side not in panes:
                problems.append(f"[geometry] source pane '{side}' missing: {sorted(panes)}")
        if "output" not in panes:
            problems.append(f"[geometry] output pane missing: {sorted(panes)}")
        # source panes side by side (increasing left, same top-ish)
        if all(s in panes for s in ("left", "center", "right")):
            xs = [panes[s][0] for s in ("left", "center", "right")]
            if not (xs[0] < xs[1] < xs[2]):
                problems.append(f"[geometry] source panes not side-by-side: {xs}")
        # output below the source row
        if "output" in panes and all(s in panes for s in ("left",)):
            if panes["output"][1] <= panes["left"][1]:
                problems.append("[geometry] output not below the source panes")
        missing_take = TAKE_NAMES - set(btns)
        if missing_take:
            problems.append(f"[take buttons] missing UIA buttons: {sorted(missing_take)}")

        # --- 2. status shows a conflict count ---
        conflict_line = next((s for s in status if "conflict section" in s), None)
        if not conflict_line:
            problems.append(f"[status] no '# N conflict section(s)' line: {status}")

        # locate the conflict row = the row the cursor starts on (engine order
        # from the dump would be authoritative, but the fixture is known: the
        # conflict is grid row 1). Re-derive from the band: scan output rows for
        # the unresolved RED, first hit = conflict row.
        img, rect = capture_window(hwnd)
        WX, WY = rect[0], rect[1]
        import numpy as np
        arr = np.asarray(img.convert("RGB")) if hasattr(img, "convert") else np.asarray(img)
        conflict_row = None
        for r in range(0, 12):
            c = output_band(arr, panes["output"], r, WY, WX) if "output" in panes else Counter()
            if c.get(RED, 0) + sum(v for k, v in c.items() if near(k, RED)) >= 6:
                conflict_row = r
                break
        if conflict_row is None:
            problems.append("[bands] no unresolved-red output band found "
                            "(measured: conflict holds center on red)")
            print("\n".join(problems), file=sys.stderr)
            return 1

        # --- 3. Take Left flips band + clears the conflict marker ---
        if "Left" not in btns:
            problems.append("[take] Left button not available to invoke")
            print("\n".join(problems), file=sys.stderr)
            return 1
        for attempt in range(2):
            win.set_focus(); time.sleep(0.2)
            btns["Left"][4].invoke()
            time.sleep(0.9)
            panes2, _, status2 = collect(win)
            img2, _ = capture_window(hwnd)
            arr2 = np.asarray(img2.convert("RGB")) if hasattr(img2, "convert") else np.asarray(img2)
            c2 = output_band(arr2, panes2["output"], conflict_row, WY, WX)
            conflict_line2 = next((s for s in status2 if "conflict section" in s), None)
            has_left_band = sum(v for k, v in c2.items() if near(k, OUTL)) >= 6
            resolved = (conflict_line2 is None) and has_left_band
            if resolved or negative:
                break

        if negative:
            if conflict_line2 is None and has_left_band:
                print("NEGATIVE FAILED: Take still resolved despite injection",
                      file=sys.stderr)
                return 1
            print(f"NEGATIVE OK: Take did not resolve (status kept "
                  f"{conflict_line2!r}, band flipped={has_left_band}) — caught")
            return 0

        if conflict_line2 is not None:
            problems.append(f"[take] after Left, status still shows conflict: {conflict_line2!r}")
        if not has_left_band:
            problems.append(f"[take] after Left, output band not took-left {OUTL} "
                            f"(counts={c2.most_common(3)})")
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("OK: merge geometry(3 source panes + output) + Take group present + "
              f"# conflict status + Take Left resolves band {RED}->{OUTL}")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
