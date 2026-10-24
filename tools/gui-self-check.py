#!/usr/bin/env python3
"""LiuCompare self-golden live gate (docs/20 §4 verification regime, item 2/3).

The OLD regime compared the product's live UIA tree against BC Oracle
snapshots (extracted/live/*). The NEW regime compares it against OUR OWN
approved baseline: extracted/golden-gui/<view>.json — recorded from the
PRODUCT's actual rendered UIA tree (not from the spec: recording the live
observation is what still catches spec->WPF->UIA translation losses, the
class of bug the RadioButton/Slider live runs historically found).

Captured per view (control-view walk, same prune rules as the Oracle gates):
  - top menu bar rows: (label, shortcut, accessKey) per top;
  - chrome rows by AutomationId "chrome:{sec}:{i}" -> (ct,cls,name) items;
  - content skeleton preorder (ct,cls,name);
  - window title.

Usage:
  python tools/gui-self-check.py <spec.json> [--view V]            # compare
  python tools/gui-self-check.py <spec.json> --record [--view V]   # (re)base
Exit 0 = all compared views match the golden; 1 = differences (red);
2 = launch/record failure. A missing golden file = red (explicit --record
first), never a silent pass.
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class, get_window_text, wintypes  # noqa: E402
# reuse the proven live readers from the Oracle checker (same walkers/rules)
from uia_menu_check_lib import (live_menu_rows, read_live_chrome,  # noqa: E402
                                live_skeleton_preorder)

GOLDEN_DIR = os.path.join(r"D:\Rea", "extracted", "golden-gui")
u32 = ctypes.windll.user32
# SHIPPING launch path: the apphost exe carries the PerMonitorV2 manifest
# (measured: exe=PER_MONITOR, `dotnet dll`=SYSTEM-aware — the dll path would
# record/gate the wrong DPI behavior). Gate the product the way it ships.
EXE = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"


def capture(spec, view, ledger_unused=None):
    """Launch the product for one view and read the live UIA facts."""
    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    proc = subprocess.Popen([EXE,
                             "--menu-spec", os.path.abspath(spec), "--view", view, "--show"],
                            env=env)
    try:
        hwnd = None
        t0 = time.time()
        while time.time() - t0 < 15:
            for w in top_windows(proc.pid):
                if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w):
                    hwnd = w
                    break
            if hwnd:
                break
            time.sleep(0.4)
        if not hwnd:
            raise RuntimeError(f"{view}: product window not found")
        time.sleep(1.2)
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        live = live_menu_rows(win) or {}
        rec = {
            "view": view,
            "title": get_window_text(hwnd),
            "tops": list(live.keys()),
            "top_rows": {m: [live[m][1], live[m][2]] for m in live},  # label, accessKey
            "chrome": read_live_chrome(win),
            "skeleton": live_skeleton_preorder(win),
        }
        # chrome/skeleton readers return tuples; JSON stores lists
        rec["chrome"] = {sec: [[list(t) for t in row] for row in rows]
                         for sec, rows in rec["chrome"].items()}
        rec["skeleton"] = [list(t) for t in rec["skeleton"]]
        return rec
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()


def compare(gold, live):
    problems = []
    for key in ("title", "tops", "top_rows", "chrome", "skeleton"):
        g, l = gold.get(key), live.get(key)
        if g != l:
            if key == "skeleton" and isinstance(g, list) and isinstance(l, list):
                problems.append(f"skeleton: golden={len(g)} live={len(l)}")
                for i, (a, b) in enumerate(zip(g, l)):
                    if a != b:
                        problems.append(f"  [{i}] golden={a} live={b}")
                        break
            elif key == "chrome":
                problems.append(f"chrome differs: golden keys={sorted(g or {})} live keys={sorted(l or {})}")
                for sec in sorted(set((g or {}).keys()) | set((l or {}).keys())):
                    if (g or {}).get(sec) != (l or {}).get(sec):
                        problems.append(f"  [{sec}] golden={len((g or {}).get(sec, []))} rows live={len((l or {}).get(sec, []))} rows")
                        break
            else:
                problems.append(f"{key}: golden={g!r} live={l!r}"[:300])
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--view")
    ap.add_argument("--record", action="store_true",
                    help="capture the product as the new golden (explicit re-base)")
    a = ap.parse_args()
    sp = json.load(open(a.spec, encoding="utf-8"))
    views = [a.view] if a.view else list(sp["top_menus_per_view"].keys())
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    fails = 0
    for v in views:
        gp = os.path.join(GOLDEN_DIR, v.replace(" ", "") + ".json")
        live = capture(a.spec, v)
        if a.record:
            json.dump(live, open(gp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"RECORDED {v}: tops={len(live['tops'])} "
                  f"chrome={sum(len(r) for rows in live['chrome'].values() for r in rows)} "
                  f"skeleton={len(live['skeleton'])}")
            continue
        if not os.path.exists(gp):
            print(f"GOLDEN MISSING {v}: run --record first", file=sys.stderr)
            fails += 1
            continue
        gold = json.load(open(gp, encoding="utf-8"))
        problems = compare(gold, live)
        if problems:
            fails += 1
            print(f"SELF-GOLDEN RED {v}:", file=sys.stderr)
            for p in problems:
                print("  " + p, file=sys.stderr)
        else:
            print(f"OK {v}: title+tops+chrome+skeleton match golden")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
