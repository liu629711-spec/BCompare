#!/usr/bin/env python3
"""Scroll-sync interaction probe v2 (docs/20 §6 step 4). The v1 wheel via
pywinauto mouse.scroll did NOT move the view (all three stage trees were
byte-identical — recorded negative). This run drives scroll the way a user
in BC actually does it: click a deep row in the LEFT pane, then keyboard
(PageDown / many Down) — the UIA footer 'N: C' text nodes (already proven
cursor-following by the v1 small-corpus click: both footers jumped to
'5: 3') give exact per-pane cursor lines, and row-signature matching on the
PNGs gives the per-pane pixel shift. Job Object, single launch, zero residue.

Usage: python tools/live-text-scroll-probe.py <BCompare.exe> <outdir> <left> <right>
"""
import ctypes
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (launch, create_kill_job, top_windows, get_class,
                            get_window_text, shutdown)  # noqa: E402
from live_text_px import capture_window  # noqa: E402

u32 = ctypes.windll.user32
FOOTER_RE = re.compile(r"^\d+: ?\d+$")


def preorder(el, out, d=0, refs=None):
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


def footers(tree):
    """all 'N: C' Text nodes in preorder, with window-relative rects
    (subtract origin later at analysis; here screen rects)"""
    return [n for ct, cls, n, rect in tree if ct == "Text" and FOOTER_RE.match(n)]


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    left, right = os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    meta = {"exe": exe, "left": left, "right": right}
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
            meta[f"footers-{tag}"] = footers(tree)
            return refs

        refs0 = snap("step0")
        mains = refs0.get("TTextEditor", [])
        if len(mains) != 2:
            meta["error"] = f"editors={len(mains)}"
            return 1
        # left pane by screen x (measured: tree order right-first)
        leftpane = min(mains, key=lambda e: e.rectangle().left)

        # 1) click a DEEP row (~y 550 rel -> row ~36) so the view MUST move
        leftpane.click_input(coords=(120, 550))
        time.sleep(1.2)
        snap("after-click-deep")

        # 2) PageDown x5 in the focused left pane (VK_NEXT = 0x22)
        def tap(vk):
            u32.keybd_event(vk, 0, 0, 0)
            u32.keybd_event(vk, 0, 2, 0)
            time.sleep(0.12)
        for _ in range(5):
            tap(0x22)  # VK_NEXT (PageDown)
        time.sleep(1.2)
        snap("after-pagedown")

        # 3) Ctrl+End: jump to document bottom (max scroll)
        u32.keybd_event(0x11, 0, 0, 0)              # VK_CONTROL down
        tap(0x23)                                    # VK_END
        u32.keybd_event(0x11, 0, 2, 0)
        time.sleep(1.2)
        snap("after-ctrlend")
        json.dump(meta, open(os.path.join(outdir, "meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        for k in ("footers-step0", "footers-after-click-deep",
                  "footers-after-pagedown", "footers-after-ctrlend"):
            print(k, meta[k])
        return 0
    finally:
        shutdown(job, pi)


if __name__ == "__main__":
    sys.exit(main())
