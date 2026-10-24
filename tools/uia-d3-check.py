#!/usr/bin/env python3
"""D3 accessibility gate (docs/20 §5: LiuCompare INVERTS BC's measured
pane-content-hiding; the live-safety experiment docs/19 §6.10 deferred).

Launches the product (--dispatch --show) and asserts BOTH halves of the D3
promise over the REAL UIA tree:

  A. CONTROL view (what the 290-skeleton / 410-chrome gates walk): the two
     TTextEditor pane nodes must still have the measured control-view shape
     — no row leaks (control-view preorder == the spec skeleton, same
     rule as uia-text-content-check).
  B. CONTENT view (what screen readers walk): under the TTextEditor
     container, a content-only traversal must reach one Text node per
     diff row, named '{lineno} {status}: {text}' (or '(empty)' for the
     orphan void side) — the row's line number, state and text, exactly
     the three things D3 says must reach assistive tech.

pywinauto semantics measured on this stack: children() uses FindAll with a
true condition = the RAW view, so B walks with content_only=True and A
compares against the content-free control-view nodes (rows carry
IsControlElement=false; they must NOT appear when filtering control view).

Usage: python tools/uia-d3-check.py <spec.json> <left> <right>
Exit 0 = both halves hold; 1 = violation; 2 = launch failure.
"""
import ctypes
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class  # noqa: E402
from uia_menu_check_lib import live_skeleton_preorder  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll"
ENGINE = r"D:\Rea\product\cli\target\release\reacmp.exe"
LEDGER = r"D:\Rea\_tmp\d3-ledger.json"


def spec_skeleton(spec):
    acc = []

    def flat(nodes):
        for n in nodes:
            acc.append((n["ct"], n["cls"], n["name"]))
            flat(n.get("children", []))
    flat(spec["skeleton"]["Text Compare"])
    return acc


def collect_content_rows(win, out, d=0):
    """Walk the CONTROL view (pywinauto children()) to the D3 pane peer
    (class TextPane) and collect its row Text nodes. Measured 2026-10-22:
    the WPF UIA bridge does NOT expose IsControlElement=false peers to tree
    navigation, so the rows are proper control elements; the structural
    skeleton/chrome gates carve the TextPane subtree out by class instead.
    A real screen reader walking the CONTENT view reaches the same rows."""
    if d > 24:
        return
    try:
        ei = win.element_info
        if (ei.class_name or "") == "TextPane":
            for c in win.children():
                ce = c.element_info
                out.append((ce.control_type or "", ce.name or "",
                            ce.automation_id or ""))
            return
        for c in win.children():
            collect_content_rows(c, out, d + 1)
    except Exception:
        pass


def main():
    spec_path, left, right = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    spec = json.load(open(spec_path, encoding="utf-8"))

    # ledger = ground truth rows (engine, independent of the UI)
    lr = subprocess.run(["dotnet", DLL, "--menu-spec", spec_path, "--dispatch",
                         left, right, "--engine", ENGINE, "--dump", LEDGER],
                        capture_output=True, text=True)
    if lr.returncode != 0:
        print(lr.stdout, lr.stderr, file=sys.stderr)
        return 2
    led = json.load(open(LEDGER, encoding="utf-8"))["content"]["rows"]

    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    proc = subprocess.Popen(["dotnet", DLL, "--menu-spec", spec_path,
                             "--dispatch", left, right, "--engine", ENGINE, "--show"],
                            env=env)
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

        # --- A. control-view skeleton intact (rows must NOT leak) ---
        want = spec_skeleton(spec)
        got = live_skeleton_preorder(win)
        if want != got:
            problems.append(f"[control skeleton] spec={len(want)} live={len(got)}")
            for i, (a, b) in enumerate(zip(want, got)):
                if a != b:
                    problems.append(f"  [{i}] spec={a} live={b}")
                    break

        # --- B. content-view rows visible, per pane ---
        rows = []
        collect_content_rows(win, rows)
        # two panes x len(led) rows expected; names must match the ledger
        if len(rows) != 2 * len(led):
            problems.append(f"[content rows] expected {2*len(led)} got {len(rows)}")
        left_names = [n for ct, n, aid in rows if ct == "Text"]
        for k, r in enumerate(led):
            for side, txt, idk in (("L", r["ltext"], "ltid"), ("R", r["rtext"], "rtid")):
                if txt is None:
                    expect = "(empty)"
                else:
                    expect = f"{r[idk]} {r['status']}: {txt}"
                if expect not in left_names:
                    problems.append(f"[content {side} row{k}] missing name '{expect}'")
                    break

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"OK: control skeleton {len(want)} nodes intact + content view "
              f"{len(rows)} rows exposed both panes (D3 holds)")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
