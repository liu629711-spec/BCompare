"""Shared helpers for live GUI probes (docs/19 §3): Job Object containment,
suspended launch with redirected profile, window/class enumeration, native
menu traversal. Used by live-menu-probe.py and live-uia-probe.py.
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


def launch(exe, env_overrides=None, args=None):
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    pi = PROCESS_INFORMATION()
    cmdline = f'"{exe}"' + (' ' + ' '.join(f'"{a}"' for a in args) if args else '')
    env = None
    if env_overrides:
        base = dict(os.environ)
        base.update(env_overrides)
        # double-NUL terminated block; embedded NULs need create_unicode_buffer,
        # c_wchar_p would truncate at the first '\0'
        block = "\0".join(f"{k}={v}" for k, v in base.items()) + "\0\0"
        env = ctypes.create_unicode_buffer(block)
    ok = kernel32.CreateProcessW(
        exe, cmdline, None, None, False, CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT, env, None, ctypes.byref(si), ctypes.byref(pi)
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




def shutdown(job, pi):
    """Close job (KILL_ON_JOB_CLOSE); hard-terminate if anything survives."""
    k = ctypes.windll.kernel32
    if job:
        k.CloseHandle(job)
    if pi and pi.hProcess:
        if k.WaitForSingleObject(pi.hProcess, 5000) != 0:
            k.TerminateProcess(pi.hProcess, 0)
        k.CloseHandle(pi.hProcess)
        k.CloseHandle(pi.hThread)
