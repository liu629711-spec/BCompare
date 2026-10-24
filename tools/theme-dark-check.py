#!/usr/bin/env python3
"""Live dark-theme gate (docs/20 D5, §6 step 3).

Launches the PRODUCT with --theme dark and asserts, from REAL PrintWindow
pixels, that the rendered palette equals the OWN DESIGN declared in
product/gui/themes/dark.json — the same check shape the measured tint/filter
gates use for light, but the expectation source flips from the BC probe to
our approved design file (dark is presentation-axis: no Oracle number to
match; the gate's teeth are the design file + negative verification).

Geometry is NOT themed (dark.json rule): pitch/gutter/body_x still come
from the measured extracted/live/textcolor-en/colors.json.

Negative verification (same discipline as REACMP_PRODUCT_COLORS for the
light tint gate): point the PRODUCT at a mutated theme copy via
REACMP_PRODUCT_THEME while the gate keeps expecting dark.json values —
the gate must go red, proving it is not a tautological pass.

Usage: python tools/theme-dark-check.py [negative]
Exit 0 = all match; 1 = differences; 2 = launch failure.
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
ROOT = r"D:\Rea"
COLORS = os.path.join(ROOT, "extracted", "live", "textcolor-en", "colors.json")
DARK = os.path.join(ROOT, "product", "gui", "themes", "dark.json")
LEFT = os.path.join(ROOT, "tools", "textcolor", "content-left.txt")
RIGHT = os.path.join(ROOT, "tools", "textcolor", "content-right.txt")
SPEC = os.path.join(ROOT, "extracted", "_scratch", "menu-spec.json")
FMAP = os.path.join(ROOT, "extracted", "live", "textfilter2-en", "filter-map.json")


def main():
    negative = len(sys.argv) > 1 and sys.argv[1] == "negative"
    colors = json.load(open(COLORS, encoding="utf-8"))
    dark = json.load(open(DARK, encoding="utf-8"))
    fm = json.load(open(FMAP, encoding="utf-8"))
    pitch = colors["geometry"]["row_pitch_px"]

    # product theme: default dark.json; negative run points the PRODUCT at a
    # mutated copy (gate expectations never change — they read dark.json)
    theme_arg = DARK
    if negative:
        mut = json.loads(json.dumps(dark))
        mut["status_rows"]["different"]["left"] = [200, 0, 0]      # wrong red
        mut["radio"]["selected"] = [0, 120, 255]                    # wrong blue
        theme_arg = os.path.join(os.environ["TEMP"], f"dark-mutated-{os.getpid()}.json")
        json.dump(mut, open(theme_arg, "w", encoding="utf-8"))

    # engine ground-truth grid (independent of the product)
    tmp = os.path.join(os.environ["TEMP"], f"darkchk-{os.getpid()}.xml")
    script = os.path.join(os.environ["TEMP"], f"darkchk-{os.getpid()}.bcscript")
    open(script, "w", encoding="utf-8").write(
        f'text-report layout:xml output-to:"{tmp}" "{LEFT}" "{RIGHT}"\n')
    subprocess.run([ENGINE, "@" + script], check=True)
    grid = [lc.get("status") for lc in ET.parse(tmp).getroot().iter("linecomp")]
    os.remove(script); os.remove(tmp)

    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    proc = subprocess.Popen(["dotnet", DLL, "--menu-spec", SPEC,
                             "--dispatch", LEFT, RIGHT, "--engine", ENGINE,
                             "--theme", theme_arg, "--show"], env=env)
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

        img, (WX, WY, WW, WH) = capture_window(hwnd)
        px = img.load()
        IW, IH = img.size

        def find_editors(el, out, d=0):
            if d > 20:
                return out
            try:
                if (el.element_info.class_name or "") == "TTextEditor":
                    r = el.rectangle()
                    out.append((r.left - WX, r.top - WY, r.width(), r.height()))
                    return out
                for c in el.children():
                    find_editors(c, out, d + 1)
            except Exception:
                pass
            return out

        editors = find_editors(win, [])
        if len(editors) != 2:
            print(f"expected 2 TTextEditor panes, found {len(editors)}", file=sys.stderr)
            return 1
        rightPane, leftPane = editors  # measured tree order: slot0 = screen right

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

        # 1) per-status row tints vs dark.json (both sides, every status present)
        checked = 0
        for status, cell in dark["status_rows"].items():
            ks = [k for k, g in enumerate(grid) if g == status]
            if not ks:
                continue
            k = ks[0]
            for pane, key, side in ((leftPane, "left", "L"), (rightPane, "right", "R")):
                want = tuple(cell[key])
                got = tint_at(pane, k)
                if not eq(got, want):
                    problems.append(f"[tint {status} {side} row{k}] want={want} got={got}")
                checked += 1

        # 2) gutter band (theme-gated, dark.json gutter.bg)
        for pane, side in ((leftPane, "L"), (rightPane, "R")):
            L, T, W, H = pane
            gx = max(2, L + (colors["geometry"]["gutter_x"] - 4) // 2)
            c = Counter()
            for y in range(T + 2, min(T + 40, IH, T + H)):
                if 0 <= gx < IW:
                    c[px[gx, y]] += 1
            got = c.most_common(1)[0][0] if c else None
            if not eq(got, tuple(dark["gutter"]["bg"])):
                problems.append(f"[gutter {side}] want={tuple(dark['gutter']['bg'])} got={got}")

        # 3) radio trio fills vs dark.json radio (selected=initial All)
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

        found = {}
        for b in find_buttons(win, []):
            r = b.rectangle()
            found[b.element_info.name] = (r.left - WX, r.top - WY, r.width(), r.height())
        if set(found) != trio:
            problems.append(f"radio trio not all found: {sorted(found)}")

        def strip_color(pane):
            x, y, w, h = pane
            c = Counter()
            for yy in range(y + 3, y + h - 3):
                for xx in range(x + 3, x + w - 3, 2):
                    if 0 <= xx < IW and 0 <= yy < IH:
                        c[px[xx, yy]] += 1
            return c.most_common(1)[0][0] if c else None

        for name, rect in found.items():
            want = tuple(dark["radio"]["selected"]) if name == "All" \
                else tuple(dark["radio"]["unselected"])
            got = strip_color(rect)
            if not eq(got, want):
                problems.append(f"[radio {name}] want={want} got={got}")

        mode = "NEGATIVE" if negative else "POSITIVE"
        if negative:
            # the gate MUST find violations against the mutated product render
            if problems:
                print(f"{mode}: red as designed ({len(problems)} violations caught, "
                      f"tint {checked} rows checked) — gate has teeth")
                return 0
            print("NEGATIVE VERIFICATION FAILED: mutated product palette was not "
                  "caught — gate would constant-pass", file=sys.stderr)
            return 1

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"OK: dark theme {checked} tints + gutter + radio trio all match dark.json")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()
        if negative and os.path.exists(theme_arg):
            os.remove(theme_arg)


if __name__ == "__main__":
    sys.exit(main())
