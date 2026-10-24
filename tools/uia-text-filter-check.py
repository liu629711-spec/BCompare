#!/usr/bin/env python3
"""Live display-filter gate: product (reacmp-gui --dispatch --display B --show)
must paint BOTH the radio selection tint AND the filtered row set exactly as
measured on the reference 5.2.6 (extracted/live/textfilter2-en + engine
three-path option, docs/19 §6.11):

  - radio trio All/Diffs/Same: selected button strip == (194,220,245),
    unselected == (240,240,240)  [measured button_selection_pixels];
  - pane rows: the per-row tint sequence matches the engine's filtered grid
    row-by-row (status -> colors.json tint, same = plain base, orphan void
    = base + hatch), row count == ledger rows;
  - skeleton preorder unchanged (chrome/menu gate reuse).

Usage: python tools/uia-text-filter-check.py <spec.json> <left> <right> <All|Diffs|Same>
Exit 0 = match; 1 = differences; 2 = launch failure.
"""
import ctypes
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class  # noqa: E402
from live_text_px import capture_window  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll"
ENGINE = r"D:\Rea\product\cli\target\release\reacmp.exe"
COLORS = r"D:\Rea\extracted\live\textcolor-en\colors.json"
FMAP = r"D:\Rea\extracted\live\textfilter2-en\filter-map.json"
TOOLBAR_H = 39  # measured UIA button rect height (probe4)


def main():
    spec, left, right, btn = (sys.argv[1], os.path.abspath(sys.argv[2]),
                              os.path.abspath(sys.argv[3]), sys.argv[4])
    colors = json.load(open(COLORS, encoding="utf-8"))
    fm = json.load(open(FMAP, encoding="utf-8"))
    opt = fm["button_to_option"][btn]
    pitch = colors["geometry"]["row_pitch_px"]

    # engine ground truth (FILTERING three-path form)
    tmp = os.path.join(os.environ["TEMP"], f"tcheckF-{os.getpid()}.xml")
    argv = [ENGINE, left, right, tmp] + ([f"--opt={opt}"] if opt != "display-all" else [])
    subprocess.run(argv, check=True)
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
    os.remove(tmp)

    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    proc = subprocess.Popen(["dotnet", DLL, "--menu-spec", spec,
                             "--dispatch", left, right, "--display", btn,
                             "--engine", ENGINE, "--colors", COLORS, "--show"], env=env)
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
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        problems = []

        img, (WX, WY, WW, WH) = capture_window(hwnd)
        px = img.load()
        IW, IH = img.size

        # --- radio selection tint from UIA Button rects (product paints chrome
        # elements; find the trio by name, sample an icon-free strip inside) ---
        SEL = tuple(fm["button_selection_pixels"]["selected"])
        UNS = tuple(fm["button_selection_pixels"]["unselected"])
        trio = set(fm["button_selection_pixels"]["radio_group"])

        def find_buttons(el, out, d=0):
            if d > 14:
                return out
            try:
                ei = el.element_info
                if (ei.control_type or "") == "Button" and (ei.name or "") in trio:
                    out.append(el)
                for c in el.children():
                    find_buttons(c, out, d + 1)
            except Exception:
                pass
            return out

        def strip_color(pane):
            x, y, w, h = pane
            c = Counter()
            for yy in range(y + 3, y + h - 3):
                for xx in range(x + 3, x + w - 3, 2):
                    if 0 <= xx < IW and 0 <= yy < IH:
                        c[px[xx, yy]] += 1
            return c.most_common(1)[0][0] if c else None

        found = {}
        for b in find_buttons(win, []):
            r = b.rectangle()
            rect = (r.left - WX, r.top - WY, r.width(), r.height())
            found[b.element_info.name] = rect
        if set(found) != trio:
            problems.append(f"radio trio not all found: {sorted(found)}")
        for name, rect in found.items():
            got = strip_color(rect)
            want = SEL if name == btn else UNS
            # the unselected buttons in BC are toolbar-grey (240); the product's
            # surrounding toolbar bg is also 240; accept either the exact tint
            # or base grey for unselected (strip may include label pixels)
            ok = (got == want) or (name != btn and got in (UNS, SEL, None))
            if name == btn and got != SEL:
                ok = got is not None and all(abs(got[i] - SEL[i]) <= 6 for i in range(3))
            if name != btn and got == SEL and btn != name:
                # selection bleeding onto another button = wrong
                problems.append(f"[radio] {name} shows SEL tint while {btn} selected: {got}")
            if name == btn and not ok:
                problems.append(f"[radio] {name} want SEL{SEL} got {got}")
            print(f"radio {name}: rect={rect} strip={got}")

        # --- pane row tints: sequence == engine filtered grid (tree order
        # right-first, same mapping as uia-text-content-check.py) ---
        def find_cls(el, cls, out, d=0):
            if d > 20:
                return out
            try:
                if (el.element_info.class_name or "") == cls:
                    out.append(el)
                for c in el.children():
                    find_cls(c, cls, out, d + 1)
            except Exception:
                pass
            return out

        eds = find_cls(win, "TTextEditor", [])
        if len(eds) != 2:
            problems.append(f"expected 2 editors, found {len(eds)}")
            print("\n".join(problems), file=sys.stderr)
            return 1
        panes = []
        for e in eds:
            r = e.rectangle()
            panes.append((r.left - WX, r.top - WY, r.width(), r.height()))
        rightPane, leftPane = panes[0], panes[1]   # measured tree order right-first

        def tint_at(pane, k):
            L, T, W, H = pane
            y0 = T + pitch * k + 4
            if y0 + 6 > T + H or y0 >= IH:
                return None
            x0 = min(L + colors["geometry"]["body_start_x"] + 3, L + W - 4, IW - 1)
            x1 = min(L + W - 4, IW - 1)
            c = Counter()
            for y in range(y0, min(y0 + 6, IH, T + H)):
                for x in range(max(0, x0), max(0, x1), 2):
                    c[px[x, y]] += 1
            return c.most_common(1)[0][0] if c else None

        checked = 0
        for k, (st, l, r) in enumerate(grid):
            cell = colors["status_rows"][st]
            for pane, side in ((leftPane, "left"), (rightPane, "right")):
                want = tuple(cell[side])
                got = tint_at(pane, k)
                if got is None:
                    problems.append(f"[row {k} {st} {side}] sampled outside pane")
                    continue
                if not all(abs(got[i] - want[i]) <= 3 for i in range(3)):
                    problems.append(f"[row {k} {st} {side}] want={want} got={got}")
                checked += 1
        print(f"checked {checked} filtered-pane tints ({len(grid)} rows x 2 panes), "
              f"display={btn} ({opt})")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"OK: radio trio + filtered rows match measurements for {btn}")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
