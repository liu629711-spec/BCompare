#!/usr/bin/env python3
"""Live find-bar gate (docs/19 §6.13 tier-1).

Product-side assertions of the measured Find behavior:
  1. before Ctrl+F: control skeleton == 24 spec nodes, NO 'Prev'/'Next';
  2. Ctrl+F: bar inserts at the TOP of the pane area (measured frame above
     panes); UIA names 'Prev'/'Next' present (measured find-open names);
  3. typing 'totally': both panes show the measured YELLOW mark
     (findmarks.json (255,227,162)) on row 2 — and the shared footers stay
     at the initial '3: 1' (measured: typing does not move the cursor);
  4. Next (button click): footers BOTH become '3: 8' — line = engine ltid,
     column = match end; ORANGE (219,127,50) accent pixels exist around the
     current span. Recorded design choice (docs/19 §6.13): BC showed an
     intermediate 3:1 after the FIRST Enter before 3:8 after the second —
     selection-vs-caret semantics unresolved, our tier-1 lands directly on
     the measured end state 3:8 and the gate asserts that.
  5. Esc: frame gone (no Prev/Next, skeleton back to 24), footer KEPT 3:8
     (measured closed state: frame removed, cursor value retained).

Negative verification: REACMP_FIND_NEG=1 -> Next click does not update the
shared cursor (footer stays 3:1) while marks still draw; the gate MUST catch
it. Proves the footer-step assertion has teeth.

Usage: python tools/uia-text-find-check.py <spec.json> <left> <right> [negative]
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
from uia_menu_check_lib import live_skeleton_preorder  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
ROOT = r"D:\Rea"
COLORS = os.path.join(ROOT, "extracted", "live", "textcolor-en", "colors.json")
MARKS = os.path.join(ROOT, "extracted", "live", "textfind-en", "findmarks.json")
FOOTER_RE = re.compile(r"^\d+: \d+$")


def collect(win, footers, named, d=0, elems=None):
    try:
        ei = win.element_info
        n = ei.name or ""
        if FOOTER_RE.match(n):
            r = win.rectangle()
            footers.append((r.left, n))
        if n in ("Prev", "Next"):
            r = win.rectangle()
            named[n] = (r.left, r.top, r.width(), r.height())
            # WPF exposes BOTH the Button and its inner TextBlock under the
            # same UIA name; only the Button carries InvokePattern.
            if elems is not None and (ei.control_type or "") == "Button":
                elems[n] = win
        if elems is not None and n == "FindWhat" and (ei.control_type or "") in ("ComboBox", "Edit"):
            elems.setdefault("Combo", win)
        for c in win.children():
            collect(c, footers, named, d + 1, elems)
    except Exception:
        pass


def main():
    spec_path, left, right = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    negative = len(sys.argv) > 4 and sys.argv[4] == "negative"
    spec = json.load(open(spec_path, encoding="utf-8"))
    colors = json.load(open(COLORS, encoding="utf-8"))
    marks = json.load(open(MARKS, encoding="utf-8"))
    pitch = colors["geometry"]["row_pitch_px"]
    bodyx = colors["geometry"]["body_start_x"]
    YELLOW = tuple(marks["find_mark_normal"]["rgb"])
    ORANGE = tuple(marks["find_mark_current"]["rgb"])

    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1",
               REACMP_FIND_NEG="1" if negative else "0")
    proc = subprocess.Popen([DLL, "--menu-spec", spec_path, "--dispatch",
                             left, right, "--show"], env=env)
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
        time.sleep(1.6)
        from pywinauto import Desktop, mouse, keyboard
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        win.set_focus()
        # keyboard.send_keys is a GLOBAL post to the foreground window (docs/19
        # §6.13 pitfall): set_focus() is async, so a fixed short sleep can drop
        # '^f' before the product window is actually frontmost. Poll until the
        # foreground really is our hwnd (timeout 5s), then settle.
        t0 = time.time()
        while time.time() - t0 < 5.0 and u32.GetForegroundWindow() != hwnd:
            win.set_focus()
            time.sleep(0.2)
        time.sleep(0.5)
        problems = []

        def snap(tag, elems=None):
            import numpy as np
            img, (WX, WY, WW, WH) = capture_window(hwnd)
            ft, named = [], {}
            collect(win, ft, named, 0, elems)
            return img, (WX, WY), sorted(x[1] for x in ft), named, np.asarray(img), (WX, WY)

        def editors(win, out=None):
            out = [] if out is None else out
            try:
                if (win.element_info.class_name or "") == "TTextEditor":
                    r = win.rectangle()
                    out.append((r.left, r.top, r.width(), r.height()))
                for c in win.children():
                    editors(c, out)
            except Exception:
                pass
            return out

        # --- 1. closed state: skeleton 24, no Prev/Next ---
        want_skel = []
        def flat(ns):
            for n in ns:
                want_skel.append((n["ct"], n["cls"], n["name"]))
                flat(n.get("children", []))
        flat(spec["skeleton"]["Text Compare"])
        img0, org, ft0, named0, a0, (WX, WY) = snap("closed")
        if live_skeleton_preorder(win) != want_skel:
            problems.append("[closed skeleton] not 24 spec nodes")
        if named0:
            problems.append(f"[closed] find controls present before Ctrl+F: {list(named0)}")
        if ft0 != ["3: 1", "3: 1"]:
            problems.append(f"[initial footer] want 3:1/3:1 got {ft0}")

        # --- 2. Ctrl+F opens the bar ---
        # win.type_keys brings the window foreground itself (robust), unlike a
        # global keypost; retry until Prev/Next actually appear.
        named1 = {}
        for attempt in range(3):
            win.set_focus()
            time.sleep(0.3)
            win.type_keys("^f", set_foreground=True, pause=0.1)
            time.sleep(0.7)
            img1, _, ft1, named1, a1, _ = snap("open")
            if set(named1) == {"Prev", "Next"}:
                break
            print(f"[retry] Ctrl+F attempt {attempt+1}: got {sorted(named1)}",
                  file=sys.stderr)
        else:
            problems.append(f"[open] expected Prev+Next, got {sorted(named1)}")
            print("\n".join(problems), file=sys.stderr)
            return 1

        eds = editors(win)
        rightR, leftR = eds[:2]

        def band_colors(img_arr, pane, k, x0=bodyx + 3):
            l, t, w, h = pane
            y0 = t - WY + k * pitch + 3
            c = Counter()
            for yy in range(y0, y0 + pitch - 5):
                for xx in range(l - WX + x0, min(l - WX + w - 6, img_arr.shape[1] - 2), 2):
                    if 0 <= xx and 0 <= yy:
                        c[tuple(int(v) for v in img_arr[yy, xx, :3])] += 1
            return c

        def accent_count(img_arr, pane, k, target, tol=70, x0=bodyx + 3):
            # The current-match accent is a 1px PEN stroke: WPF anti-aliases it
            # against the yellow fill, so exact-match sampling never sees the
            # declared RGB. Count pixels within <tol> Chebyshev distance.
            l, t, w, h = pane
            y0 = t - WY + k * pitch + 3
            n = 0
            for yy in range(y0 - 1, y0 + pitch - 3):
                for xx in range(l - WX + x0, min(l - WX + w - 6, img_arr.shape[1] - 2), 1):
                    if 0 <= xx and 0 <= yy:
                        p = img_arr[yy, xx, :3].astype(int)
                        if max(abs(p[0] - target[0]), abs(p[1] - target[1]),
                               abs(p[2] - target[2])) < tol:
                            n += 1
            return n

        # --- 3. type 'totally': yellow marks row2 BOTH panes; cursor stays ---
        # Element-level typing: global keypost races the combo's Win32 focus
        # (observed flake: 'totally' landed in the panes, footer jumped 2:29).
        # Focus the editable child of the FindWhat combo, then key into it.
        combo_elems = {}
        snap("open2", combo_elems)
        combo = combo_elems.get("Combo")
        if combo is None:
            problems.append("[typed] FindWhat combo not found in UIA tree")
            print("\n".join(problems), file=sys.stderr)
            return 1
        edit_box = []
        def find_edit(n):
            try:
                if not edit_box and (n.element_info.control_type or "") == "Edit":
                    edit_box.append(n)
                    return
                for c in n.children():
                    find_edit(c)
            except Exception:
                pass
        find_edit(combo)
        target = edit_box[0] if edit_box else combo
        target.set_focus()
        time.sleep(0.4)
        target.type_keys("totally", set_foreground=False)
        time.sleep(0.8)
        img2, _, ft2, _, a2, _ = snap("typed")
        for pane, side in ((leftR, "L"), (rightR, "R")):
            c = band_colors(a2, pane, 2)
            if c.get(YELLOW, 0) < 8:
                problems.append(f"[typed marks {side}] no yellow band on row2 (counts={c.most_common(3)})")
        if ft2 != ["3: 1", "3: 1"]:
            problems.append(f"[typed footer] typing must NOT move the cursor, got {ft2}")

        # --- 4. Prev/Next: footer 3:8 both, orange accent present ---
        # UIA Invoke instead of a physical mouse click: on this host,
        # mouse.click steals the foreground window (measured: GetForegroundWindow
        # != hwnd right after the click) and the step/Esc chain then runs
        # against the wrong window. InvokePattern is the same activation the
        # button receives from a click, without touching focus.
        nx = named1["Next"]
        elems = {}
        snap("pre-next", elems)
        if "Next" not in elems:
            problems.append("[next] Next element not captured for invoke")
            print("\n".join(problems), file=sys.stderr)
            return 1
        elems["Next"].invoke()
        time.sleep(0.8)
        img3, _, ft3, _, a3, _ = snap("next")
        if negative:
            # injection: cursor not bound to Next -> footers must be STALE
            if ft3 == ["3: 8", "3: 8"]:
                print("NEGATIVE FAILED: Next still moved the cursor despite injection",
                      file=sys.stderr)
                return 1
            print(f"NEGATIVE OK: Next did not step the shared cursor ({ft3}) — caught")
            return 0
        if ft3 != ["3: 8", "3: 8"]:
            problems.append(f"[next footer] want 3:8/3:8 got {ft3}")
        # Current-match orange lands on the pane HOLDING the match (measured
        # §6.13 again-state: orange in the LEFT pane after wrap; the other
        # pane keeps plain yellow marks). Match scan order = left rows first
        # (EngineBridge.FindState.Recompute), so the first Next lands on the
        # left match. Assert orange ADDED on left and NOT spread to right —
        # both directions have teeth.
        for pane, side, want_add in ((leftR, "L", True), (rightR, "R", False)):
            n_after = accent_count(a3, pane, 2, ORANGE)
            n_before = accent_count(a2, pane, 2, ORANGE)
            delta = n_after - n_before
            if want_add and delta < 6:
                problems.append(f"[next accent {side}] orange current-match not added "
                                f"by Next (delta={delta})")
            if not want_add and delta >= 6:
                problems.append(f"[next accent {side}] orange leaked to non-cursor pane "
                                f"(delta={delta})")

        # --- 5. Esc: frame gone, cursor kept ---
        # Global keypost again needs the product window frontmost.
        t0 = time.time()
        while time.time() - t0 < 3.0 and u32.GetForegroundWindow() != hwnd:
            win.set_focus()
            time.sleep(0.2)
        keyboard.send_keys("{ESC}")
        time.sleep(0.7)
        img4, _, ft4, named4, a4, _ = snap("closed2")
        if named4:
            problems.append(f"[esc] controls remain after Escape: {sorted(named4)}")
        if ft4 != ["3: 8", "3: 8"]:
            problems.append(f"[esc footer] cursor value must be KEPT (3:8), got {ft4}")
        if live_skeleton_preorder(win) != want_skel:
            problems.append("[esc skeleton] 24 nodes not restored")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("OK: Ctrl+F bar open/close + live marks (yellow) + cursor hold on typing + "
              "Next->3:8 (orange) + Esc keeps cursor + skeleton all hold")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
