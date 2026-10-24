#!/usr/bin/env python3
"""Live content gate for the engine-wired Text Compare pane.

Launches the PRODUCT (reacmp-gui --dispatch L R --show) — our own dotnet
process (subprocess + kill, same pattern as uia-menu-check.py; the Job Object
discipline is for the Oracle BCompare, which this check never starts).

Asserts, read from the REAL rendered window (PrintWindow pixels), against the
MEASURED colors.json (reference 5.2.6 probe) — never against a design guess:
  1. every XML status row's background tint (both panes) == colors.json tint;
  2. orphan empty-side == pane base + diagonal hatch stripe;
  3. a 'same' row stays the plain pane base (no tint) — the measured rule;
  4. the UIA control-view skeleton preorder is UNCHANGED (content overlay is
     peer-pruned; the 24-node Text Compare skeleton must still match spec).

Usage: python tools/uia-text-content-check.py <spec.json> <left> <right>
Exit 0 = all content colors + skeleton match; 1 = differences; 2 = launch fail.
"""
import ctypes
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from ctypes import wintypes
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class, get_window_text  # noqa: E402
from live_text_px import capture_window  # noqa: E402  (shared with probe)

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll"
ENGINE = r"D:\Rea\product\cli\target\release\reacmp.exe"
COLORS = r"D:\Rea\extracted\live\textcolor-en\colors.json"
# The gate EXPECTS the measured colors.json. The PRODUCT renders from
# PRODUCT_COLORS, which defaults to the same file (fidelity) but a NEGATIVE
# verification points it at a mutated copy so the product draws wrong colors
# while the gate still expects the measured ones — proving the check can fail
# (not constant-pass). If both read the same file, a mutation would make them
# agree and test nothing.
PRODUCT_COLORS = os.environ.get("REACMP_PRODUCT_COLORS", COLORS)


def find_editors(win, out):
    """UIA bounding rects of the two TTextEditor pane containers, tree order."""
    try:
        if (win.element_info.class_name or "") == "TTextEditor":
            r = win.rectangle()
            out.append((r.left, r.top, r.width(), r.height()))
            return out
        for c in win.children():
            find_editors(c, out)
    except Exception:
        pass
    return out


def skeleton_preorder(win):
    """Shared walker from uia_menu_check_lib — the D3 TextPane carve-out
    rule must be defined exactly once across all structural gates."""
    from uia_menu_check_lib import live_skeleton_preorder
    return live_skeleton_preorder(win)


def spec_skeleton(spec, view):
    acc = []

    def flat(nodes):
        for n in nodes:
            acc.append((n["ct"], n["cls"], n["name"]))
            flat(n.get("children", []))
    flat(spec["skeleton"].get(view, []))
    return acc




def main():
    spec_path, left, right = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    colors = json.load(open(COLORS, encoding="utf-8"))
    expect = colors  # gate always expects the MEASURED colors.json
    pitch = colors["geometry"]["row_pitch_px"]
    spec = json.load(open(spec_path, encoding="utf-8"))

    # ground-truth grid: re-run the engine directly (independent of the product)
    tmp = os.path.join(os.environ["TEMP"], f"tcheck-{os.getpid()}.xml")
    script = os.path.join(os.environ["TEMP"], f"tcheck-{os.getpid()}.bcscript")
    open(script, "w", encoding="utf-8").write(
        f'text-report layout:xml output-to:"{tmp}" "{left}" "{right}"\n')
    subprocess.run([ENGINE, "@" + script], check=True)
    grid = []
    for lc in ET.parse(tmp).getroot().iter("linecomp"):
        st = lc.get("status")
        l = r = None
        for tx in lc.findall("text"):
            if tx.get("ltid"):
                l = int(tx.get("ltid"))
            if tx.get("rtid"):
                r = int(tx.get("rtid"))
        grid.append((st, l, r))
    os.remove(script); os.remove(tmp)

    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    proc = subprocess.Popen(["dotnet", DLL, "--menu-spec", os.path.abspath(spec_path),
                             "--dispatch", left, right, "--engine", ENGINE,
                             "--colors", PRODUCT_COLORS, "--show"], env=env)
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
        time.sleep(1.5)
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        problems = []

        # --- gate: skeleton preorder UNCHANGED by the content overlay ---
        want = spec_skeleton(spec, "Text Compare")
        got = skeleton_preorder(win)
        if want != got:
            problems.append(f"[skeleton] spec={len(want)} live={len(got)}")
            for i, (a, b) in enumerate(zip(want, got)):
                if a != b:
                    problems.append(f"  [{i}] spec={a} live={b}")
                    break

        # --- gate: per-status row tint (PrintWindow pixels) ---
        img, (WX, WY, WW, WH) = capture_window(hwnd)
        editors = find_editors(win, [])
        if len(editors) != 2:
            problems.append(f"expected 2 TTextEditor panes, found {len(editors)}")
            print("\n".join(problems), file=sys.stderr)
            return 1
        # UIA rects are screen coords; the capture is window-relative -> subtract
        # origin. Pane identity by TREE ORDER (not geometry): BC's measured
        # tree order is RIGHT-first (gui-text-session-en.json: editor#0 x=784,
        # #1 x=86) and the product's attach slot parity is the same measured
        # order (MenuMode: slot 0 => IsLeft=(0%2==1)=false=right), so preorder
        # slot 0 = right pane, slot 1 = left pane on BOTH sides of the gate.
        def to_win(rect):
            l, t, w, h = rect
            return (l - WX, t - WY, w, h)
        editors = [to_win(e) for e in editors]
        rightPane, leftPane = editors[0], editors[1]  # measured tree order
        px = img.load()
        IW, IH = img.size

        def tint_at(pane, k):
            L, T, W, H = pane
            y0 = T + k * pitch + 4
            if y0 + 6 > T + H or y0 >= IH:
                return None
            x0 = min(L + colors["geometry"]["body_start_x"] + 3, L + W - 4, IW - 1)
            x1 = min(L + W - 4, IW - 1)
            c = Counter()
            for y in range(y0, min(y0 + 6, IH, T + H)):
                for x in range(max(0, x0), max(0, x1), 2):
                    c[px[x, y]] += 1
            return c.most_common(1)[0][0] if c else None

        def eq(a, b, tol=3):
            return a is not None and all(abs(a[i] - b[i]) <= tol for i in range(3))

        # colors.json status_rows already stores the per-side measured color,
        # including the orphan EMPTY side = pane base (hatch dots are sparse).
        checked = 0
        for status, cell in expect["status_rows"].items():
            ks = [k for k, g in enumerate(grid) if g[0] == status]
            if not ks:
                continue
            k = ks[0]
            for pane, key, side in ((leftPane, "left", "L"), (rightPane, "right", "R")):
                want_c = tuple(cell[key])
                got_c = tint_at(pane, k)
                if not eq(got_c, want_c):
                    problems.append(f"[tint {status} {side} row{k}] want={want_c} got={got_c}")
                checked += 1
        print(f"checked {checked} pane-row tints against colors.json")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"OK: content {checked} rows + skeleton {len(want)} nodes all match")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
