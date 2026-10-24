#!/usr/bin/env python3
"""Round-3 merge-to probe — fixes round-2 probe bugs (not product findings):

  C2  the round-2 Esc went through the stale main-window wrapper while the
      modal save dialog was up (ElementNotEnabled; dialog never closed).
      Now: close the dialog through its OWN hwnd (Cancel button / WM_CLOSE),
      re-acquire the main wrapper, then click Left and Ctrl+S.
  D2  Desktop.top_level() does not exist -> enumerate popup menus as #32768
      windows of the process; snapshot the step0 window before steps.

Outputs -> extracted/live/textmerge-to-en/round3-meta.json
Usage: python tools/live-text-merge-to-probe3.py <BCompare.exe> <outdir>
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

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32

WM_CLOSE = 0x0010
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
VK_ESCAPE = 0x1B


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


def visible_windows(pid):
    return [[get_class(w), get_window_text(w)]
            for w in top_windows(pid) if u32.IsWindowVisible(w)]


def send_esc(hwnd):
    u32.PostMessageW(hwnd, WM_KEYDOWN, VK_ESCAPE, 0)
    u32.PostMessageW(hwnd, WM_KEYUP, VK_ESCAPE, 0)


def close_dialogs(pid, mode="esc"):
    """Dismiss every visible dialog/menu window of the process."""
    closed = []
    for w in top_windows(pid):
        cls = get_class(w)
        if cls in ("TViewForm", "TApplication", "TUiMainMenu") or \
                not u32.IsWindowVisible(w):
            continue
        if cls in ("#32770", "#32768") or "Save" in get_window_text(w) or \
                "Settings" in get_window_text(w):
            if mode == "esc":
                send_esc(w)
            else:
                u32.PostMessageW(w, WM_CLOSE, 0, 0)
            closed.append([cls, get_window_text(w)])
            time.sleep(0.8)
    return closed


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


def reacquire(ctx):
    from pywinauto import Desktop
    ctx["win"] = Desktop(backend="uia").window(
        handle=ctx["hwnd"]).wrapper_object()
    ctx["win"].set_focus()
    time.sleep(0.8)


def run(tag, nfiles, steps, outdir, exe):
    od = os.path.join(outdir, f"round3-{tag}")
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
        snap("step0")
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
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    all_meta = {}

    # ---- C2: 3-file: dialog via own hwnd -> Esc -> Left -> Ctrl+S ----
    def c2(name, ctx):
        from pywinauto import Desktop
        m = ctx["meta"]
        ctrl_s(ctx)
        m["dialogs-after-ctrl-s"] = visible_windows(ctx["pid"])
        m["closed"] = close_dialogs(ctx["pid"], "esc")
        time.sleep(1.0)
        m["dialogs-after-esc"] = visible_windows(ctx["pid"])
        reacquire(ctx)
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
                try:
                    left[0].click_input()
                    clicked = True
                    m["radio-click-attempt"] = attempt
                    break
                except Exception as e:
                    m[f"click-err-{attempt}"] = repr(e)
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

    all_meta["C2"] = run("C2-3file-left", 3, [("c2", c2)], outdir, exe)

    # ---- D2: session popup items -> Session Settings dialog -> Swap ----
    def d2a(name, ctx):
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
        time.sleep(1.5)
        # popup menu = a visible #32768 window of the process
        pops = []
        sub_h = None
        for w in top_windows(ctx["pid"]):
            if get_class(w) == "#32768" and u32.IsWindowVisible(w):
                try:
                    ww = Desktop(backend="uia").window(handle=w)
                    tree = []
                    preorder(ww.wrapper_object(), tree)
                    json.dump(tree, open(os.path.join(
                        ctx["outdir"], "tree-session-popup.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
                    for it in ww.descendants(control_type="MenuItem"):
                        ei = it.element_info
                        pops.append([ei.name, str(ww.wrapper_object().enabled),
                                     str(it.enabled)])
                        if ei.name and ei.name.startswith("Session Settings"):
                            sub_h = it
                except Exception as e:
                    m["popup-err"] = repr(e)
        m["popup-menuitems"] = pops
        if sub_h is None:
            m["dialog-open"] = "popup item not found"
            close_dialogs(ctx["pid"], "esc")
            return
        try:
            sub_h.invoke()
        except Exception:
            sub_h.click_input()
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
        m["closed-settings"] = close_dialogs(ctx["pid"], "esc")
        time.sleep(1.0)

    def d2b(name, ctx):
        import numpy as np
        from PIL import Image
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
        a0 = np.asarray(Image.open(os.path.join(
            ctx["outdir"], "window-step0.png")).convert("RGB")).astype(int)
        a1 = np.asarray(Image.open(p2).convert("RGB")).astype(int)

        def reg(a, x, y, w, h):
            return a[y:y + h, x:x + w]

        def diff(a, b):
            return int((np.abs(a - b).sum(axis=2) > 10).sum())

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
                         [("session-menu", d2a), ("swap", d2b)], outdir, exe)

    json.dump(all_meta, open(os.path.join(outdir, "round3-meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
    for tag, m in all_meta.items():
        print("=====", tag)
        for k in sorted(m):
            v = m[k]
            if k.startswith("content"):
                v = str(v)[:100]
            elif k == "popup-menuitems":
                v = v[:45]
            print(" ", k, "=", v)


if __name__ == "__main__":
    sys.exit(main())
