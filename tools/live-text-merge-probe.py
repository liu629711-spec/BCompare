#!/usr/bin/env python3
"""Live Text Merge probe (docs/20 §6 step 4 — merge channel recon).

ONE reference-BCompare launch (Job Object, CREATE_SUSPENDED, strictly serial,
zero residue expected). Command form from help/command_line_reference.html:
  BCompare.exe <Left> <Right> <Center>     (3 files -> Text Merge view)

Captures what the static DFM cannot answer:
  step0        merge view opened on our fixture (L edits line2, R edits
               line5, C=base unchanged)
  row-tint     per-grid-row MODE color census inside each TTextEditor body
               (the merge status palette: auto-left / auto-right / conflict /
               equal bands) — pixel-only, BC exposes nothing via UIA here
  + full UIA preorder trees + window screenshots per step

Outputs -> extracted/live/textmerge-en/
Usage: python tools/live-text-merge-probe.py <BCompare.exe> <outdir> <L> <R> <C>
"""
import ctypes
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (launch, create_kill_job, top_windows, get_class)  # noqa: E402
from live_text_px import capture_window  # noqa: E402

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


def find_editors(el, out, d=0):
    try:
        if d > 24:
            return
        if (el.element_info.class_name or "") == "TTextEditor":
            out.append(el)
            return  # do not descend into pane internals for the census list
        for c in el.children():
            find_editors(c, out, d + 1)
    except Exception:
        pass


def main():
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    L, R, C = (os.path.abspath(sys.argv[i]) for i in (3, 4, 5))
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    meta = {"exe": exe, "L": L, "R": R, "C": C}
    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof}, args=[L, R, C])
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
            print(json.dumps(meta))
            return 1
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(2.0)

        def snap(tag):
            tree = []
            preorder(win, tree)
            json.dump(tree, open(os.path.join(outdir, f"tree-{tag}.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=1)
            img, rect = capture_window(main_h)
            img.save(os.path.join(outdir, f"window-{tag}.png"))
            meta["rect-" + tag] = list(rect)
            return img, tree

        img, tree = snap("step0")
        meta["title"] = u32.GetWindowTextW(main_h)

        # row tint census: every TTextEditor, sample body rows
        arr = __import__("numpy").asarray(img.convert("RGB"))
        WR = meta["rect-step0"]
        eds = []
        find_editors(win, eds)
        meta["n_editors"] = len(eds)
        pitches = [15]
        # measure pitch empirically: find the dominant row period later if needed
        census = {}
        for idx, ed in enumerate(eds):
            r = ed.rectangle()
            # skip the top sub-toolbar (~25px) and bottom footer (~17px):
            # body starts a few px under the editor top
            x0 = r.left - WR[0] + 46
            y_top = r.top - WR[1] + 30
            h = r.height() - 50
            w = r.width() - 52
            bands = {}
            for k in range(30):
                y = y_top + k * 15 + 5
                if y >= y_top + h or y >= arr.shape[0]:
                    break
                c = Counter()
                for x in range(x0, min(x0 + w, arr.shape[1] - 2), 2):
                    c[tuple(int(v) for v in arr[y, x][:3])] += 1
                bands[k] = c.most_common(3)
            census[f"editor{idx}"] = {"rect": [r.left - WR[0], r.top - WR[1],
                                                r.width(), r.height()], "rows": bands}
        json.dump(census, open(os.path.join(outdir, "merge-tints.json"), "w",
                               encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(meta, open(os.path.join(outdir, "meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps(meta, ensure_ascii=False))
        return 0
    finally:
        k32.TerminateJobObject(job, 0)
        ctypes.windll.kernel32.CloseHandle(job)
        time.sleep(0.5)
        left = [w for w in top_windows(pi.dwProcessId)]
        meta["residue"] = left
        print("residue:", left)


if __name__ == "__main__":
    sys.exit(main())
