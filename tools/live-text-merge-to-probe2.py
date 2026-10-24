#!/usr/bin/env python3
"""Round-2 merge-to probe: close the two round-1 gaps.

  C2  3-file: after dismissing the "Save File on File System As - Output Side"
      dialog with Esc, re-enumerate the radio row (retry loop) and click Left,
      then Ctrl+S: does the LEFT file get the merge output with NO dialog?
  D2  4-file: open the Session menu via UIA MenuItem, snapshot the popup item
      list (names + enabled states), invoke "Session Settings...", capture the
      dialog UIA tree; then physical-click the toolbar "Swap" button and pixel-
      compare pane regions (does Swap Sides exchange the side panes?).

Both launches: Job Object, CREATE_SUSPENDED, redirected profile, zero residue.
Outputs -> extracted/live/textmerge-to-en/ (round-2 subfolders, shared meta).
Usage: python tools/live-text-merge-to-probe2.py <BCompare.exe> <outdir>
"""
import ctypes
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (create_kill_job, top_windows, get_class,
                            get_window_text)  # noqa: E402
from live_probe_job import launch as plaunch  # noqa: E402
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
    time.sleep(1.2)


def visible_windows(pid):
    return [[get_class(w), get_window_text(w)]
            for w in top_windows(pid) if u32.IsWindowVisible(w)]


def run(tag, nfiles, steps, outdir):
    od = os.path.join(outdir, f"round2-{tag}")
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
        for name, fn in steps:
            try:
                fn(name, ctx)
            except Exception as e:
                meta[f"step-{name}-err"] = repr(e)
        return meta
    finally:
        k32.TerminateJobObject(job, 0)
        ctypes.windll.kernel32.CloseHandle(job)
        time.sleep(0.5)
        meta["residue"] = visible_windows(pi.dwProcessId)


def main():
    global exe
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(os.path.join(outdir, "round2-meta.json")):
        os.remove(os.path.join(outdir, "round2-meta.json"))
    all_meta = {}

    # ---- C2: 3-file: dialog -> Esc -> retry radio Left -> Ctrl+S ----
    def c2(name, ctx):
        m = ctx["meta"]
        ctrl_s(ctx)
        m["dialogs-after-ctrl-s"] = visible_windows(ctx["pid"])
        esc(ctx)
        time.sleep(1.0)
        m["dialogs-after-esc"] = visible_windows(ctx["pid"])
        # retry radio enumeration while the tree settles
        clicked = False
        for attempt in range(6):
            try:
                radios = ctx["win"].descendants(control_type="RadioButton")
            except Exception as e:
                m[f"enum-err-{attempt}"] = repr(e)
                time.sleep(1.0)
                continue
            left = [r for r in radios if r.element_info.name == "Left"]
            if left:
                left[0].click_input()
                clicked = True
                m["radio-click-attempt"] = attempt
                break
            time.sleep(1.0)
        m["clicked-left"] = clicked
        if not clicked:
            return
        time.sleep(1.0)
        ctx["snap"](name + "-radio")
        ctrl_s(ctx)
        m["dialogs-after-ctrl-s-left"] = visible_windows(ctx["pid"])
        m["title-saved-left"] = get_window_text(ctx["hwnd"])
        for p in ctx["files"]:
            after = read_file(p)
            m[f"changed-{os.path.basename(p)}"] = (after != ctx["orig"][p])
            m[f"content-{os.path.basename(p)}"] = after
        ctx["snap"](name)

    all_meta["C2"] = run("C2-3file-left", 3, [("c2", c2)], outdir)

    # ---- D2: session menu + Session Settings dialog + Swap physical click ----
    def d2a(name, ctx):
        """Open the Session menu via UIA, snapshot items, open the dialog."""
        from pywinauto import Desktop
        m = ctx["meta"]
        wait_foreground(ctx)
        items = [x for x in ctx["win"].descendants(control_type="MenuItem")
                 if x.element_info.name == "Session"]
        m["session-menuitems-found"] = len(items)
        if not items:
            return
        try:
            items[0].invoke()
        except Exception:
            items[0].click_input()
        time.sleep(1.2)
        # popup menu items (native menu may surface under the window or desktop)
        pops = []
        for el in Desktop(backend="uia").top_level():
            try:
                for it in el.descendants(control_type="MenuItem"):
                    ei = it.element_info
                    pops.append([ei.name, str(it.enabled)])
            except Exception:
                pass
        m["popup-menuitems"] = pops[:60]
        sub = None
        for el in Desktop(backend="uia").top_level():
            try:
                cand = [it for it in el.descendants(control_type="MenuItem")
                        if it.element_info.name and
                        it.element_info.name.startswith("Session Settings")]
                if cand:
                    sub = cand[0]
                    break
            except Exception:
                pass
        if sub is None:
            m["dialog-open"] = "popup item not found"
            esc(ctx)
            return
        try:
            sub.invoke()
        except Exception:
            sub.click_input()
        time.sleep(2.5)
        dlg = visible_windows(ctx["pid"])
        m["windows-after-session-settings"] = dlg
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
                m[f"dlg{i}-class-title"] = [cls, title]
            except Exception as e:
                m[f"dlg{i}-err"] = repr(e)
        ctx["snap"](name)
        esc(ctx)
        time.sleep(1.0)

    def d2b(name, ctx):
        """Physical click on toolbar Swap; pixel-compare pane exchange."""
        import numpy as np
        m = ctx["meta"]
        btn = [x for x in ctx["win"].descendants(control_type="Button")
               if x.element_info.name == "Swap"]
        if not btn:
            m["err-swap"] = "no Swap button"
            return
        btn[0].click_input()
        time.sleep(2.0)
        m["title-after-swap"] = get_window_text(ctx["hwnd"])
        ctx["snap"](name)
        img, _ = capture_window(ctx["hwnd"])
        p2 = os.path.join(ctx["outdir"], "window-swap-after.png")
        img.save(p2)
        a0 = numpy.asarray(Image.open(os.path.join(
            ctx["outdir"], "window-step0.png")).convert("RGB")).astype(int)
        a1 = numpy.asarray(Image.open(p2).convert("RGB")).astype(int)

        def reg(a, x, y, w, h):
            return a[y:y + h, x:x + w]

        def diff(a, b):
            return int((numpy.abs(a - b).sum(axis=2) > 10).sum())

        panes = {"L": (8, 154, 479, 226), "C": (491, 154, 474, 226),
                 "R": (969, 154, 479, 226), "OUT": (60, 491, 1388, 340)}
        m["pane-diffs"] = {
            "L_step0_vs_swap": diff(reg(a0, *panes["L"]), reg(a1, *panes["L"])),
            "R_step0_vs_swap": diff(reg(a0, *panes["R"]), reg(a1, *panes["R"])),
            "C_step0_vs_swap": diff(reg(a0, *panes["C"]), reg(a1, *panes["C"])),
            "OUT_step0_vs_swap": diff(reg(a0, *panes["OUT"]), reg(a1, *panes["OUT"])),
            "L_step0_vs_R_swap": diff(reg(a0, *panes["L"]), reg(a1, *panes["R"])),
            "R_step0_vs_L_swap": diff(reg(a0, *panes["R"]), reg(a1, *panes["L"])),
        }

    all_meta["D2"] = run("D2-session-swap", 4,
                         [("session-menu", d2a), ("swap", d2b)], outdir)

    json.dump(all_meta, open(os.path.join(outdir, "round2-meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
    for tag, m in all_meta.items():
        print("=====", tag)
        for k in sorted(m):
            v = m[k]
            if k.startswith("content"):
                v = str(v)[:100]
            elif k == "popup-menuitems":
                v = v[:40]
            print(" ", k, "=", v)


if __name__ == "__main__":
    sys.exit(main())
