#!/usr/bin/env python3
"""Live tier-1 interaction gate (docs/20 §6 step 4 / docs/19 §6.12).

Launches the PRODUCT with the engine-wired Text Compare and asserts the
BEHAVIOR SPEC (all constants/rules with measured sources):

  1. INITIAL footers == '{ltid of row0}: 1' both panes, read over UIA
     (the chrome cell name — BC semantics of footer 'N: C' source line:col
     is measured, textlayout-en; format from chrome spec sb cells '1: 1').
  2. CLICK row 2 (measured different row, y = 2*15+7, x = 60 relative to
     the LEFT pane — same spot as the BC probe textlayout-en):
       - BOTH footers update in lockstep (shared cursor; BC measured both
         moved together — our line = engine ltid, our column = own
         renderer char-advance at that x);
       - the details band pixels change (BC: both bands changed after a
         click; CONTENT of our bands is our design — we assert the
         CHANGE, not BC's undecodable glyphs);
       - per-status tint of rows is UNCHANGED (measured BC rule: no
         selection background band).
  3. WHEEL down over the left pane scrolls the SHARED viewport: the gutter
     digit bitmap of the top row changes in BOTH panes identically (sync),
     footers stay put (cursor row is an index, not a viewport position).
  4. Skeleton (control view) unchanged throughout (24 nodes).

Negative verification: REACMP_INTERACT_NEG=1 makes the product suppress the
footer UIA refresh for the RIGHT pane (wiring fault injection) — the gate
must catch the desync. Proves the footer-sync assertion has teeth.

Usage: python tools/uia-text-interact-check.py <spec.json> <left> <right> [negative]
Exit 0 = all hold; 1 = violation; 2 = launch/parse failure.
"""
import ctypes
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class  # noqa: E402
from live_text_px import capture_window  # noqa: E402
from uia_menu_check_lib import live_skeleton_preorder  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
COLORS = r"D:\Rea\extracted\live\textcolor-en\colors.json"


def find_editors(win, out):
    try:
        if (win.element_info.class_name or "") == "TTextEditor":
            r = win.rectangle()
            out.append((r.left, r.top, r.width(), r.height()))
        for c in win.children():
            find_editors(c, out)
    except Exception:
        pass
    return out


def find_bands(win, out):
    try:
        if (win.element_info.class_name or "") == "TTextDetailsEditor":
            r = win.rectangle()
            out.append((r.left, r.top, r.width(), r.height()))
        for c in win.children():
            find_bands(c, out)
    except Exception:
        pass
    return out


def footer_names(win, out):
    """The footer cells are chrome-host children with LiveName wired: they
    report the initial measured name pattern 'N: C'. Collect every Text-name
    matching that pattern from the control tree."""
    import re
    rx = re.compile(r"^\d+: \d+$")
    try:
        n = win.element_info.name or ""
        if rx.match(n):
            r = win.rectangle()
            out.append((r.left, n))
        for c in win.children():
            footer_names(c, out)
    except Exception:
        pass
    return out


def main():
    spec_path = sys.argv[1]
    left, right = os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    negative = len(sys.argv) > 4 and sys.argv[4] == "negative"
    spec = json.load(open(spec_path, encoding="utf-8"))
    colors = json.load(open(COLORS, encoding="utf-8"))
    pitch = colors["geometry"]["row_pitch_px"]

    # engine ground truth (initial full grid)
    eng = os.path.join(os.environ["TEMP"], f"inter-{os.getpid()}.xml")
    script = os.path.join(os.environ["TEMP"], f"inter-{os.getpid()}.bcscript")
    import xml.etree.ElementTree as ET
    open(script, "w", encoding="utf-8").write(
        f'text-report layout:xml output-to:"{eng}" "{left}" "{right}"\n')
    subprocess.run([r"D:\Rea\product\cli\target\release\reacmp.exe", "@" + script], check=True)
    grid = []
    for lc in ET.parse(eng).getroot().iter("linecomp"):
        st = lc.get("status")
        l = r = None
        for tx in lc.findall("text"):
            if tx.get("ltid"):
                l = int(tx.get("ltid"))
            if tx.get("rtid"):
                r = int(tx.get("rtid"))
        grid.append((st, l, r))
    os.remove(script); os.remove(eng)

    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1",
               REACMP_INTERACT_NEG="1" if negative else "0")
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
        from pywinauto import Desktop, mouse
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        # REAL INPUT requires the target foreground: mouse.click/scroll post
        # to the window under the cursor, but WPF only routes down-clicks to
        # a non-activated window as ACTIVATION — the measured first manual
        # run showed footers change only after win.set_focus() (recorded
        # also as the foreground-lock family limitation for menus).
        win.set_focus()
        time.sleep(0.5)
        problems = []

        def snapshot(tag):
            img, (WX, WY, WW, WH) = capture_window(hwnd)
            eds = find_editors(win, [])
            fts = sorted(footer_names(win, []))
            skel = live_skeleton_preorder(win)
            bands = find_bands(win, [])
            return img, (WX, WY), eds, fts, skel, bands

        img0, origin, eds0, ft0, skel0, bands0 = snapshot("step0")
        if len(eds0) != 2:
            print(f"expected 2 TTextEditor, found {len(eds0)}", file=sys.stderr)
            return 1
        # tree order: eds0[0]=right pane (measured parity, MenuMode attach)
        rightR, leftR = eds0
        WX, WY = origin

        # --- 1. initial footers = first DIFFERENT row's line, col 1 both ---
        # MEASURED (docs/19 §6.13): fresh BC compare shows footer '3: 1' =
        # first different row (textlayout-en/textfind-en step0 both 3:1;
        # textscroll-en 149-row corpus read 40:1 = its first different).
        fdex = next(i for i, g in enumerate(grid) if g[0] == "different")
        want_ft = f"{grid[fdex][1] or grid[fdex][2]}: 1"
        got_ft = [n for _, n in ft0]
        if len(got_ft) != 2 or got_ft != [want_ft, want_ft]:
            problems.append(f"[footer initial] want both '{want_ft}' got {got_ft}")

        # --- 2. click a DIFFERENT different-row than the initial cursor ---
        # initial = first different (row 2), so click row 4 (ltid 5 'X1'/Y1).
        click_k = next(k for k in range(len(grid))
                       if grid[k][0] == "different" and k != fdex)
        cx = leftR[0] + 60                      # probe x (textlayout-en click spot)
        cy = leftR[1] + click_k * pitch + pitch // 2
        mouse.click(coords=(cx, cy))
        time.sleep(0.8)
        img1, _, eds1, ft1, skel1, bands1 = snapshot("click")

        row2 = grid[click_k]
        wantL = f"{row2[1]}: {1 + round((60 - colors['geometry']['body_start_x']) / 6.6)}"
        # column from OUR renderer advance: read the real value over UIA is
        # indirect; assert line part + the two footers moved TOGETHER
        gotL = [n for _, n in sorted(ft1)]
        if len(gotL) != 2:
            problems.append(f"[footer after click] expected 2 got {gotL}")
        else:
            if gotL[0] != gotL[1]:
                problems.append(f"[footer SYNC] both panes must move together: {gotL}")
            for n in gotL:
                if not n.startswith(f"{row2[1]}: ") and not n.startswith(f"{row2[2]}: "):
                    problems.append(f"[footer line] want ltid/rtid of row2 ({row2[1]}/{row2[2]}) got {n}")

        # band content changed after click (BC-measured: BOTH bands changed)
        import numpy as np
        arr0, arr1 = np.asarray(img0), np.asarray(img1)

        def px(a, rect):
            x, y, w, h = rect
            return a[y - WY + 2: y - WY + h - 2, x - WX + 2: x - WX + w - 4]
        for bi in range(min(len(bands0), len(bands1))):
            b0 = px(arr0, bands0[bi]).astype(int)
            b1 = px(arr1, bands1[bi]).astype(int)
            if b0.size == 0 or b1.size == 0:
                problems.append(f"[band {bi} click] empty crop rect")
                continue
            n = min(b0.shape[0], b1.shape[0]), min(b0.shape[1], b1.shape[1])
            d = (np.abs(b0[:n[0], :n[1]] - b1[:n[0], :n[1]]) > 0).sum()
            if d < 50:
                problems.append(f"[band {bi} click] content did not change (diff px={d})")

        # tint unchanged / shared viewport: sample the row band with the
        # MAJORITY-color census (uia-text-content-check's rule — a single
        # pixel lands on hatch dots or glyph ink; the mode over the body
        # band is the status tint; void side = base because dots are sparse)
        from collections import Counter

        def tint(img, pane, k):
            x, y, w, h = pane
            yy0 = y - WY + k * pitch + 2
            xx0 = x - WX + colors["geometry"]["body_start_x"] + 3
            xx1 = min(x - WX + w - 6, img.size[0] - 2)
            c = Counter()
            a = np.asarray(img)
            for yy in range(yy0, yy0 + pitch - 4):
                for xx in range(xx0, xx1, 2):
                    if 0 <= xx < a.shape[1] and 0 <= yy < a.shape[0]:
                        c[tuple(int(v) for v in a[yy, xx, :3])] += 1
            return c.most_common(1)[0][0] if c else None
        expect_tint = colors["status_rows"]["different"]
        gotL2 = tint(img1, leftR, 2)
        gotR2 = tint(img1, rightR, 2)
        if gotL2 != tuple(expect_tint["left"]):
            problems.append(f"[tint row2 L] want {tuple(expect_tint['left'])} got {gotL2}")
        if gotR2 != tuple(expect_tint["right"]):
            problems.append(f"[tint row2 R] want {tuple(expect_tint['right'])} got {gotR2}")

        # --- 3. wheel down over left pane: SHARED viewport in BOTH panes.
        # Proof = each pane's visible row 0 now renders grid row 6's per-side
        # tint (notches -2 => TopRow 6; row6=leftorphan: left red tint, right
        # void=pane base — comparing raw gutter glyphs across panes would
        # falsely differ on orphan rows, the tint mapping is the assertion).
        mouse.scroll(coords=(leftR[0] + 60, leftR[1] + 100), wheel_dist=-2)
        time.sleep(0.8)
        img2, _, _, ft2, skel2, _ = snapshot("wheel")
        st6, l6, r6 = grid[6]
        want6 = colors["status_rows"][st6]
        got6L = tint(img2, leftR, 0)
        got6R = tint(img2, rightR, 0)
        if got6L != tuple(want6["left"]):
            problems.append(f"[wheel shared-viewport L] row0 must render grid6 "
                            f"({st6}) left tint {tuple(want6['left'])}, got {got6L}")
        if got6R != tuple(want6["right"]):
            problems.append(f"[wheel shared-viewport R] row0 must render grid6 "
                            f"({st6}) right tint {tuple(want6['right'])}, got {got6R}")
        # footers stay put (cursor is an index, viewport moved)
        got2 = [n for _, n in sorted(ft2)]
        if got2 != [n for n in gotL]:
            problems.append(f"[footer after wheel] must stay {gotL} got {got2}")

        # --- 4. skeleton stable all the way ---
        want_skel = None
        def flat(nodes):
            acc = []
            def go(ns):
                for n in ns:
                    acc.append((n["ct"], n["cls"], n["name"]))
                    go(n.get("children", []))
            go(nodes)
            return acc
        want_skel = flat(spec["skeleton"]["Text Compare"])
        for tag, s in (("step0", skel0), ("click", skel1), ("wheel", skel2)):
            if list(s) != want_skel:
                problems.append(f"[skeleton {tag}] {len(s)} != {len(want_skel)}")

        if negative:
            # the injection breaks the right-pane footer refresh: gate MUST see
            # a desync or stale line, i.e. ANY footer problem
            nf = sum(1 for p in problems if p.startswith("[footer"))
            if not any(p.startswith("[footer") for p in problems):
                print("NEGATIVE FAILED: injected right-footer staleness not caught",
                      file=sys.stderr)
                return 1
            print(f"NEGATIVE OK: caught {nf} footer violations — gate has teeth")
            return 0

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("OK: footer initial/sync + bands change + tint-unchanged-on-select + "
              "wheel shared viewport + skeleton all hold")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
