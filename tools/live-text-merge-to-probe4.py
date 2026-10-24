#!/usr/bin/env python3
"""Round-4 merge-to probe: Session Settings dialog only.

The Session menubar item is physically clicked (click_input), then every
visible window of the process is enumerated repeatedly for 5s to catch the
popup (whatever class VCL uses) and the dialog. The popup item tree and the
dialog tree are captured; the dialog is closed via its own Cancel button.

Usage: python tools/live-text-merge-to-probe4.py <BCompare.exe> <outdir>
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


def visible_windows(pid):
    return [[get_class(w), get_window_text(w)]
            for w in top_windows(pid) if u32.IsWindowVisible(w)]


def main():
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    tag = "R4-dialog"
    od = os.path.join(outdir, tag)
    if os.path.exists(od):
        shutil.rmtree(od)
    os.makedirs(od, exist_ok=True)
    L, R, C = make_fixtures(od)
    OUT = os.path.join(od, "out.txt")
    open(OUT, "w", encoding="utf-8", newline="\n").write("PRESETPANE_OUT\n")
    meta = {}

    job = create_kill_job()
    si, pi = plaunch(exe, {"APPDATA": os.path.join(od, "_profile"),
                           "LOCALAPPDATA": os.path.join(od, "_profile")},
                     args=[L, R, C, OUT])
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
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(2.0)
        meta["windows-before"] = visible_windows(pi.dwProcessId)

        # physical click on the Session menubar item
        items = [x for x in win.descendants(control_type="MenuItem")
                 if x.element_info.name == "Session"]
        meta["found"] = len(items)
        if items:
            items[0].click_input()
        seen = {}
        popup_h = dlg_h = None
        t0 = time.time()
        while time.time() - t0 < 6:
            for cls, title in visible_windows(pi.dwProcessId):
                seen[f"{cls}|{title}"] = seen.get(f"{cls}|{title}", 0) + 1
            ws = [w for w in top_windows(pi.dwProcessId) if u32.IsWindowVisible(w)]
            for w in ws:
                cls = get_class(w)
                if cls == "TViewForm":
                    continue
                if cls in ("#32768", "TTBPopupWindow") and popup_h is None:
                    popup_h = w
                if cls not in ("TViewForm", "TApplication", "#32768",
                               "TUiMainMenu", "TTBPopupWindow", "SysShadow")                         and dlg_h is None:
                    dlg_h = w
            if dlg_h:
                break
            time.sleep(0.3)
        meta["seen-windows"] = seen
        meta["popup_h"] = bool(popup_h)
        meta["dlg_h"] = get_class(dlg_h) if dlg_h else None
        for name, hw in (("popup", popup_h), ("dialog", dlg_h)):
            if hw:
                w = Desktop(backend="uia").window(handle=hw)
                tree = []
                preorder(w.wrapper_object(), tree)
                json.dump(tree, open(os.path.join(od, f"tree-{name}.json"),
                          "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        img, _ = capture_window(main_h)
        img.save(os.path.join(od, "window-state.png"))

        # walk into Session Settings if the popup is open
        if popup_h and not dlg_h:
            pw = Desktop(backend="uia").window(handle=popup_h)
            sub = [it for it in pw.descendants(control_type="MenuItem")
                   if it.element_info.name and
                   it.element_info.name.startswith("Session Settings")]
            meta["sub-found"] = len(sub)
            if sub:
                try:
                    sub[0].invoke()
                except Exception:
                    sub[0].click_input()
                time.sleep(2.5)
                for w in top_windows(pi.dwProcessId):
                    cls = get_class(w)
                    if u32.IsWindowVisible(w) and cls not in (
                            "TViewForm", "TApplication", "TUiMainMenu", "#32768"):
                        dlg_h = w
                        break
                if dlg_h:
                    w = Desktop(backend="uia").window(handle=dlg_h)
                    tree = []
                    preorder(w.wrapper_object(), tree)
                    json.dump(tree, open(os.path.join(od, "tree-dialog.json"),
                              "w", encoding="utf-8"), ensure_ascii=False,
                              indent=1)
                    meta["dialog-title"] = get_window_text(dlg_h)
                    img, _ = capture_window(dlg_h)
                    img.save(os.path.join(od, "window-dialog.png"))
                    # close via Cancel button
                    canc = [b for b in w.descendants(control_type="Button")
                            if b.element_info.name in ("Cancel", "取消")]
                    meta["cancel-found"] = len(canc)
                    if canc:
                        canc[0].invoke()
                        time.sleep(1.0)
        meta["windows-final"] = visible_windows(pi.dwProcessId)
        return 0
    finally:
        k32.TerminateJobObject(job, 0)
        ctypes.windll.kernel32.CloseHandle(job)
        time.sleep(0.5)
        meta["residue"] = visible_windows(pi.dwProcessId)
        json.dump(meta, open(os.path.join(outdir, "round4-meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps(meta, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
