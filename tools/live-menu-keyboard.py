#!/usr/bin/env python3
"""Keyboard-driven menu capture: BC's menu bar is VCL-owner-drawn (TUiMainMenu),
UIA ExpandCollapse does not materialize submenu items, and the native HMENU is
absent. But when a menu is OPENED (keyboard or click), Delphi shows its items —
as native popup (#32768) or a VCL popup class. This probe:
  1. launches under job, waits for TViewForm,
  2. foregrounds it, presses Alt (menu mode) + arrow to open each top menu,
  3. enumerates all visible windows of the pid + dumps any native menu they hold,
  4. ESC closes; repeat per top-menu index.
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import launch, create_kill_job, top_windows, get_class, read_menu  # noqa: E402

k32 = ctypes.windll.kernel32
u32 = ctypes.windll.user32
k32.AssignProcessToJobObject.restype = wintypes.BOOL
k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.ResumeThread.argtypes = [wintypes.HANDLE]

EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def visible_windows_of(pid):
    found = []

    def cb(h, _):
        p = wintypes.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and u32.IsWindowVisible(h):
            r = wintypes.RECT()
            u32.GetWindowRect(h, ctypes.byref(r))
            found.append((h, get_class(h), r.left, r.top, r.right, r.bottom))
        return True

    u32.EnumWindows(EnumProc(cb), 0)
    return found


def tap(vk, sec=0.5):
    u32.keybd_event(vk, 0, 0, 0)
    u32.keybd_event(vk, 0, 2, 0)
    time.sleep(sec)


def dump_opened(pid, base):
    """Diff visible windows vs baseline; return structures found for new popups."""
    out = []
    for h, cls, l, t, r_, b in visible_windows_of(pid):
        key = (h, cls)
        if key in base:
            continue
        rec = {"class": cls, "rect": [l, t, r_, b], "native_menu": None, "uia": None}
        hm = u32.GetMenu(h)
        if hm:
            rec["native_menu"] = read_menu(hm)
        out.append(rec)
    return out


def main():
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    os.makedirs(outdir, exist_ok=True)
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)

    result = {"menus": {}}
    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof})
    try:
        if not k32.AssignProcessToJobObject(job, k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)):
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
            result["error"] = "no window"
        else:
            u32.ShowWindow(main_h, 9)
            u32.SetForegroundWindow(main_h)
            time.sleep(1.5)
            top_names = []
            # enter menu mode
            tap(0x12, 1.0)          # Alt alone -> VCL enters menu mode
            tap(0x0D, 1.0)          # Enter opens first top menu? use F10+Enter safer:
            # determine top menu count by walking; capture each popup
            for idx in range(10):
                if idx == 0:
                    pass  # already opened one via Enter
                else:
                    tap(0x27, 0.9)  # VK_RIGHT to next top menu
                base = set((h, c) for h, c, *_ in visible_windows_of(pi.dwProcessId))
                time.sleep(0.4)
                news = dump_opened(pi.dwProcessId, base)
                # label from UIA: get focused element text
                lbl = None
                try:
                    lbl = get_class(main_h)
                except Exception:
                    pass
                result["menus"][f"top{idx}"] = news
                tap(0x1B, 0.3)  # ESC closes submenu but keeps menu mode? press twice later
            # collect names from title? re-read via UIA menubar children
            tap(0x1B, 0.3)
            tap(0x1B, 0.3)
    finally:
        k32.CloseHandle(job)
        if pi.hProcess:
            k32.WaitForSingleObject(pi.hProcess, 4000)
            k32.CloseHandle(pi.hProcess)
            k32.CloseHandle(pi.hThread)
    with open(os.path.join(outdir, "keyboard-menus.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v and [x["class"] for x in v] or [] for k, v in result.get("menus", {}).items()}, indent=0))


if __name__ == "__main__":
    sys.exit(main())
