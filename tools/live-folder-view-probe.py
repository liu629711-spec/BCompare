#!/usr/bin/env python3
"""Folder Compare view probe (docs/20 feature 3 GUI tier; engine = dir crate).

ONE script, TWO strictly serial reference-BCompare launches (Job Object,
CREATE_SUSPENDED, redirected profile, zero residue):
  BCompare.exe <Ldir> <Rdir>    (dispatch dirs -> Folder Compare view)

Fixture pair exercises every observed status: a.txt same, b.txt diff,
c.txt left-only, d.txt right-only, newer.txt timestamp-only (utime-set:
left older -> rtnewer), sub/ directory with s.txt inside (same).

Measures what statics cannot (TDirTreeView rows are runtime-drawn; 禁臆测):
  launch A (step0)   column layout (x-runs of ink per row band), row tint
                     census (status palette), status bar texts via UIA,
                     title, full UIA tree (are ROWS exposed?)
  launch B (clicked) physical click on the b.txt row -> selection tint
                     pixels + any footer/status change

Outputs -> extracted/live/folderview-en/
Usage: python tools/live-folder-view-probe.py <BCompare.exe> <outdir>
"""
import ctypes
import json
import os
import shutil
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (launch as plaunch, create_kill_job, top_windows,
                            get_class, get_window_text)  # noqa: E402
from live_text_px import capture_window  # noqa: E402

import numpy  # noqa: E402
from PIL import Image  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32


def preorder(el, out, d=0):
    try:
        ei = el.element_info
        r = el.rectangle()
        node = [ei.control_type or "", ei.class_name or "", ei.name or "",
                [r.left, r.top, r.width(), r.height()]]
        out.append(node)
        if d < 24:
            kids = []
            for c in el.children():
                preorder(c, kids, d + 1)
            out[-1].extend(kids)
    except Exception:
        pass


def make_fixture(root):
    if os.path.exists(root):
        shutil.rmtree(root)
    L = os.path.join(root, "L")
    R = os.path.join(root, "R")
    os.makedirs(os.path.join(L, "sub"))
    os.makedirs(os.path.join(R, "sub"))
    def w(base, name, content):
        p = os.path.join(base, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    # same / diff / ltonly / rtonly
    w(L, "a.txt", "alpha\n"); w(R, "a.txt", "alpha\n")
    w(L, "b.txt", "left-B\n"); w(R, "b.txt", "right-B\n")
    w(L, "c.txt", "leftonly\n")
    w(R, "d.txt", "rightonly\n")
    w(L, "newer.txt", "x\n"); w(R, "newer.txt", "x\n")
    w(L, os.path.join("sub", "s.txt"), "s\n"); w(R, os.path.join("sub", "s.txt"), "s\n")
    # timestamp-only: left older (2020), right newer (2024) -> rtnewer family
    old = 1580515200  # 2020-02-01
    new = 1706745600  # 2024-02-01
    os.utime(os.path.join(L, "newer.txt"), (old, old))
    os.utime(os.path.join(R, "newer.txt"), (new, new))
    return L, R


def run_launch(exe, outdir, tag, L, R, click=None):
    od = os.path.join(outdir, tag)
    if os.path.exists(od):
        shutil.rmtree(od)
    os.makedirs(od, exist_ok=True)
    meta = {"tag": tag, "L": L, "R": R}
    job = create_kill_job()
    si, pi = plaunch(exe, {"APPDATA": os.path.join(od, "_profile"),
                           "LOCALAPPDATA": os.path.join(od, "_profile")},
                     args=[L, R])
    try:
        h = k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)
        if not k32.AssignProcessToJobObject(job, h):
            k32.TerminateProcess(pi.hProcess, 0)
            raise ctypes.WinError()
        k32.ResumeThread(pi.hThread)
        main_h = None
        t0 = time.time()
        while time.time() - t0 < 30 and not main_h:
            for w in top_windows(pi.dwProcessId):
                if get_class(w) == "TViewForm" and u32.IsWindowVisible(w):
                    main_h = w
                    break
            time.sleep(0.5)
        if not main_h:
            meta["error"] = "no TViewForm"
            return meta
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(2.5)
        meta["title"] = get_window_text(main_h)
        tree = []
        preorder(win, tree)
        json.dump(tree, open(os.path.join(od, f"tree-{tag}.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        img, rect = capture_window(main_h)
        img.save(os.path.join(od, f"window-{tag}.png"))
        meta["window-rect"] = list(rect)

        # status bar texts
        texts = []

        def texts_of(el, d=0):
            try:
                if d > 20:
                    return
                ei = el.element_info
                if (ei.control_type or "") == "Text" and ei.name:
                    texts.append(ei.name)
                for c in el.children():
                    texts_of(c, d + 1)
            except Exception:
                pass
        texts_of(win)
        meta["uia_texts"] = [t for t in texts if t.strip()][:60]

        # list rows: find TDirTreeView, sample rows in the body
        arr = numpy.asarray(img.convert("RGB")).astype(int)
        tv = None

        def find_cls(el, cls, d=0):
            nonlocal tv
            try:
                if d > 20:
                    return
                if (el.element_info.class_name or "") == cls:
                    tv = el
                    return
                for c in el.children():
                    find_cls(c, cls, d + 1)
            except Exception:
                pass
        find_cls(win, "TDirTreeView")
        if tv is None:
            meta["error"] = "no TDirTreeView"
            return meta
        r = tv.element_info.rectangle
        meta["treeview-rect-win-rel"] = [r.left - rect[0], r.top - rect[1],
                                         r.width(), r.height()]
        # ink x-runs + per-row dominant colors for the first ~14 rows
        # the list body: below the view top; find dark-ink row bands
        x0, y0, w, h = meta["treeview-rect-win-rel"]
        sub = arr[y0:y0 + h, x0:x0 + w]
        gray = numpy.asarray(img.convert("L")).astype(int)[y0:y0 + h, x0:x0 + w]
        dark = (gray < 100).sum(axis=1)
        bands = []
        inb = False
        for y, v in enumerate(dark):
            if v > 6 and not inb:
                s = y; inb = True
            elif v <= 6 and inb:
                if y - s > 7:
                    bands.append((s, y))
                inb = False
        meta["row_bands_first12"] = bands[:12]
        meta["row_pitches"] = [bands[i + 1][0] - bands[i][0]
                               for i in range(min(6, len(bands) - 1))]
        rows = {}
        for i, (bs, be) in enumerate(bands[:14]):
            cc = Counter()
            for y in range(bs, be):
                for x in range(0, w, 2):
                    cc[tuple(int(v) for v in sub[y, x][:3])] += 1
            rows[f"row{i}"] = cc.most_common(6)
        meta["row_colors"] = rows
        # column ink profile for the first row band
        if bands:
            bs, be = bands[0]
            darkx = (gray[bs:be] < 100).sum(axis=0)
            runs = []
            inb = False
            for x, v in enumerate(darkx):
                if v > 0 and not inb:
                    s = x; inb = True
                elif v == 0 and inb:
                    runs.append([x0 + s, x0 + x]); inb = False
            meta["row0_ink_runs"] = runs

        if click:
            import pywinauto.mouse as mouse
            mouse.click(coords=click)
            time.sleep(1.2)
            img2, _ = capture_window(main_h)
            img2.save(os.path.join(od, "window-clicked.png"))
            texts2 = []
            texts_of(win)
            meta["uia_texts_after_click"] = [t for t in texts if t.strip()][:60]
        return meta
    finally:
        k32.TerminateJobObject(job, 0)
        ctypes.windll.kernel32.CloseHandle(job)
        time.sleep(0.5)
        meta["residue"] = [[get_class(w), get_window_text(w)]
                           for w in top_windows(pi.dwProcessId)
                           if u32.IsWindowVisible(w)]


def main():
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)
    root = os.path.join(outdir, "_fix")
    L, R = make_fixture(root)
    all_meta = {"A-step0": run_launch(exe, outdir, "A-step0", L, R)}
    # launch B: click the b.txt row (second row under the header) in the tree
    m = all_meta["A-step0"]
    if "treeview-rect-win-rel" in m and m.get("row_bands_first12"):
        tr = m["treeview-rect-win-rel"]
        bands = m["row_bands_first12"]
        band = bands[1] if len(bands) > 1 else bands[0]
        click = [tr[0] + 100, tr[1] + (band[0] + band[1]) // 2]
    else:
        click = None
    all_meta["B-clicked"] = run_launch(exe, outdir, "B-clicked", L, R,
                                       click=click)
    json.dump(all_meta, open(os.path.join(outdir, "folderview-meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
    for tag, m in all_meta.items():
        print("=====", tag)
        for k in sorted(m):
            if k in ("title", "error", "residue", "treeview-rect-win-rel",
                     "row_bands_first12", "row_pitches", "row0_ink_runs",
                     "uia_texts", "uia_texts_after_click"):
                print(" ", k, "=", json.dumps(m[k], ensure_ascii=False, default=str)[:500])
            elif k == "row_colors":
                v = {rk: rv[:3] for rk, rv in list(m[k].items())[:14]}
                print(" ", k, "=", json.dumps(v, ensure_ascii=False, default=str)[:1600])


if __name__ == "__main__":
    sys.exit(main())
