#!/usr/bin/env python3
"""Milestone-tail manual walkthrough (docs/20 §4-4): BC vs LiuCompare
side-by-side evidence over the three MVP full-chain views.

What this AUTOMATES (objective facts only — the judgement layer is the human
looking at the pairs, and this script's whole point is to hand that human
complete evidence):
  * same-content session on both products (shared fixtures);
  * full-window PrintWindow screenshots -> <view>-bc.png / <view>-ours.png;
  * window class/title/rect;
  * brand-line fact: the UIA text tree contains 'Beyond Compare' (BC) /
    'LiuCompare' (ours) — the D1 brand swap reaching every view;
  * menu-item name sets (capabilities parity, per-view);
  * toolbar layer fact (docs/19 §6.21 known gap): BC = icon-only
    TUiSpeedButton faces, ours = text buttons — counted, not interpreted;
  * statusbar text samples.

Serialization: Job Object, one product at a time, zero residue (Oracle
single-instance rule). Screenshots need the DEFAULT input desktop (PrintWindow
paints the backbuffer fine, but WPF menu popups/UIA fills need render — same
precheck family as the dialog gates).

Usage: python tools/live-walkthrough.py <BCompare.exe> [views]
  views = comma list of text,folder,hex (default: all three)
"""
import ctypes
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (create_kill_job, shutdown, top_windows,  # noqa: E402
                            get_class)

u32 = ctypes.windll.user32
g32 = ctypes.windll.gdi32
k32 = ctypes.windll.kernel32
ROOT = r"D:\Rea"
OUT = os.path.join(ROOT, "extracted", "live", "walkthrough-en")
OUR_EXE = os.path.join(ROOT, r"product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe")
SPEC = os.path.join(ROOT, r"product\gui\spec\menu-spec.json")
PW_RENDERFULLCONTENT = 2


class RECT(ctypes.Structure):
    _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long),
                ("r", ctypes.c_long), ("b", ctypes.c_long)]


class BIH(ctypes.Structure):
    _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32)]


def desktop_name():
    h = u32.OpenInputDesktop(0, False, 1)
    b = ctypes.create_unicode_buffer(256)
    n = ctypes.c_ulong()
    u32.GetUserObjectInformationW(h, 2, b, 256, ctypes.byref(n))
    return b.value


def capture_window(hwnd):
    from PIL import Image
    r = RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.r - r.l, r.b - r.t
    hdc = u32.GetWindowDC(hwnd)
    try:
        mem = g32.CreateCompatibleDC(hdc)
        bmp = g32.CreateCompatibleBitmap(hdc, w, h)
        old = g32.SelectObject(mem, bmp)
        u32.PrintWindow(hwnd, mem, PW_RENDERFULLCONTENT)
        bmi = BIH()
        bmi.biSize = ctypes.sizeof(BIH)
        bmi.biWidth, bmi.biHeight = w, -h
        bmi.biPlanes, bmi.biBitCount, bmi.biCompression = 1, 32, 0
        buf = ctypes.create_string_buffer(w * h * 4)
        g32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bmi), 0)
        g32.SelectObject(mem, old)
        g32.DeleteObject(bmp)
        g32.DeleteDC(mem)
        return Image.frombytes("RGB", (w, h), buf.raw, "raw", "BGRX"), \
            [r.l, r.t, w, h]
    finally:
        u32.ReleaseDC(hwnd, hdc)


def pid_of(hwnd):
    pid = ctypes.c_ulong()
    u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def win_text(hwnd, Desktop):
    try:
        return Desktop(backend="uia").window(handle=hwnd).wrapper_object().window_text() or ""
    except Exception:
        n = u32.GetWindowTextLengthW(hwnd)
        b = ctypes.create_unicode_buffer(n + 1)
        u32.GetWindowTextW(hwnd, n + 1, b)
        return b.value


def plaunch(exe, env_over, args):
    import live_probe_job as lpj
    base = dict(os.environ)
    base.update(env_over)
    envbuf = ctypes.create_unicode_buffer(
        "".join(f"{k}={v}\0" for k, v in base.items()) + "\0")
    cl = '"{}"'.format(exe) + ("".join(' "{}"'.format(a) for a in args) if args else "")
    s = lpj.STARTUPINFO()
    s.cb = ctypes.sizeof(lpj.STARTUPINFO)
    p = lpj.PROCESS_INFORMATION()
    ok = k32.CreateProcessW(exe, cl, None, None, False,
                            0x4 | 0x0400,  # CREATE_SUSPENDED | UNICODE
                            envbuf, None, ctypes.byref(s), ctypes.byref(p))
    if not ok:
        raise ctypes.WinError()
    return s, p


def grab(exe, args, prof, title_contains, png, ours, Desktop):
    """launch → wait for the session window → settle → screenshot + facts"""
    os.makedirs(prof, exist_ok=True)
    job = create_kill_job()
    si, pi = plaunch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof,
                           "DOTNET_NOLOGO": "1"}, args)
    try:
        h = k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)
        k32.AssignProcessToJobObject(job, h)
        k32.ResumeThread(pi.hThread)
        pid = pi.dwProcessId
        hwnd = None
        t0 = time.time()
        while time.time() - t0 < 30:
            for w in top_windows(pid):
                if u32.IsWindowVisible(w) and title_contains in win_text(w, Desktop):
                    hwnd = w
                    break
            if hwnd:
                break
            time.sleep(0.5)
        if not hwnd:
            return {"error": "window not found"}
        time.sleep(4.0)   # engine + paint + (BC) license dialogs settle
        try:
            u32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        time.sleep(0.8)
        img, rect = capture_window(hwnd)
        img.save(png)
        facts = harvest(pid, hwnd, Desktop)
        facts.update({"class": get_class(hwnd), "title": win_text(hwnd, Desktop),
                      "rect": rect, "png": os.path.basename(png)})
        return facts
    finally:
        shutdown(job, pi)


def harvest(pid, hwnd, Desktop):
    """UIA facts: brand line, menu names, toolbar layer counts, statusbar."""
    out = {"brand": False, "menu_items": [], "toolbar": {}, "statusbar": []}
    try:
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
    except Exception as e:
        return {"error": "uia-fail:" + type(e).__name__}
    texts = []
    def rec(e, d=0):
        if d > 14 or len(texts) > 2000:
            return
        try:
            ei = e.element_info
            if ei.name:
                texts.append((ei.control_type or "", ei.name))
            for c in e.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    low = " | ".join(t for (_, t) in texts).lower()
    out["brand"] = ("beyond compare" in low) or ("liucompare" in low)
    out["menu_items"] = sorted({t for (ct, t) in texts if ct == "MenuItem"})
    # toolbar layer: BC = TUiSpeedButton/BitsButton window classes (win32
    # side), ours = ChromeElement text faces; count by exposed Button/Text
    btns = [t for (ct, t) in texts if ct == "Button"]
    out["toolbar"] = {"buttons_named": len([b for b in btns if b]),
                      "buttons_total": len(btns)}
    out["statusbar"] = [t for (ct, t) in texts
                        if ct == "Text" and (") free on" in t or "file(s)" in t
                        or ": 1" in t and len(t) < 12)][:12]
    return out


def main():
    bc = os.path.abspath(sys.argv[1])
    which = (sys.argv[2].split(",") if len(sys.argv) > 2 else ["text", "folder", "hex"])
    if desktop_name() != "Default":
        print(f"ENV-BLOCKED: input desktop = {desktop_name()}", file=sys.stderr)
        return 3
    from pywinauto import Desktop
    os.makedirs(OUT, exist_ok=True)   # NEVER rmtree: incremental re-runs of
    # one view must not wipe the other views' PNGs + meta facts (measured:
    # an earlier version did, losing the text/folder evidence layer).
    fx = os.path.join(ROOT, "_tmp", "walkthrough-fx")
    os.makedirs(fx, exist_ok=True)
    lt, rt = os.path.join(fx, "wt-L.txt"), os.path.join(fx, "wt-R.txt")
    open(lt, "w", encoding="utf-8", newline="\n").write(
        "HEAD line\nbeta\nTOTALLY other words here\ncommon four\nalpha five\n")
    open(rt, "w", encoding="utf-8", newline="\n").write(
        "HEAD line\nbeta\nTOTALLY missing here\ncommon four\nomega five\nextra tail\n")
    dl, dr = os.path.join(fx, "dirL"), os.path.join(fx, "dirR")
    shutil.rmtree(dl, ignore_errors=True)
    shutil.rmtree(dr, ignore_errors=True)
    os.makedirs(dl)
    os.makedirs(dr)
    open(os.path.join(dl, "same.txt"), "w").write("same\n")
    open(os.path.join(dr, "same.txt"), "w").write("same\n")
    open(os.path.join(dl, "leftonly.txt"), "w").write("L only content here\n")
    open(os.path.join(dr, "modified.txt"), "w").write("v2 content changed\n")
    open(os.path.join(dl, "modified.txt"), "w").write("v1 content original\n")
    L = list(range(0x00, 0x30))
    L[8:12] = [0xAA, 0xBB, 0xCC, 0xDD]
    L += [0x30, 0x31, 0x32, 0x33]
    R = list(range(0x00, 0x30))
    R[8:12] = [0x11, 0x22, 0x33, 0x44]
    R += [0xF0, 0xF1]
    hl, hr = os.path.join(fx, "wt-L.bin"), os.path.join(fx, "wt-R.bin")
    open(hl, "wb").write(bytes(L))
    open(hr, "wb").write(bytes(R))

    # the BC sandbox profile lives OUTSIDE the evidence tree (temp), so
    # nothing personal ever lands in extracted/live/ — measured lesson: the
    # .gitignore rule is "*_profile/", a dir literally named _prof escaped it.
    prof = os.path.join(os.environ.get("TEMP", ROOT), "reacmp-walkthrough-prof")
    # the BC sandbox profile out of the evidence tree (repo convention).
    META = os.path.join(OUT, "walkthrough-meta.json")
    # merge into any existing meta (single-view reruns keep the other views)
    report = {"date": "2026-10-25",
              "purpose": "docs/20 §4-4 milestone-tail walkthrough (automated "
              "evidence layer; judgement = the human pass over the PNG pairs)",
              "views": {}}
    if os.path.exists(META):
        try:
            old = json.load(open(META, encoding="utf-8"))
            report["views"] = old.get("views", {})
        except Exception:
            pass
    VIEWS = {
        "text":   ([lt, rt], [lt, rt], "Text Compare", "Text Compare"),
        "folder": ([dl, dr], [dl, dr], "Folder Compare", "Folder Compare"),
        "hex":    ([hl, hr], [hl, hr], "Hex Compare", "Hex Compare"),
        # BC title for the hex view is '{L} <--> {R} - Hex Compare - Beyond
        # Compare' (extracted/live/hexview-en/hexview-meta.json, measured).
    }
    for v in which:
        bc_args, our_args, bc_title, our_title = VIEWS[v]
        row = {}
        row["bc"] = grab(bc, bc_args, prof, bc_title,
                         os.path.join(OUT, f"{v}-bc.png"), False, Desktop)
        row["ours"] = grab(OUR_EXE, ["--menu-spec", SPEC, "--dispatch"]
                           + our_args + ["--show"], prof, our_title,
                           os.path.join(OUT, f"{v}-ours.png"), True, Desktop)
        for side in ("bc", "ours"):
            f = row[side]
            f.pop("error", None) if "png" in f else f.setdefault("error", "no shot")
        report["views"][v] = row
        print(v, "->", json.dumps(
            {s: (row[s].get("error") or "ok " + str(row[s].get("rect")))
             for s in ("bc", "ours")}, ensure_ascii=False))
    json.dump(report, open(os.path.join(OUT, "walkthrough-meta.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved ->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
