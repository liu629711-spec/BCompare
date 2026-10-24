#!/usr/bin/env python3
"""Live Text Merge MERGE-TO + SWAP gate (docs/19 §6.18 semantics).

Claims under test (positive) — all traced to
extracted/live/textmerge-to-en/merge-to-findings.json:
  1. TITLE FOLLOWS DESTINATION (measured: out.txt -> left.txt the moment the
     Left radio is picked; 3-file form with unnamed Other falls back to the
     center file name). The path field next to 'Other:' shows the CURRENT
     destination path.
  2. SAVE TARGET = RADIO (measured A/B/C2): Ctrl+S after picking Left writes
     the LEFT file (merged content), OUT sentinel untouched; picking Other:
     again and Ctrl+S writes the OUT file. No dialog for a named target.
  3. SWAP SIDES (measured: physical toolbar 'Swap' exchanges the side panes,
     center untouched, output re-materializes with band attribution swapped):
     after Swap the left pane's cyan band sits at the R-fixture row and the
     output band flips took-left cyan -> took-right purple.

Negatives (TEST-INJECTION env, never set in product use):
  mergeto — REACMP_MERGETO_NEG=1: the radio is accepted but the destination
            never moves -> the title/path assertions MUST catch it.
  swap    — REACMP_SWAP_NEG=1: Swap is accepted but sides never exchange ->
            the band-position assertions MUST catch it.

Usage: python tools/uia-text-merge-to-check.py [mergeto|swap]
Exit 0/1/2 like the other live gates. Fixtures are generated under _tmp.
"""
import ctypes
import json
import os
import re
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
PAL = os.path.join(ROOT, "extracted", "live", "textmerge-en", "merge-palette.json")
PITCH = 15
FXDIR = os.path.join(ROOT, "_tmp", "merge-to-gate")

BASE = [f"line {w}" for w in ("one", "two", "three", "four", "five",
                              "six", "seven", "eight")]
LEFT = list(BASE); LEFT[1] = "L-TWO-CHANGED"
RIGHT = list(BASE); RIGHT[4] = "R-FIVE-CHANGED"
MERGED = list(BASE); MERGED[1] = "L-TWO-CHANGED"; MERGED[4] = "R-FIVE-CHANGED"
OUT_PRESET = "PRESETPANE_MERGETO_GATE_1\nPRESETPANE_MERGETO_GATE_2"


def near(p, t, tol=8):
    # owner-drawn band rects are anti-alias-FREE (SolidColorBrush fills); a
    # loose tolerance would read plain white as a pale band (edit-gate lesson)
    return max(abs(int(p[0]) - t[0]), abs(int(p[1]) - t[1]),
               abs(int(p[2]) - t[2])) <= tol


def write(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def band_count(arr, rect, row, WY, WX, color):
    """Exact-match pixel count of `color` on grid row `row` of the pane."""
    x0, y0, w, h = rect
    y = int(y0 - WY + (row + 0.5) * PITCH)
    c = 0
    for xx in range(int(x0 - WX + 2), int(x0 - WX + w - 2), 2):
        if 0 <= y < arr.shape[0] and 0 <= xx < arr.shape[1]:
            if near(arr[y, xx, :3], color):
                c += 1
    return c


def collect(win):
    panes, btns, radios, extra = {}, {}, {}, {}

    def rec(n, d=0):
        try:
            if d > 22:
                return
            ei = n.element_info
            cls = ei.class_name or ""
            nm = ei.name or ""
            ct = ei.control_type or ""
            if cls in ("MergePane", "MergeOutput"):
                r = n.rectangle()
                panes[nm] = (r.left, r.top, r.width(), r.height())
            if ct == "Button" and nm:
                btns[nm] = n
            if ct == "RadioButton" and nm:
                radios[nm] = n
            if nm and (nm.endswith(".txt") or nm.endswith(".txt")) and \
                    os.sep in nm:
                extra[nm] = n          # the MergeToPath destination field
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return panes, btns, radios, extra


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "positive"
    if mode not in ("positive", "mergeto", "swap"):
        print("usage: uia-text-merge-to-check.py [positive|mergeto|swap]",
              file=sys.stderr)
        return 2
    full_pal = json.load(open(PAL, encoding="utf-8"))
    pal = full_pal["tint_measured"]
    LEFTB = tuple(pal["left_change_band"])
    RIGHTB = tuple(pal["right_change_band"])
    OUTL = tuple(pal["output_took_left_band"])
    OUTR = tuple(pal["output_took_right_band"])

    # fresh fixtures
    if os.path.exists(FXDIR):
        shutil.rmtree(FXDIR)
    os.makedirs(FXDIR, exist_ok=True)
    L = os.path.join(FXDIR, "left.txt"); write(L, LEFT)
    R = os.path.join(FXDIR, "right.txt"); write(R, RIGHT)
    C = os.path.join(FXDIR, "base.txt"); write(C, BASE)
    O = os.path.join(FXDIR, "out.txt"); write(O, OUT_PRESET.splitlines())
    orig = {p: read(p) for p in (L, R, C, O)}
    merged_txt = "\n".join(MERGED)

    env = dict(os.environ, DOTNET_NOLOGO="1",
               REACMP_MERGETO_NEG="1" if mode == "mergeto" else "0",
               REACMP_SWAP_NEG="1" if mode == "swap" else "0")
    proc = subprocess.Popen([DLL, "--menu-spec", SPEC, "--merge",
                             L, R, C, O, "--show"], env=env)
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

        def title():
            return win.window_text()

        def invoke(radio):
            try:
                radio.invoke()
            except Exception:
                try:
                    radio.select()
                except Exception:
                    radio.click_input()

        # ---- 1. initial: title=OUT, path field=OUT, radios present ----
        panes, btns, radios, extra = collect(win)
        t0_title = title()
        if t0_title != f"out.txt - Text Merge - LiuCompare":
            problems.append(f"[title] initial expected OUT title, got {t0_title!r}")
        for nm in ("Left", "Right", "Other:"):
            if nm not in radios:
                problems.append(f"[radios] missing {nm!r}: {sorted(radios)}")
        if O not in extra:
            problems.append(f"[path-field] no destination field showing OUT path: {sorted(extra)}")

        # ---- 2. pick Left: title+field follow (mergeto negative catches) ----
        if "Left" in radios:
            win.set_focus(); time.sleep(0.2)
            invoke(radios["Left"])
            time.sleep(0.8)
            _, _, _, extra2 = collect(win)
            t1_title = title()
            if mode == "mergeto":
                if t1_title != f"out.txt - Text Merge - LiuCompare" or L in extra2:
                    print("NEGATIVE FAILED: destination moved despite injection",
                          file=sys.stderr)
                    return 1
                print("NEGATIVE OK: title/path stayed on OUT despite Left "
                      "radio — caught")
                return 0
            if t1_title != f"left.txt - Text Merge - LiuCompare":
                problems.append(f"[title] after Left expected left.txt title, got {t1_title!r}")
            if L not in extra2:
                problems.append(f"[path-field] after Left expected LEFT path in field: {sorted(extra2)}")
        else:
            problems.append("[radios] Left radio missing; cannot continue")
            print("\n".join(problems), file=sys.stderr)
            return 1

        # ---- 3. Ctrl+S writes the LEFT file, OUT untouched ----
        for _ in range(25):
            if u32.GetForegroundWindow() == hwnd:
                break
            win.set_focus(); time.sleep(0.2)
        win.type_keys("^s")
        time.sleep(1.4)
        if read(L) != merged_txt:
            problems.append(f"[save-left] left.txt not the merged output: {read(L)!r:.120}")
        if read(O) != OUT_PRESET:
            problems.append(f"[save-left] out.txt sentinel overwritten: {read(O)!r:.80}")
        if read(R) != orig[R] or read(C) != orig[C]:
            problems.append("[save-left] right/base file modified unexpectedly")

        # ---- 4. back to Other: -> Ctrl+S writes OUT ----
        if "Other:" in radios:
            win.set_focus(); time.sleep(0.2)
            invoke(radios["Other:"])
            time.sleep(0.8)
            if title() != f"out.txt - Text Merge - LiuCompare":
                problems.append(f"[title] after Other: expected OUT title, got {title()!r}")
            win.set_focus()
            win.type_keys("^s")
            time.sleep(1.4)
            if read(O) != merged_txt:
                problems.append(f"[save-other] out.txt not the merged output: {read(O)!r:.120}")
            if read(L) != merged_txt:
                problems.append("[save-other] left.txt changed unexpectedly")

        # ---- 5. Swap: band attribution swaps (swap negative catches) ----
        if "Swap" not in btns:
            problems.append("[swap] no Swap button in the toolbar bar")
        else:
            img, rect = capture_window(hwnd)
            WX, WY = rect[0], rect[1]
            import numpy as np
            arr0 = np.asarray(img.convert("RGB"))
            before = {
                "L_row1": band_count(arr0, panes["left"], 1, WY, WX, LEFTB),
                "L_row4": band_count(arr0, panes["left"], 4, WY, WX, LEFTB),
                "R_row1": band_count(arr0, panes["right"], 1, WY, WX, RIGHTB),
                "R_row4": band_count(arr0, panes["right"], 4, WY, WX, RIGHTB),
                "OUT_row1_left": band_count(arr0, panes["output"], 1, WY, WX, OUTL),
                "OUT_row1_right": band_count(arr0, panes["output"], 1, WY, WX, OUTR),
            }
            win.set_focus(); time.sleep(0.2)
            btns["Swap"].invoke()
            time.sleep(1.0)
            panes2, _, _, _ = collect(win)
            img2, _ = capture_window(hwnd)
            arr1 = np.asarray(img2.convert("RGB"))
            after = {
                "L_row1": band_count(arr1, panes2.get("left", panes["left"]), 1, WY, WX, LEFTB),
                "L_row4": band_count(arr1, panes2.get("left", panes["left"]), 4, WY, WX, LEFTB),
                "R_row1": band_count(arr1, panes2.get("right", panes["right"]), 1, WY, WX, RIGHTB),
                "R_row4": band_count(arr1, panes2.get("right", panes["right"]), 4, WY, WX, RIGHTB),
                "OUT_row1_left": band_count(arr1, panes2.get("output", panes["output"]), 1, WY, WX, OUTL),
                "OUT_row1_right": band_count(arr1, panes2.get("output", panes["output"]), 1, WY, WX, OUTR),
            }
            if mode == "swap":
                swapped = (after["L_row4"] >= 6 and after["L_row1"] < 6 and
                           after["R_row1"] >= 6 and
                           after["OUT_row1_right"] >= 6)
                if swapped:
                    print("NEGATIVE FAILED: sides exchanged despite injection",
                          file=sys.stderr)
                    return 1
                print(f"NEGATIVE OK: bands unmoved after Swap ({after}) — caught")
                return 0
            # measured: L cyan at the R-fixture row (index 4), R purple at
            # index 1, output row1 took-right; before: L row1 / R row4 /
            # output row1 took-left
            if before["L_row1"] < 6:
                problems.append(f"[swap-pre] expected left band at row1 before swap: {before}")
            if after["L_row4"] < 6:
                problems.append(f"[swap] left pane cyan band not at row4 after swap: {after}")
            if after["L_row1"] >= 6:
                problems.append(f"[swap] left pane row1 still banded after swap: {after}")
            if after["R_row1"] < 6:
                problems.append(f"[swap] right pane purple band not at row1 after swap: {after}")
            if after["OUT_row1_right"] < 6:
                problems.append(f"[swap] output row1 not took-right after swap: {after}")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("OK: title/path follow Merge-to radio; Ctrl+S writes the picked "
              "destination (left file then OUT, sentinel intact); Swap "
              "exchanges side bands and output attribution flips "
              f"{OUTL}->{OUTR}")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
