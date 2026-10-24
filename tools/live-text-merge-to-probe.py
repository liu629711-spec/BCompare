#!/usr/bin/env python3
"""Text Merge "Merge to" + session-level switching probe (feature 2 wrap-up).

ONE script, FOUR strictly serial reference-BCompare launches (each: Job Object,
CREATE_SUSPENDED, redirected temp profile, zero residue). Command forms
(help/command_line_reference.html, both already probed §6.15/§6.17):
  BCompare.exe <L> <R> <C> <OUT>    4-file merge (OUT = named save target)
  BCompare.exe <L> <R> <C>          3-file merge (no output path)

Open questions (help only says "Merge to defines the destination file of the
merge results", sessiontextmergespecs.html — the VIEW-level behavior is
unmeasured; 禁臆测):
  QA  4-file: click radio "Left"  -> Ctrl+S: does the LEFT file get the merge
      output? does OUT stay untouched? does anything re-render (pixel diff)?
  QB  4-file: same for "Right".
  QC  3-file: Ctrl+S on default "Other:" (no output path) -> dialog? then
      radio "Left" -> Ctrl+S: direct write, no dialog? (closes the §6.17
      recorded gap "3-file save path unprobed")
  QD  4-file: Session->Session Settings dialog structure (UIA tree) +
      toolbar "Swap": do the side panes exchange and the output recompute?

Fixtures per launch (clean family, §6.15): C=base 8 lines, L changes line2,
R changes line5; OUT preset with a sentinel that must never appear on disk.

Outputs -> extracted/live/textmerge-to-en/
Usage: python tools/live-text-merge-to-probe.py <BCompare.exe> <outdir>
"""
import ctypes
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (launch as plaunch, create_kill_job, top_windows,
                            get_class, get_window_text)  # noqa: E402
from live_text_px import capture_window  # noqa: E402

import numpy  # noqa: E402
from PIL import Image  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32

SEL_TINT = (194, 220, 245)   # selected radio tint (merge-palette.json)
TOL = 12


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


def make_fixtures(d):
    base = [f"line {w}" for w in ("one", "two", "three", "four", "five",
                                  "six", "seven", "eight")]

    def w(name, lines):
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
        return p

    left = list(base); left[1] = "L-TWO-CHANGED"
    right = list(base); right[4] = "R-FIVE-CHANGED"
    return w("left.txt", left), w("right.txt", right), w("base.txt", base)


def read_file(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return f"<ERR {e}>"


def png_diff(a_path, b_path):
    a = numpy.asarray(Image.open(a_path).convert("RGB")).astype(int)
    b = numpy.asarray(Image.open(b_path).convert("RGB")).astype(int)
    if a.shape != b.shape:
        return -1, int(a.shape[0] * a.shape[1])
    return int((numpy.abs(a - b).sum(axis=2) > 10).sum()), int(a.shape[0] * a.shape[1])


def radio_census(ctx, tag):
    """UIA radios (name/rect/toggle) + selected-tint pixel vote per radio."""
    win, od, meta = ctx["win"], ctx["outdir"], ctx["meta"]
    radios = []
    for r in win.descendants(control_type="RadioButton"):
        ei = r.element_info
        try:
            ts = str(r.get_toggle_state())
        except Exception:
            ts = None
        rc = ei.rectangle
        radios.append({"name": ei.name,
                       "rect": [rc.left, rc.top, rc.width(), rc.height()],
                       "toggle": ts})
    meta.setdefault("radios", {})[tag] = radios
    png = os.path.join(od, f"window-{tag}.png")
    if not os.path.exists(png) or not radios:
        return
    arr = numpy.asarray(Image.open(png).convert("RGB")).astype(int)
    wr = meta.get("rects", {}).get(tag)
    votes = {}
    for r in radios:
        x0, y0, w, h = r["rect"]
        if wr:
            x0 -= wr[0]; y0 -= wr[1]
        cnt = 0
        for y in range(max(0, y0), min(y0 + h, arr.shape[0]), 2):
            for x in range(max(0, x0), min(x0 + w, arr.shape[1]), 2):
                px = arr[y, x]
                if all(abs(int(px[i]) - SEL_TINT[i]) <= TOL for i in range(3)):
                    cnt += 1
        votes[r["name"]] = cnt
    meta.setdefault("radio_tint_votes", {})[tag] = votes


def dialog_windows(pid):
    return [[get_class(w), get_window_text(w)]
            for w in top_windows(pid) if u32.IsWindowVisible(w)]


def wait_foreground(ctx, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout and \
            u32.GetForegroundWindow() != ctx["hwnd"]:
        time.sleep(0.1)
    ctx["win"].set_focus()
    time.sleep(0.3)


def ctrl_s(ctx):
    wait_foreground(ctx)
    ctx["win"].type_keys("^s")
    time.sleep(1.6)


def esc(ctx):
    wait_foreground(ctx)
    ctx["win"].type_keys("{ESC}")
    time.sleep(0.8)


def click_radio(ctx, name):
    r = [x for x in ctx["win"].descendants(control_type="RadioButton")
         if x.element_info.name == name]
    if not r:
        return False
    r[0].click_input()
    time.sleep(1.0)
    return True


def disk_check(meta, files, orig, prefix=""):
    for p in files:
        after = read_file(p)
        meta[f"{prefix}changed-{os.path.basename(p)}"] = (after != orig[p])
        meta[f"{prefix}content-{os.path.basename(p)}"] = after


def launch(exe, outdir, tag, nfiles, steps_fn):
    """Build fresh fixtures and run one contained launch with `steps_fn`."""
    od = os.path.join(outdir, f"launch-{tag}")
    if os.path.exists(od):
        shutil.rmtree(od)
    os.makedirs(od, exist_ok=True)
    L, R, C = make_fixtures(od)
    args = [L, R, C]
    if nfiles == 4:
        OUT = os.path.join(od, "out.txt")
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write("PRESETPANE_MERGETO_OUT_1\nPRESETPANE_MERGETO_OUT_2\n")
        args = [L, R, C, OUT]
    files = list(args)
    orig = {p: read_file(p) for p in files}

    meta = {"tag": tag, "files": [os.path.basename(p) for p in files]}
    job = create_kill_job()
    si, pi = plaunch(exe, {"APPDATA": os.path.join(od, "_profile"),
                           "LOCALAPPDATA": os.path.join(od, "_profile")},
                     args=args)
    ctx = {"pid": pi.dwProcessId, "outdir": od, "meta": meta, "files": files,
           "orig": orig}
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
        ctx["hwnd"] = main_h
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        ctx["win"] = win
        win.set_focus()
        time.sleep(2.0)

        def snap(name):
            tree = []
            preorder(win, tree)
            json.dump(tree, open(os.path.join(od, f"tree-{name}.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=1)
            img, rect = capture_window(main_h)
            img.save(os.path.join(od, f"window-{name}.png"))
            meta.setdefault("rects", {})[name] = list(rect)

        ctx["snap"] = snap

        def step0(name, _ctx):
            snap(name)
            radio_census(ctx, name)
            meta["title-step0"] = get_window_text(main_h)
            meta["windows-step0"] = dialog_windows(pi.dwProcessId)

        for name, fn in [("step0", step0)] + steps_fn:
            try:
                fn(name, ctx)
            except Exception as e:
                meta[f"step-{name}-err"] = repr(e)
        return meta
    finally:
        k32.TerminateJobObject(job, 0)
        ctypes.windll.kernel32.CloseHandle(job)
        time.sleep(0.5)
        meta["residue"] = dialog_windows(pi.dwProcessId)


def main():
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)
    all_meta = {}

    # ---- A: 4-file, switch radio LEFT, Ctrl+S ----
    def steps_A():
        def sel_left(name, ctx):
            if not click_radio(ctx, "Left"):
                ctx["meta"]["err-sel-left"] = "no Left radio"
                return
            ctx["snap"](name)
            radio_census(ctx, name)
            ctx["meta"]["title-sel-left"] = get_window_text(ctx["hwnd"])
            ctx["meta"]["pngdiff-step0->sel-left"] = png_diff(
                os.path.join(ctx["outdir"], "window-step0.png"),
                os.path.join(ctx["outdir"], "window-sel-left.png"))

        def saved(name, ctx):
            ctrl_s(ctx)
            ctx["snap"](name)
            m = ctx["meta"]
            m["dialogs-after-ctrl-s"] = dialog_windows(ctx["pid"])
            m["title-saved"] = get_window_text(ctx["hwnd"])
            disk_check(m, ctx["files"], ctx["orig"])
            m["pngdiff-sel->saved"] = png_diff(
                os.path.join(ctx["outdir"], "window-sel-left.png"),
                os.path.join(ctx["outdir"], "window-saved.png"))
        return [("sel-left", sel_left), ("saved", saved)]

    all_meta["A"] = launch(exe, outdir, "A-4file-left", 4, steps_A())

    # ---- B: 4-file, switch radio RIGHT, Ctrl+S ----
    def steps_B():
        def sel_right(name, ctx):
            if not click_radio(ctx, "Right"):
                ctx["meta"]["err-sel-right"] = "no Right radio"
                return
            ctx["snap"](name)
            radio_census(ctx, name)
            ctx["meta"]["title-sel-right"] = get_window_text(ctx["hwnd"])
            ctx["meta"]["pngdiff-step0->sel-right"] = png_diff(
                os.path.join(ctx["outdir"], "window-step0.png"),
                os.path.join(ctx["outdir"], "window-sel-right.png"))

        def saved(name, ctx):
            ctrl_s(ctx)
            ctx["snap"](name)
            m = ctx["meta"]
            m["dialogs-after-ctrl-s"] = dialog_windows(ctx["pid"])
            m["title-saved"] = get_window_text(ctx["hwnd"])
            disk_check(m, ctx["files"], ctx["orig"])
            m["pngdiff-sel->saved"] = png_diff(
                os.path.join(ctx["outdir"], "window-sel-right.png"),
                os.path.join(ctx["outdir"], "window-saved.png"))
        return [("sel-right", sel_right), ("saved", saved)]

    all_meta["B"] = launch(exe, outdir, "B-4file-right", 4, steps_B())

    # ---- C: 3-file, default-Other save (dialog?), then LEFT save ----
    def steps_C():
        def save_default(name, ctx):
            ctrl_s(ctx)
            m = ctx["meta"]
            m["dialogs-after-ctrl-s-default"] = dialog_windows(ctx["pid"])
            ctx["snap"](name)
            disk_check(m, ctx["files"], ctx["orig"])
            esc(ctx)
            m["dialogs-after-esc"] = dialog_windows(ctx["pid"])

        def sel_left_save(name, ctx):
            if not click_radio(ctx, "Left"):
                ctx["meta"]["err-sel-left"] = "no Left radio"
                return
            ctx["snap"](name + "-radio")
            radio_census(ctx, name + "-radio")
            ctrl_s(ctx)
            m = ctx["meta"]
            m["dialogs-after-ctrl-s-left"] = dialog_windows(ctx["pid"])
            m["title-saved-left"] = get_window_text(ctx["hwnd"])
            disk_check(m, ctx["files"], ctx["orig"], prefix="leftsave-")
            ctx["snap"](name)
        return [("save-default", save_default), ("left-save", sel_left_save)]

    all_meta["C"] = launch(exe, outdir, "C-3file-other-left", 3, steps_C())

    # ---- D: 4-file, Session Settings dialog + toolbar Swap ----
    def steps_D():
        def session_settings(name, ctx):
            win = ctx["win"]
            wait_foreground(ctx)
            try:
                win.menu_select("Session->Session Settings...")
            except Exception as e:
                ctx["meta"]["menu-select-err"] = repr(e)
            time.sleep(2.0)
            dlg = dialog_windows(ctx["pid"])
            ctx["meta"]["windows-after-menu-select"] = dlg
            from pywinauto import Desktop
            handles = {get_window_text(h): h for h in top_windows(ctx["pid"])}
            for i, (cls, title) in enumerate(dlg):
                if cls in ("TViewForm", "TApplication", "TUiMainMenu"):
                    continue
                h = handles.get(title)
                if h is None:
                    continue
                try:
                    w = Desktop(backend="uia").window(handle=h)
                    tree = []
                    preorder(w.wrapper_object(), tree)
                    json.dump(tree, open(os.path.join(
                        ctx["outdir"], f"tree-{name}-dlg{i}.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
                    ctx["meta"][f"dlg{i}-class-title"] = [cls, title]
                except Exception as e:
                    ctx["meta"][f"dlg{i}-err"] = repr(e)
            ctx["snap"](name)
            esc(ctx)

        def toolbar_swap(name, ctx):
            win = ctx["win"]
            b = [x for x in win.descendants(control_type="Button")
                 if x.element_info.name == "Swap"]
            if not b:
                ctx["meta"]["err-swap"] = "no Swap button"
                return
            try:
                b[0].invoke()
            except Exception:
                b[0].click_input()
            time.sleep(1.5)
            ctx["snap"](name)
            ctx["meta"]["title-after-swap"] = get_window_text(ctx["hwnd"])
            ctx["meta"]["pngdiff-step0->swap"] = png_diff(
                os.path.join(ctx["outdir"], "window-step0.png"),
                os.path.join(ctx["outdir"], "window-swap.png"))
            radio_census(ctx, name)
        return [("session-settings", session_settings), ("swap", toolbar_swap)]

    all_meta["D"] = launch(exe, outdir, "D-session-swap", 4, steps_D())

    json.dump(all_meta, open(os.path.join(outdir, "merge-to-meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)

    summary = {}
    for tag in ("A", "B", "C", "D"):
        m = all_meta.get(tag, {})
        s = {"residue_windows": len(m.get("residue", []))}
        for k in sorted(m):
            if k.startswith(("changed", "pngdiff", "radios", "radio_tint",
                             "title", "dialogs", "windows-", "err", "menu",
                             "dlg")):
                s[k] = m[k]
            elif k.startswith("content"):
                s[k] = m[k][:130]
        summary[tag] = s
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
