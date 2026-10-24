#!/usr/bin/env python3
"""Hex Compare view probe (docs/20 feature 5 GUI tier; engine M7 byte model).

ONE script, TWO strictly serial reference-BCompare launches (Job Object,
CREATE_SUSPENDED, redirected profile, zero residue):
  BCompare.exe <L.bin> <R.bin>     (dispatch .bin -> Hex Compare view)

Measures what DFM/statics cannot (THEXVIEW.dfm names LeftPanel/RightPanel but
the pane interiors are runtime-drawn custom controls; 禁臆测):
  launch A  small fixture pair (48/50 bytes: paired change at 0x08-0x0B,
            left-only tail, right-only tail) -> pane geometry (classes+rects),
            per-row tint census (diff highlight palette), column darkness
            profile (offset / hex zone / ascii zone x boundaries), status bar
            counts via UIA texts, window title
  launch B  the 600-byte golden pair (verify/hex/h-int-600-*.bin) -> scrolling
            viewport behavior (same census at top) + title

Outputs -> extracted/live/hexview-en/
Usage: python tools/live-hex-view-probe.py <BCompare.exe> <outdir>
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


def make_fixture(d, name, body):
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(bytes(body))
    return p


def fixtures_small(d):
    # 0x00..0x2F equal except 0x08..0x0B (paired change); L tail 0x30..0x33
    # left-only; R tail 0xF0..0xF1 right-only.
    L = list(range(0x00, 0x30))
    L[8:12] = [0xAA, 0xBB, 0xCC, 0xDD]
    L += [0x30, 0x31, 0x32, 0x33]
    R = list(range(0x00, 0x30))
    R[8:12] = [0x11, 0x22, 0x33, 0x44]
    R += [0xF0, 0xF1]
    return (make_fixture(d, "h-small-L.bin", L),
            make_fixture(d, "h-small-R.bin", R))


def census_panes(win, img, wr, tag, meta, od):
    """Every pane-ish element + per-row tint census inside each editor."""
    eds = []

    def find(el, d=0):
        try:
            ei = el.element_info
            cls = ei.class_name or ""
            r = ei.rectangle
            if r.width() > 100 and r.height() > 100 and (
                    "Editor" in cls or "View" in cls or "Panel" in cls or
                    "Hex" in cls):
                eds.append((cls, [r.left, r.top, r.width(), r.height()], el))
            for c in el.children():
                find(c, d + 1)
        except Exception:
            pass
    find(win)
    arr = numpy.asarray(img.convert("RGB")).astype(int)
    panes = {}
    for i, (cls, rect, el) in enumerate(eds):
        rows = {}
        pitch = 15
        for k in range(40):
            y = rect[1] - wr[1] + 30 + k * pitch + 5
            if y >= min(rect[1] - wr[1] + rect[3] - 20, arr.shape[0]):
                break
            c = Counter()
            for x in range(rect[0] - wr[0] + 10,
                           min(rect[0] - wr[0] + rect[2] - 10, arr.shape[1]), 2):
                c[tuple(int(v) for v in arr[y, x][:3])] += 1
            rows[k] = c.most_common(4)
        panes[f"pane{i}-{cls}"] = {"rect_win_rel": [rect[0] - wr[0],
                                                    rect[1] - wr[1],
                                                    rect[2], rect[3]],
                                   "rows": rows}
    meta.setdefault("panes", {})[tag] = panes


def column_profile(img, wr, tag, meta):
    """Darkness (ink) profile across x for the body band -> column boundaries."""
    arr = numpy.asarray(img.convert("L")).astype(int)
    prof = {}
    for band, (y0, y1) in (("body", (200, 360)),):
        darkness = (arr[y0:y1] < 128).sum(axis=0)
        cols = [int(x) for x in range(0, arr.shape[1]) if darkness[x] > 0]
        runs = []
        if cols:
            s = cols[0]; p = cols[0]
            for x in cols[1:]:
                if x - p > 3:
                    runs.append([s, p]); s = x
                p = x
            runs.append([s, p])
        prof[band] = {"dark_x_runs_first20": runs[:20], "n_runs": len(runs)}
    meta.setdefault("column_profile", {})[tag] = prof


def run_launch(exe, outdir, tag, files):
    od = os.path.join(outdir, tag)
    if os.path.exists(od):
        shutil.rmtree(od)
    os.makedirs(od, exist_ok=True)
    meta = {"tag": tag, "files": [os.path.basename(f) for f in files]}
    job = create_kill_job()
    si, pi = plaunch(exe, {"APPDATA": os.path.join(od, "_profile"),
                           "LOCALAPPDATA": os.path.join(od, "_profile")},
                     args=list(files))
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
        json.dump(tree, open(os.path.join(od, "tree-step0.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        img, rect = capture_window(main_h)
        img.save(os.path.join(od, "window-step0.png"))
        meta["window-rect"] = list(rect)
        wr = [rect[0], rect[1]]
        census_panes(win, img, wr, "step0", meta, od)
        column_profile(img, wr, "step0", meta)
        # status bar texts (UIA)
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
        meta["uia_texts"] = texts[:80]
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
    d = os.path.join(outdir, "_fix")
    os.makedirs(d, exist_ok=True)
    L, R = fixtures_small(d)
    all_meta = {
        "A-small": run_launch(exe, outdir, "A-small", [L, R]),
        "B-600": run_launch(exe, outdir, "B-600",
                            [os.path.abspath("verify/hex/h-int-600-L.bin"),
                             os.path.abspath("verify/hex/h-int-600-R.bin")]),
    }
    json.dump(all_meta, open(os.path.join(outdir, "hexview-meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
    for tag, m in all_meta.items():
        print("=====", tag)
        for k in sorted(m):
            v = m[k]
            if k == "uia_texts":
                v = [t for t in v if t][:30]
            elif k == "panes":
                v = {pk: {"rect": pv["rect_win_rel"],
                          "row0": pv["rows"].get("0"),
                          "row_diff_sample": pv["rows"].get("3")}
                     for pk, pv in v.get("step0", {}).items()}
            elif k == "column_profile":
                v = v.get("step0", {}).get("body")
            print(" ", k, "=", json.dumps(v, ensure_ascii=False, default=str)[:600])


if __name__ == "__main__":
    sys.exit(main())
