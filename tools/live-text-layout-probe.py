#!/usr/bin/env python3
"""Live Text-Compare LAYOUT/INTERACTION probe (docs/20 §6 step 4, 第四步).

ONE reference-BCompare launch (Job Object + CREATE_SUSPENDED, strictly
serial, zero residue expected) capturing the interaction specs that static
DFM evidence cannot answer:

  step0: full UIA preorder snapshot with rects (panes/splitters/details/
         scrollbars/thumbnails/statusbars) + window PNG.
  click: click a measured 'different' row in the LEFT pane (grid geometry
         from textcolor-en/colors.json: y = top + k*15 + 7, x = left + 60)
         -> step1 snapshot + PNG: does the Details pane gain content, do
         other regions change?
  wheel: 3x WM_MOUSEWHEEL down over the left pane -> step2 snapshot + PNG:
         does the right pane scroll WITH the left (sync rule), where do
         scrollbar thumbs go?

NO pixel analysis here — offline analyze on stored PNGs/snapshots
(probe/analysis separation, same as every textcolor/filter probe).

Usage: python tools/live-text-layout-probe.py <BCompare.exe> <outdir> <left> <right>
       [--profile <dir>] [--click-row K]
Safety: kill-on-close Job Object; run STANDALONE (serial Oracle discipline).
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (launch, create_kill_job, top_windows, get_class,
                            get_window_text, shutdown)  # noqa: E402
from live_text_px import capture_window  # noqa: E402 (shared PrintWindow)

u32 = ctypes.windll.user32

WM_MOUSEWHEEL = 0x020A


def preorder(el, out, d=0, refs=None):
    """(ct, cls, name, rect) preorder over the FULL UIA tree (raw view is
    what matters here: the details editor content exposure question).
    refs: optional dict cls -> [element] collected DURING the same walk —
    a second full-tree scan right after a heavy one hit transient UIA
    exceptions and silently returned nothing (measured on the first run)."""
    if d > 24:
        return out
    try:
        ei = el.element_info
        r = el.rectangle()
        cls = ei.class_name or ""
        out.append([ei.control_type or "", cls, ei.name or "",
                    [r.left, r.top, r.width(), r.height()]])
        if refs is not None and cls:
            refs.setdefault(cls, []).append(el)
        for c in el.children():
            preorder(c, out, d + 1, refs)
    except Exception:
        pass
    return out


def find_by_class(root, cls, out):
    try:
        if (root.element_info.class_name or "") == cls:
            out.append(root)
        for c in root.children():
            find_by_class(c, out)
    except Exception:
        pass
    return out


def scroll_at(win, x, y, clicks):
    """Scroll down over screen point (x, y): prefer real wheel input
    (pywinauto mouse.scroll — routes exactly like a user); fall back to
    PostMessageW(WM_MOUSEWHEEL) if the OS foreground lock rejects cursor
    moves (recorded limitation for menu probes)."""
    try:
        from pywinauto import mouse
        mouse.scroll(coords=(x, y), wheel_dist=-clicks)
        return "pywinauto"
    except Exception:
        hwnd = u32.WindowFromPoint(wintypes.POINT(x, y))
        delta = (-120 * clicks) & 0xFFFFFFFF
        u32.PostMessageW(hwnd, WM_MOUSEWHEEL, (delta << 16) & 0xFFFFFFFF, 0)
        return "postmessage"


def bar_values(refs):
    """RangeValue of every TUiScrollBar (vertical thumbs) — the direct
    scroll-sync measurement; geometry alone can't show thumb position.
    Reads the refs collected by the SAME preorder walk (no rescan: a
    second full scan right after a heavy one hits transient UIA failures)."""
    out = {}
    for i, b in enumerate(refs.get("TUiScrollBar", [])):
        try:
            r = b.rectangle()
            rec = {"rect": [r.left, r.top, r.width(), r.height()]}
        except Exception:
            rec = {"rect": None}
        try:
            rec["value"] = b.iface_range_value.get_Value()
        except Exception:
            rec["value"] = None
        out[f"bar{i}"] = rec
    return out


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    left, right = os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
    prof = None
    if "--profile" in sys.argv:
        prof = os.path.abspath(sys.argv[sys.argv.index("--profile") + 1])
    if prof is None:
        prof = os.path.join(outdir, "_profile")
    click_row = 2  # colors.json: status_rows.different.grid_row = 2
    if "--click-row" in sys.argv:
        click_row = int(sys.argv[sys.argv.index("--click-row") + 1])
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    meta = {"exe": exe, "left": left, "right": right, "profile": prof,
            "click_row": click_row}
    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof}, args=[left, right])
    try:
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)
        if not k32.AssignProcessToJobObject(job, h):
            k32.TerminateProcess(pi.hProcess, 0)
            raise ctypes.WinError()
        k32.ResumeThread(pi.hThread)
        main_h = None
        t0 = time.time()
        while time.time() - t0 < 25 and not main_h:
            for w in top_windows(pi.dwProcessId):
                if get_class(w) == "TViewForm" and u32.IsWindowVisible(w):
                    main_h = w
                    break
            time.sleep(0.5)
        if not main_h:
            meta["error"] = "no visible TViewForm within 25s"
            print(json.dumps(meta, ensure_ascii=False))
            return 1

        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(1.5)
        meta["title"] = get_window_text(main_h)

        def snap(tag, refs=None):
            tree = preorder(win, [], 0, refs)
            json.dump(tree, open(os.path.join(outdir, f"tree-{tag}.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=1)
            img, rect = capture_window(main_h)
            img.save(os.path.join(outdir, f"window-{tag}.png"))
            meta[f"rect-{tag}"] = list(rect)
            return img, rect

        refs0 = {}
        img0, rect0 = snap("step0", refs0)
        wx, wy = rect0[0], rect0[1]
        meta["bars-step0"] = bar_values(refs0)

        # locate the LEFT main editor by SCREEN GEOMETRY (tree order is
        # right-first per gui-text-session-en: editor#0 x=784 — do not trust
        # comment-order; x-min decides). TTextDetailsEditor is a distinct
        # class so the "TTextEditor" key is already the two main panes.
        mains = refs0.get("TTextEditor", [])
        details = refs0.get("TTextDetailsEditor", [])
        rects = {}
        for i, e in enumerate(mains):
            r = e.rectangle()
            rects[f"editor{i}"] = [r.left, r.top, r.width(), r.height()]
        for i, e in enumerate(details):
            r = e.rectangle()
            rects[f"details{i}"] = [r.left, r.top, r.width(), r.height()]
        meta["main_editors"] = rects
        if len(mains) != 2:
            meta["error"] = f"expected 2 TTextEditor, found {len(mains)}"
            json.dump(meta, open(os.path.join(outdir, "meta.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=1)
            return 1

        leftpane = min(mains[:2] if len(mains) >= 2 else mains,
                       key=lambda e: e.rectangle().left)
        lr = leftpane.rectangle()
        # measured grid (colors.json): row k center y = top + k*15 + 7,
        # body x offset 60 (well past gutter 41 and text start 42)
        px, py = lr.left + 60, lr.top + click_row * 15 + 7
        meta["click_point_windowrel"] = [px - wx, py - wy]
        leftpane.click_input(coords=(60, click_row * 15 + 7))
        time.sleep(1.2)
        refs1 = {}
        img1, _ = snap("after-click", refs1)
        meta["bars-step1"] = bar_values(refs1)

        # wheel down over the same spot: sync-scroll + thumb positions.
        # --scroll-only K: skip the row click, wheel K notches at center-top
        # (tall-corpus run: the only question is the L/R scroll coupling).
        px, py = lr.left + 60, lr.top + click_row * 15 + 7
        if not os.environ.get("LAYOUT_SCROLL_ONLY"):
            meta["wheel_via"] = scroll_at(win, px, py, 3)
            time.sleep(1.2)
            refs2 = {}
            snap("after-wheel", refs2)
            meta["bars-step2"] = bar_values(refs2)
        else:
            k = int(os.environ["LAYOUT_SCROLL_ONLY"])
            px, py = lr.left + 60, lr.top + 100
            meta["wheel_via"] = scroll_at(win, px, py, k)
            time.sleep(1.5)
            refs2 = {}
            snap("after-wheel", refs2)
            meta["bars-step2"] = bar_values(refs2)
            # wheel UP to top: does coupling hold both directions?
            meta["wheel2_via"] = scroll_at(win, px, py, -k)
            time.sleep(1.5)
            refs3 = {}
            snap("after-wheel-up", refs3)
            meta["bars-step3"] = bar_values(refs3)

        json.dump(meta, open(os.path.join(outdir, "meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: v for k, v in meta.items() if k != "profile"},
                         ensure_ascii=False, indent=1))
        return 0
    finally:
        shutdown(job, pi)


if __name__ == "__main__":
    sys.exit(main())
