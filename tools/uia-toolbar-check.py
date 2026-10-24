#!/usr/bin/env python3
"""Live toolbar text-button gate (docs/21 B tier-1; self-design annotated there).

Product-side assertions on a dispatched Text Compare session:
  1. TREE — every named MainBar button is present (chrome-matrix names, 13),
     each UIA rect is the measured 39px button height inside the measured
     44px toolbar row (textlayout-en/tree-step0.json), and the full UIA
     preorder (ct,cls,name) is byte-identical to the positive run's saved
     tree (rendering must never touch the tree; the offline 845/410/290
     ledger axes are tree-only and separately green).
  2. INK — sampled buttons carry glyph pixels (dark-on-light) inside their
     rects: the text face is actually drawn, not a 2px empty shell.
  3. DARK — with --theme dark the glyph pixels are the dark.json
     "toolbar.text" ink on a dark toolbar background.

Negative (REACMP_TB_NEG=1, TEST-INJECTION ONLY): the face draws nothing while
sizes/layout stay identical — the gate MUST catch empty button rects (ink==0)
and MUST see a tree byte-identical to the positive run.

Usage: python tools/uia-toolbar-check.py <L> <R> [positive|negative|dark]
  positive saves _tmp/uia-toolbar-tree-positive.json (negative compares it)
Exit 0/1/2 like the other live gates.
"""
import ctypes
import json
import os
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
DARK = os.path.join(ROOT, "product", "gui", "themes", "dark.json")
TREE_OUT = os.path.join(ROOT, "_tmp", "uia-toolbar-tree-positive.json")

# chrome-matrix Text Compare toolbars[0] named items (MainBar) — every named
# button the tier-1 face draws. Unnamed Pane/ComboBox/path-bar items stay
# shells (annotated docs/19 §6.21).
NAMES = {"Home", "All", "Diffs", "Same", "Context", "Minor", "Rules",
         "Format", "Copy", "Next Section", "Prev Section", "Swap", "Reload"}
BTN_H = 39     # measured UIA button rect height (tree-step0)
ROW_H = 44     # measured TUiDock row height (tree-step0)
INK_LIGHT_MAX = 140   # glyph pixel = max(r,g,b) below this on the light face
INK_DARK_MIN = 150    # glyph pixel = min(r,g,b) above this on the dark face


def preorder(win):
    """[ct, cls, name] triples, preorder — the tree-identity payload."""
    out = []

    def rec(n, d=0):
        try:
            if d > 22:
                return
            ei = n.element_info
            out.append([ei.control_type or "", ei.class_name or "", ei.name or ""])
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return out


def collect(win):
    btns = {}
    dock = None

    def rec(n, d=0):
        nonlocal dock
        try:
            if d > 22:
                return
            ei = n.element_info
            cls = ei.class_name or ""
            nm = ei.name or ""
            ct = ei.control_type or ""
            if cls == "TUiDock":
                r = n.rectangle()
                dock = (r.left, r.top, r.width(), r.height())
            if ct in ("Button", "MenuItem") and nm in NAMES and nm not in btns:
                r = n.rectangle()
                btns[nm] = (r.left, r.top, r.width(), r.height())
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return btns, dock


def ink_stats(arr, rect, WX, WY, dark):
    """(count of glyph pixels, most common glyph color) inside a UIA rect."""
    x0, y0, w, h = rect
    c = Counter()
    for yy in range(y0 - WY, y0 - WY + h):
        for xx in range(x0 - WX, x0 - WX + w):
            if 0 <= yy < arr.shape[0] and 0 <= xx < arr.shape[1]:
                p = tuple(int(v) for v in arr[yy, xx, :3])
                if dark:
                    if min(p) > INK_DARK_MIN:
                        c[p] += 1
                else:
                    if max(p) < INK_LIGHT_MAX:
                        c[p] += 1
    return sum(c.values()), (c.most_common(1)[0][0] if c else None)


def launch(env, theme=None):
    args = [DLL, "--menu-spec", SPEC, "--dispatch", L, R, "--show"]
    if theme:
        args += ["--theme", theme]
    return subprocess.Popen(args, env=env)


def open_window(proc):
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
        return None
    time.sleep(2.4)
    from pywinauto import Desktop
    win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
    for _ in range(25):
        if u32.GetForegroundWindow() == hwnd:
            break
        win.set_focus()
        time.sleep(0.2)
    time.sleep(0.5)
    return hwnd, win


def main():
    global L, R
    L, R = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    mode = sys.argv[3] if len(sys.argv) > 3 else "positive"
    if mode not in ("positive", "negative", "dark"):
        print("mode must be positive|negative|dark", file=sys.stderr)
        return 2
    dark_cfg = json.load(open(DARK, encoding="utf-8"))
    ink_want = tuple(dark_cfg["toolbar"]["text"])

    env = dict(os.environ, DOTNET_NOLOGO="1",
               REACMP_TB_NEG="1" if mode == "negative" else "0")
    proc = launch(env, theme="dark" if mode == "dark" else None)
    try:
        found = open_window(proc)
        if not found:
            print("product window not found", file=sys.stderr)
            return 2
        hwnd, win = found
        img, rect = capture_window(hwnd)
        WX, WY = rect[0], rect[1]
        import numpy as np
        arr = np.asarray(img.convert("RGB"))
        tree = preorder(win)
        btns, dock = collect(win)
        problems = []

        if mode == "positive":
            json.dump(tree, open(TREE_OUT, "w", encoding="utf-8"))
        missing = NAMES - set(btns)
        if missing:
            problems.append(f"[tree] named buttons missing: {sorted(missing)}")

        # measured geometry: 39px buttons inside a 44px toolbar row
        for nm in sorted(NAMES & set(btns)):
            if abs(btns[nm][3] - BTN_H) > 1:
                problems.append(f"[geometry] {nm} height {btns[nm][3]} != {BTN_H}")
        if dock and abs(dock[3] - ROW_H) > 1:
            problems.append(f"[geometry] TUiDock height {dock[3]} != {ROW_H}")

        dark = mode == "dark"
        for nm in sorted(NAMES & set(btns)):
            n_ink, top = ink_stats(arr, btns[nm], WX, WY, dark)
            if mode == "negative":
                if n_ink != 0:
                    problems.append(f"[negative] {nm} still has {n_ink} glyph px "
                                    f"(face not disabled?)")
            else:
                if n_ink < 15:
                    problems.append(f"[ink] {nm} only {n_ink} glyph px "
                                    f"(top={top}) — text face not drawn")
            if dark and n_ink > 0 and top is not None:
                if any(abs(top[i] - ink_want[i]) > 25 for i in range(3)):
                    problems.append(f"[dark] {nm} glyph {top} != dark.json "
                                    f"toolbar.text {ink_want}")

        if mode == "negative":
            if not os.path.exists(TREE_OUT):
                problems.append("[tree] no positive tree saved — run positive first")
            else:
                want = json.load(open(TREE_OUT, encoding="utf-8"))
                if tree != want:
                    diff = next((i for i, (a, b) in enumerate(zip(want, tree)) if a != b), None)
                    problems.append(f"[tree] negative tree differs from positive "
                                    f"at index {diff}: want={want[diff] if diff is not None and diff < len(want) else '?'} "
                                    f"got={tree[diff] if diff is not None and diff < len(tree) else '?'} "
                                    f"(lens {len(want)} vs {len(tree)})")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        if mode == "negative":
            print(f"NEGATIVE OK: all {len(btns)} named buttons render EMPTY "
                  f"(ink==0) with an unchanged tree ({len(tree)} nodes) — caught")
        else:
            print(f"OK: {len(btns)}/{len(NAMES)} toolbar text buttons drawn "
                  f"(39px in 44px row, tree {len(tree)} nodes"
                  + (f", dark ink {ink_want}" if mode == "dark" else "") + ")")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
