#!/usr/bin/env python3
"""Live menu/window probe for the BCompare GUI oracle (docs/19 §3).

Launches BCompare.exe inside a kill-on-close Job Object, waits for its
top-level windows, then reads the *native* menu hierarchy via GetMenu /
GetSubMenu / GetMenuString (no foreground focus stealing, no clicking),
plus a class-name snapshot of all top-level and child windows.

Static (DFM) evidence says BC builds menus at runtime with TMenuPopulator
from ActionList categories; this probe captures the *resulting* menu tree,
which is the authoritative baseline for menu/shortcut replication.

Usage:
  python tools/live-menu-probe.py <BCompare.exe> <outdir> [--wait SEC]

Discipline: strictly serial with any harness run; the Job Object guarantees
process containment; caller must verify zero residue afterwards
(`tasklist //FI "IMAGENAME eq BCompare.exe"`).
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ctypes default restype c_int truncates 64-bit handles: declare signatures.
kernel32.CreateProcessW.restype = wintypes.BOOL
kernel32.CreateProcessW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p,
    ctypes.c_void_p, wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
    ctypes.c_void_p, ctypes.c_void_p]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
kernel32.CreateJobObjectW.restype = wintypes.HANDLE
kernel32.SetInformationJobObject.restype = wintypes.BOOL
kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
user32.GetMenu.restype = wintypes.HMENU
user32.GetMenu.argtypes = [wintypes.HWND]
user32.GetSubMenu.restype = wintypes.HMENU
user32.GetSubMenu.argtypes = [wintypes.HMENU, wintypes.UINT]
user32.GetMenuItemInfoW.restype = wintypes.BOOL

# ---- Job Object (same containment as harness) ----
JobObjExtendedBasicInformation = 9


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000


def create_kill_job():
    h = kernel32.CreateJobObjectW(None, None)
    if not h:
        raise ctypes.WinError()
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    ok = kernel32.SetInformationJobObject(
        h, JobObjExtendedBasicInformation, ctypes.byref(info), ctypes.sizeof(info)
    )
    if not ok:
        raise ctypes.WinError()
    return h


class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


CREATE_SUSPENDED = 0x4
CREATE_UNICODE_ENVIRONMENT = 0x400


def launch(exe, env_overrides=None):
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    pi = PROCESS_INFORMATION()
    env = None
    if env_overrides:
        base = dict(os.environ)
        base.update(env_overrides)
        # double-NUL terminated block; embedded NULs need create_unicode_buffer,
        # c_wchar_p would truncate at the first '\0'
        block = "\0".join(f"{k}={v}" for k, v in base.items()) + "\0\0"
        env = ctypes.create_unicode_buffer(block)
    ok = kernel32.CreateProcessW(
        exe, None, None, None, False, CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT, env, None, ctypes.byref(si), ctypes.byref(pi)
    )
    if not ok:
        raise ctypes.WinError()
    return si, pi


# ---- window enumeration ----
WM_GETTEXTLENGTH = 0x000E
WM_GETTEXT = 0x000D


def get_window_text(hwnd):
    n = user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.SendMessageW(hwnd, WM_GETTEXT, n + 1, buf)
    return buf.value[:n]


def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def top_windows(pid):
    found = []

    def cb(hwnd, _):
        wpid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value == pid:
            found.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found


def child_windows(pid):
    """All windows created by the process (EnumChildWindows over each top window)."""
    out = []

    def cb(hwnd, _):
        wpid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value == pid:
            cls = get_class(hwnd)
            out.append(cls)
        return True

    for top in top_windows(pid):
        user32.EnumChildWindows(top, EnumWindowsProc(cb), 0)
    return out


# ---- native menu traversal ----
MF_SEPARATOR = 0x0001
MF_ENABLED = 0x0000
MF_GRAYED = 0x0002
MF_DISABLED = 0x0004
MF_CHECKED = 0x0008
MF_POPUP = 0x0010
MF_OWNERDRAW = 0x0400


class MENUITEMINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("fMask", wintypes.UINT),
        ("fType", wintypes.UINT),
        ("fState", wintypes.UINT),
        ("wID", wintypes.UINT),
        ("hSubMenu", wintypes.HMENU),
        ("hbmpChecked", wintypes.HBITMAP),
        ("hbmpUnchecked", wintypes.HBITMAP),
        ("dwItemData", ctypes.c_void_p),
        ("dwTypeData", wintypes.LPWSTR),
        ("cch", wintypes.UINT),
        ("hbmpMenu", wintypes.HBITMAP),
        ("cch2", wintypes.UINT),   # fString2 support (menu item string 2)
        ("hbmpMenu2", wintypes.HBITMAP),
    ]


MIIM_FTYPE = 0x00000100
MIIM_STATE = 0x00000001
MIIM_ID = 0x00000002
MIIM_SUBMENU = 0x00000004
MIIM_STRING = 0x00000040
MIIM_STRING2 = 0x00004000


def read_menu(hmenu, depth=0, max_depth=6):
    count = user32.GetMenuItemCount(hmenu)
    items = []
    if count < 0:
        return items
    for i in range(count):
        mii = MENUITEMINFO()
        mii.cbSize = ctypes.sizeof(MENUITEMINFO)
        mii.fMask = MIIM_FTYPE | MIIM_STATE | MIIM_ID | MIIM_SUBMENU | MIIM_STRING
        # two-pass: GetMenuItemInfoW may need buffer sized by GetMenuStringW
        text_buf = ctypes.create_unicode_buffer(1024)
        user32.GetMenuStringW(hmenu, i, text_buf, 1024, 0x0400)  # MF_BYPOSITION | MF_STRING
        mii.dwTypeData = text_buf
        mii.cch = 1023
        ok = user32.GetMenuItemInfoW(hmenu, i, True, ctypes.byref(mii))
        ftype = mii.fType if ok else 0
        fstate = mii.fState if ok else 0
        if ftype & MF_SEPARATOR:
            items.append({"pos": i, "sep": True})
            continue
        raw = text_buf.value
        # strip VCL '...' kept as-is; strip accelerator '&' but keep '&&'
        label = raw.replace("&&", "\x00").replace("&", "").replace("\x00", "&")
        entry = {
            "pos": i,
            "label": label,
            "raw": raw,
            "id": int(mii.wID) if ok else None,
            "enabled": bool(ok) and (fstate & (MF_GRAYED | MF_DISABLED)) == 0,
            "checked": bool(ok) and (fstate & MF_CHECKED) != 0,
            "ownerdraw": bool(ftype & MF_OWNERDRAW),
        }
        if ok and (mii.fType & MF_POPUP) and mii.hSubMenu and depth < max_depth:
            entry["items"] = read_menu(mii.hSubMenu, depth + 1, max_depth)
        items.append(entry)
    return items


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    exe = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    wait = float(sys.argv[sys.argv.index("--wait") + 1]) if "--wait" in sys.argv else 12.0
    os.makedirs(outdir, exist_ok=True)

    # profile redirection: BC reads %APPDATA%\Beyond Compare; point both vars at a
    # throwaway dir so the probe cannot mutate the user's real configuration.
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)

    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof})
    try:
        handle = kernel32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)  # PROCESS_ALL_ACCESS
        if not kernel32.AssignProcessToJobObject(job, handle):
            raise ctypes.WinError()
        kernel32.ResumeThread(pi.hThread)
        # let it paint
        t0 = time.time()
        wins = []
        while time.time() - t0 < wait:
            wins = top_windows(pi.dwProcessId)
            if any(user32.IsWindowVisible(w) for w in wins):
                # small settle
                time.sleep(1.5)
                wins = top_windows(pi.dwProcessId)
                break
            time.sleep(0.5)

        snapshot = {
            "exe": exe,
            "pid": pi.dwProcessId,
            "waited_s": round(time.time() - t0, 1),
            "windows": [],
            "child_classes": {},
            "menus": {},
        }
        for w in wins:
            vis = bool(user32.IsWindowVisible(w))
            rect = wintypes.RECT()
            user32.GetWindowRect(w, ctypes.byref(rect))
            hm = user32.GetMenu(w)
            entry = {
                "hwnd": w,
                "class": get_class(w),
                "title": get_window_text(w),
                "visible": vis,
                "rect": [rect.left, rect.top, rect.right, rect.bottom],
                "has_menu": bool(hm),
            }
            snapshot["windows"].append(entry)
            if hm:
                snapshot["menus"][f"{get_class(w)}|{entry['title']}"] = read_menu(hm)
        from collections import Counter

        snapshot["child_classes"] = dict(Counter(child_windows(pi.dwProcessId)))

        with open(os.path.join(outdir, "live-snapshot.json"), "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=1)
        print(json.dumps({k: snapshot[k] for k in ("pid", "waited_s")}, indent=1))
        print("windows:", [(e["class"], e["title"], e["visible"]) for e in snapshot["windows"]])
        for k, m in snapshot["menus"].items():
            print("menu:", k, "top-items:", [i.get("label", "sep") for i in m])
    finally:
        kernel32.CloseHandle(job)  # KILL_ON_JOB_CLOSE terminates the process tree

    if pi.hProcess:
        kernel32.WaitForSingleObject(pi.hProcess, 5000)
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)
    return 0


if __name__ == "__main__":
    sys.exit(main())
