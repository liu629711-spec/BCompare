#!/usr/bin/env python3
"""Text Merge EDIT + SAVE probe (docs/20 feature 2, tier-2 recon).

ONE reference-BCompare launch (Job Object, CREATE_SUSPENDED, serial, zero
residue). Command form (verified help/command_line_reference.html):
  BCompare.exe <Left> <Right> <Center> <Output>   (4 files -> merge + output)

Answering the two open questions that decide the GUI design (help asserts
"non-editable source panes + editable output pane" — viewtextmerge.html — but
NOT these behavioral edges):
  Q1 INIT: with a pre-populated <Output> file, does the output pane show the
     file's own content (OUT loaded verbatim) or BC's auto-merged result?
  Q2 SAVE timing: after typing into the output pane, is the <Output> file
     updated immediately (auto-write) or only on an explicit Ctrl+S?
     (help lists File>Save File as an action -> explicit save expected)

Probe beats:
  step0     open, snapshot output-pane text + OUT file content
  typed     click output pane, type a unique marker, re-snapshot
            -> read OUT file WITHOUT saving (Q2 immediate-write check)
  saved     Ctrl+S, then re-read OUT file (Q2 explicit-write check)

The <Output> fixture is a throwaway temp file so nothing user-owned is
touched; any un-saved edit dies with the job-kill. Outputs ->
extracted/live/textmerge-edit-en/.
Usage: python tools/live-text-merge-edit-probe.py <BCompare.exe> <outdir> <L> <R> <C> <OUT>
"""
import ctypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (launch, create_kill_job, top_windows, get_class,
                            get_window_text)  # noqa: E402
from live_text_px import capture_window  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
MARKER = "ZZEDITMARKER7"


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


def texts_of(el, acc, d=0):
    try:
        if d > 16:
            return
        ei = el.element_info
        if (ei.control_type or "") == "Text" and ei.name:
            acc.append(ei.name)
        for c in el.children():
            texts_of(c, acc, d + 1)
    except Exception:
        pass


def find_editors(el, out, d=0):
    try:
        if d > 24:
            return
        if (el.element_info.class_name or "") == "TTextEditor":
            out.append(el)
            return
        for c in el.children():
            find_editors(c, out, d + 1)
    except Exception:
        pass


def main():
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    L, R, C, OUTF = (os.path.abspath(sys.argv[i]) for i in (3, 4, 5, 6))
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    meta = {"exe": exe, "L": L, "R": R, "C": C, "OUT": OUTF,
            "OUT_preset": open(OUTF, encoding="utf-8", errors="replace").read()}

    def read_out():
        try:
            return open(OUTF, encoding="utf-8", errors="replace").read()
        except Exception as e:
            return f"<ERR {e}>"

    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof}, args=[L, R, C, OUTF])
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
        from pywinauto import Desktop, keyboard
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(2.0)

        def snap(tag):
            tree = []
            preorder(win, tree)
            json.dump(tree, open(os.path.join(outdir, f"tree-{tag}.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=1)
            try:
                img, rect = capture_window(main_h)
                img.save(os.path.join(outdir, f"window-{tag}.png"))
                meta["rect-" + tag] = list(rect)
            except Exception as e:
                meta[f"snap-{tag}-err"] = str(e)

        # ---- step0: which pane is editable, output content, OUT file state ----
        snap("step0")
        meta["title"] = get_window_text(main_h)
        eds = []
        find_editors(win, eds)
        meta["n_editors"] = len(eds)
        # output pane = the TTextEditor whose footer does NOT say 'Editing disabled'
        out_texts = []
        out_pane = None
        for i, ed in enumerate(eds):
            acc = []
            texts_of(ed, acc)
            disabled = any("Editing disabled" in a for a in acc)
            footers = [a for a in acc if ":" in a and len(a) < 12]
            meta[f"editor{i}"] = {"disabled": disabled, "footers": footers[:3]}
            if not disabled and out_pane is None:
                out_pane = ed
                meta["output_pane_index"] = i
        meta["OUT_after_step0"] = read_out()

        # ---- typed: click output pane, type marker, read OUT WITHOUT saving ----
        if out_pane is None:
            meta["error"] = "no editable output pane found"
        else:
            try:
                out_pane.click_input()
            except Exception as e:
                meta["click_err"] = str(e)
            time.sleep(0.8)
            keyboard.send_keys(MARKER)
            time.sleep(1.2)
            snap("typed")
            meta["OUT_after_typed_nosave"] = read_out()

            # ---- saved: explicit Ctrl+S then read OUT ----
            # a Ctrl+S on a pre-named existing file should write directly; if a
            # modal Save dialog appears, a NEW top window shows up (recorded).
            keyboard.send_keys("^s")
            time.sleep(1.6)
            dlg = []
            for w in top_windows(pi.dwProcessId):
                cls = get_class(w)
                if u32.IsWindowVisible(w) and cls != "TViewForm":
                    dlg.append([cls, get_window_text(w)])
            meta["post_ctrls_windows"] = dlg
            snap("saved")
            meta["OUT_after_ctrl_s"] = read_out()

        json.dump(meta, open(os.path.join(outdir, "meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        # compact stdout summary
        print(json.dumps({
            "n_editors": meta["n_editors"],
            "output_pane_index": meta.get("output_pane_index"),
            "OUT_preset": repr(meta["OUT_preset"])[:60],
            "OUT_after_step0": repr(meta.get("OUT_after_step0", ""))[:60],
            "OUT_after_typed_nosave": repr(meta.get("OUT_after_typed_nosave", ""))[:60],
            "OUT_after_ctrl_s": repr(meta.get("OUT_after_ctrl_s", ""))[:60],
            "editor_flags": {f"e{i}": meta[f"editor{i}"]["disabled"] for i in range(meta["n_editors"])},
        }, ensure_ascii=False))
        return 0
    finally:
        k32.TerminateJobObject(job, 0)
        ctypes.windll.kernel32.CloseHandle(job)
        time.sleep(0.5)
        print("residue:", [w for w in top_windows(pi.dwProcessId)])


if __name__ == "__main__":
    sys.exit(main())
