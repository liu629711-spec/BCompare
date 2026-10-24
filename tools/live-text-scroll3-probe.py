#!/usr/bin/env python3
"""Scroll-sync probe v3: drive scrolling by CLICKING THE VERTICAL SCROLLBAR
LINE-BUTTONS via UIA (measured names '上一行'/'下一行'; rects from the
textscroll-en step0 tree: left down-line [762,772], right down-line [1456,709])
— the deterministic scroll channel (v2 keyboard events did NOT reach the
panes: footer stayed put, content unshifted — a recorded negative).

Clicks the LEFT pane's '下一行' 5 times -> snapshot; then the RIGHT pane's
'下一行' 5 times -> snapshot. Per-pane pixel shift + footer text gives the
coupling rule (does the opposite pane follow? by how many rows/px?).

Usage: python tools/live-text-scroll3-probe.py <BCompare.exe> <outdir> <left> <right>
Safety: Job Object kill-on-close, single launch, serial, zero residue expected.
"""
import ctypes
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (launch, create_kill_job, top_windows, get_class,
                            shutdown)  # noqa: E402
from live_text_px import capture_window  # noqa: E402

FOOTER_RE = re.compile(r"^\d+: ?\d+$")


def preorder(el, out, d=0, refs=None):
    if d > 24:
        return out
    try:
        ei = el.element_info
        r = el.rectangle()
        cls = ei.class_name or ""
        name = ei.name or ""
        out.append([ei.control_type or "", cls, name,
                    [r.left, r.top, r.width(), r.height()]])
        if refs is not None:
            refs.setdefault(name, []).append(el)
        for c in el.children():
            preorder(c, out, d + 1, refs)
    except Exception:
        pass
    return out


def main():
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    left, right = os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    meta = {"exe": exe}
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
                if get_class(w) == "TViewForm" and ctypes.windll.user32.IsWindowVisible(w):
                    main_h = w
                    break
            time.sleep(0.5)
        if not main_h:
            meta["error"] = "no TViewForm"
            print(json.dumps(meta))
            return 1
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(1.5)

        def snap(tag):
            refs = {}
            tree = preorder(win, [], 0, refs)
            json.dump(tree, open(os.path.join(outdir, f"tree-{tag}.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=1)
            img, rect = capture_window(main_h)
            img.save(os.path.join(outdir, f"window-{tag}.png"))
            meta[f"rect-{tag}"] = list(rect)
            meta[f"footers-{tag}"] = [[n, r] for _, _, n, r in tree
                                      if FOOTER_RE.match(n)]
            return refs, tree

        refs0, _ = snap("step0")
        downs = refs0.get("下一行", [])
        leftbtn = rightbtn = None
        for b in downs:
            x = b.rectangle().left
            if x < 900:
                leftbtn = b
            else:
                rightbtn = b
        if not leftbtn or not rightbtn:
            meta["error"] = f"down-line buttons not both found: {len(downs)}"
            print(json.dumps(meta, ensure_ascii=False))
            return 1
        meta["left_down_x"], meta["right_down_x"] = (
            leftbtn.rectangle().left, rightbtn.rectangle().left)

        for _ in range(5):
            leftbtn.click_input()
            time.sleep(0.45)
        time.sleep(1.0)
        refs1, _ = snap("after-left-5")

        for _ in range(5):
            rightbtn.click_input()
            time.sleep(0.45)
        time.sleep(1.0)
        snap("after-right-5")

        json.dump(meta, open(os.path.join(outdir, "meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        for k in ("footers-step0", "footers-after-left-5", "footers-after-right-5"):
            print(k, meta.get(k))
        return 0
    finally:
        shutdown(job, pi)


if __name__ == "__main__":
    sys.exit(main())
