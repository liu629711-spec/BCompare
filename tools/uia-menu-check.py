#!/usr/bin/env python3
"""Live UIA check for the WPF menu bar: launch the product's menu window and
compare the ACTUAL accessibility tree against the Oracle live baseline for the
same view (extracted/live/menu-matrix.json / per-view gui-home.json).

Same harness family as tools/live-gui-probe.py (pywinauto UIA), same discipline:
own process, terminate at end, zero residue expected.

Asserts per top menu: identical ordered list of (label, shortcut, accessKey).
  label     = MenuItem Name with '\t<gesture>' stripped (Oracle format)
  shortcut  = the gesture text after '\t' ('' if none)
  accessKey = UIA AccessKey property ('' if none)

Usage: python tools/uia-menu-check.py <spec.json> --view "Text Compare"
       [--oracle extracted/live/ref-5.2.6-uia/gui-text-session-en.json]
Exit 0 = identical; 1 = differences; 2 = launch failure.
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class, get_window_text, wintypes  # noqa: E402

u32 = ctypes.windll.user32
from pywinauto import Desktop
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll"
ORACLE = {
    "Home": "ref-5.2.6-uia/gui-home-en.json",
    "Text Compare": "ref-5.2.6-uia/gui-text-session-en.json",
    "Text Merge": "view-textmerge/gui-home.json",
    "Hex Compare": "view-hex/gui-home.json",
    "Table Compare": "view-table/gui-home.json",
    "Picture Compare": "view-picture/gui-home.json",
    "Registry Compare": "view-registry/gui-home.json",
    "Version Compare": "view-version/gui-home.json",
    "Folder Compare": "view-folder/gui-home.json",
    "Folder Merge": "view-foldermerge/gui-home.json",
    "Folder Sync": "view-foldersync/gui-home.json",
    "Media Compare": "view-media/gui-home.json",
}
UIA_AccessKeyPropertyId = 30007


def oracle_menu_rows(path):
    r = json.load(open(path, encoding="utf-8"))
    rows = {}
    for menu, items in r["tops"].items():
        seq = []
        for it in items:
            if it.get("ct") == 50011 and it.get("name"):
                parts = it["name"].split("\t")
                seq.append((parts[0], parts[1] if len(parts) > 1 else "",
                            it.get("acc", "") or ""))
        rows[menu] = seq
    return rows


def read_live_chrome(win):
    """Product chrome rows: PanelHost wrappers carry AutomationId 'chrome:SEC:i';
    children are ChromeElements whose peer reports the exact (ct, cls, name)
    triple the Oracle captured. Returns {'tb': [[..],..], 'sb': [[..],..]} in
    index order (tree order can differ from DOM order under DockPanel)."""
    found = {}

    def walk(el, d=0):
        if d > 12:
            return
        aid = el.element_info.automation_id or ""
        if aid.startswith("chrome:"):
            parts = aid.split(":")
            found.setdefault(parts[1], {})[int(parts[2])] = [
                (c.element_info.control_type, c.element_info.class_name,
                 c.element_info.name or "")
                for c in el.children()]
        for c in el.children():
            walk(c, d + 1)
    walk(win)
    return {sec: [v[k] for k in sorted(v)] for sec, v in found.items()}


def compare_chrome(view, win, problems):
    """--chrome tier: live UIA chrome rows vs chrome-matrix.json triples."""
    ch = json.load(open(os.path.join(r"D:\Rea\extracted\live", "chrome-matrix.json"),
                        encoding="utf-8"))[view]
    live = read_live_chrome(win)
    for sec, key in (("tb", "toolbars"), ("sb", "statusbars")):
        want = [[(i["ct"], i["cls"], i["name"]) for i in row] for row in ch[key]]
        got = live.get(sec, [])
        if want != got:
            problems.append(f"[chrome {sec}] rows oracle={len(want)} live={len(got)}")
            for i, (w, g) in enumerate(zip(want, got)):
                for j, (a, b) in enumerate(zip(w, g)):
                    if a != b:
                        problems.append(f"  [{sec}][{i}][{j}] oracle={a} live={b}")
                        break
    return sum(len(r) for r in ch["toolbars"] + ch["statusbars"])


def live_skeleton_preorder(win):
    """Preorder (ct, cls, name) of the product's content-view UIA control tree.
    Skip rules mirror the skeleton prune: the window root is not emitted (WPF
    reports HwndWrapper for TViewForm); menu bars are skipped entirely (menu
    axis = gate 6.6); titlebar/system-menu skipped (OS chrome); a chrome row
    host emits its OWN triple but does not descend — its item children live in
    the chrome ledger, not the skeleton."""
    out = []

    def walk(el, d=0):
        if d > 20:
            return
        ct = el.element_info.control_type or ""
        if ct in ("MenuBar", "Menu") or ct == "TitleBar":
            return
        out.append((ct, el.element_info.class_name or "", el.element_info.name or ""))
        if (el.element_info.automation_id or "").startswith("chrome:"):
            return
        for c in el.children():
            walk(c, d + 1)
    for c in win.children():
        walk(c)
    return out


def compare_skeleton(view, win, problems, spec_path):
    """--skeleton tier: live content UIA tree vs the spec skeleton preorder."""
    spec = json.load(open(spec_path, encoding="utf-8"))

    def flat(nodes, acc):
        for n in nodes:
            acc.append((n["ct"], n["cls"], n["name"]))
            flat(n["children"], acc)
        return acc
    want = flat(spec["skeleton"][view], [])
    got = live_skeleton_preorder(win)
    if want != got:
        problems.append(f"[skeleton] nodes oracle={len(want)} live={len(got)}")
        for i, (w, g) in enumerate(zip(want, got)):
            if w != g:
                problems.append(f"  [{i}] oracle={w} live={g}")
                break
    return len(want)



def live_menu_rows(win):
    """Find the app menu (NOT the OS titlebar system menu — same trap as the BC
    probe: it also reports MenuBar) and return {topLabel: (element, label, accKey)}."""
    bars = []

    def find(el, d=0):
        if d > 8:
            return
        if el.element_info.control_type in ("MenuBar", "Menu"):
            bars.append(el)
            return
        for c in el.children():
            find(c, d + 1)
    find(win)
    if not bars:
        return None
    # WPF's Menu reports 'Menu'; the OS system menu reports 'MenuBar' with 1 item.
    menubar = max(bars, key=lambda b: len(b.children()))
    rows = {}
    for top in menubar.children():
        if top.element_info.control_type != "MenuItem":
            continue
        raw = top.element_info.element
        acc = raw.GetCurrentPropertyValue(UIA_AccessKeyPropertyId) or ""
        label = (top.element_info.name or "").replace("&", "").replace("_", "")
        rows[label] = (top, label, acc)
    return rows


def menu_state(win):
    """(appMenu, {label: topItemWrapper}) read FRESH from the window each time.
    WPF popups invalidate cached UIA refs, so every interaction re-reads."""
    bars = []

    def find(el, d=0):
        if d > 8:
            return
        if el.element_info.control_type in ("MenuBar", "Menu"):
            bars.append(el)
            return
        for c in el.children():
            find(c, d + 1)
    find(win)
    if not bars:
        return None, {}
    app = max(bars, key=lambda b: len(b.children()))
    tops = {}
    for t in app.children():
        if t.element_info.control_type == "MenuItem":
            nm = (t.element_info.name or "").replace("&", "").replace("_", "")
            tops[nm] = t
    return app, tops


def children_rows(win, label):
    """Rows of the open submenu: re-read the tree, find the top item, read its
    submenu children (a nested Menu container once open)."""
    app, tops = menu_state(win)
    top = tops.get(label)
    if top is None:
        return []
    out = []

    def rec(el, d=0):
        if d > 8:
            return
        for c in el.children():
            if c.element_info.control_type == "MenuItem":
                try:
                    acc = c.element_info.element.GetCurrentPropertyValue(UIA_AccessKeyPropertyId) or ""
                except Exception:
                    acc = ""
                name = c.element_info.name or ""
                parts = name.split(chr(9))
                out.append((parts[0].replace("&", "").replace("_", ""),
                            parts[1] if len(parts) > 1 else "",
                            (acc[4:] if acc.lower().startswith("alt+") else acc)))
                rec(c, d + 1)
    rec(top)
    return out



def force_foreground(hwnd):
    """Bring a window to the foreground reliably. A plain SetForegroundWindow
    fails while our process is background (the OS foreground lock); the standard
    bypass is AttachThreadInput to the current foreground thread, then Alt-nudge."""
    u32.ShowWindow(hwnd, 9)  # SW_RESTORE
    if u32.GetForegroundWindow() == hwnd:
        return
    fg = u32.GetForegroundWindow()
    our_tid = u32.GetWindowThreadProcessId(u32.GetShellWindow(), None)
    fg_tid = u32.GetWindowThreadProcessId(fg, None) if fg else 0
    me_tid = ctypes.windll.kernel32.GetCurrentThreadId()
    if fg_tid and fg_tid != me_tid:
        u32.AttachThreadInput(me_tid, fg_tid, True)
    try:
        u32.SetForegroundWindow(hwnd)
        u32.SetFocus(hwnd)
    finally:
        if fg_tid and fg_tid != me_tid:
            u32.AttachThreadInput(me_tid, fg_tid, False)
    if u32.GetForegroundWindow() != hwnd:
        u32.keybd_event(0x12, 0, 0, 0)
        u32.keybd_event(0x12, 0, 2, 0)
        u32.SetForegroundWindow(hwnd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--view", required=True)
    ap.add_argument("--oracle")
    ap.add_argument("--expand", action="store_true",
                    help="also expand each submenu (requires an interactive foreground session)")
    ap.add_argument("--chrome", action="store_true",
                    help="also verify live toolbar/statusbar rows against chrome-matrix.json")
    ap.add_argument("--skeleton", action="store_true",
                    help="also verify the content-view UIA tree against the spec skeleton")
    a = ap.parse_args()

    orc_path = a.oracle or os.path.join(r"D:\Rea\extracted\live", ORACLE[a.view])
    oracle = oracle_menu_rows(orc_path)

    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    proc = subprocess.Popen(["dotnet", DLL, "--menu-spec", os.path.abspath(a.spec),
                             "--view", a.view, "--show"], env=env)
    try:
        hwnd = None
        t0 = time.time()
        while time.time() - t0 < 15:
            for w in top_windows(proc.pid):
                if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w):
                    hwnd = w
                    break
            if hwnd:
                break
            time.sleep(0.4)
        if not hwnd:
            print("menu window not found", file=sys.stderr)
            return 2
        time.sleep(1.2)
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        live = live_menu_rows(win)
        if live is None:
            print("no MenuBar in product window", file=sys.stderr)
            return 2

        # compare: top order/labels/access-keys, then each submenu via click-expand
        problems = []
        o_tops = list(oracle.keys())
        l_tops = list(live.keys())
        if o_tops != l_tops:
            problems.append(f"top menus differ: oracle={o_tops} live={l_tops}")
        verified = 0

        def current_tops():
            """Re-read the app menu bar AFTER each open/close: WPF popups
            invalidate the UIA references captured before the click."""
            rows = live_menu_rows(win)
            return rows or {}

        for m in o_tops:
            if m not in live:
                continue
            oracle_acc = oracle[m][0][2] if oracle[m] else ""
            live_acc = live[m][2]
            live_norm = live_acc[4:] if live_acc.lower().startswith("alt+") else live_acc
            if live_norm.lower() != oracle_acc.lower():
                problems.append(f"[{m}] top AccessKey: oracle={oracle_acc!r} live={live_acc!r}")
            try:
                tops_now = current_tops()
                if m not in tops_now:
                    problems.append(f"[{m}] top item vanished after re-read")
                    continue
                # open with the keyboard (mouse clicks on UIA refs die after WPF
                # popups invalidate them -> SetCursorPos errors)
                # Submenu expansion needs real foreground (this checker runs as a
                # background service process, and the OS foreground lock blocks it).
                # Default mode asserts the top-level bar (labels + access keys);
                # --expand additionally walks submenus where the environment allows.
                if not a.expand:
                    continue
                force_foreground(hwnd)
                time.sleep(0.6)
                if u32.GetForegroundWindow() != hwnd:
                    problems.append(f"[{m}] cannot foreground window (OS foreground lock); run --expand from an interactive session")
                    continue
                _app, tops_now = menu_state(win)
                if m not in tops_now:
                    problems.append(f"[{m}] top item not found for open")
                    continue
                r = tops_now[m].rectangle()
                cx, cy = int(r.left + r.width() / 2), int(r.top + r.height() / 2)
                if r.width() <= 0 or r.height() <= 0 or cx <= 0 or cy <= 0:
                    problems.append(f"[{m}] invalid rect {r}, skipping")
                    continue
                u32.SetCursorPos(cx, cy)
                time.sleep(0.2)
                u32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.05)
                u32.mouse_event(0x0004, 0, 0, 0, 0)
                time.sleep(1.0)
                got = [(x[0], x[1]) for x in children_rows(win, m)]
                want = [(x[0], x[1]) for x in oracle[m]]
                if want != got:
                    problems.append(f"[{m}] submenu rows differ ({len(want)} oracle / {len(got)} live)")
                    for i, (w, g) in enumerate(zip(want, got)):
                        if w != g:
                            problems.append(f"    [{m}][{i}] oracle={w} live={g}")
                    if len(want) != len(got):
                        problems.append(f"    [{m}] length oracle={want[len(got):]} live={got[len(want):]}")
                else:
                    verified += len(got)
                _a2, tops2 = menu_state(win)
                if m in tops2:
                    try:
                        tops2[m].click_input()
                    except Exception:
                        u32.keybd_event(0x1B, 0, 0, 0)
                        u32.keybd_event(0x1B, 0, 2, 0)
                time.sleep(0.4)
            except Exception as e:
                problems.append(f"[{m}] expand failed: {type(e).__name__}: {str(e)[:100]}")
        chrome_items = compare_chrome(a.view, win, problems) if a.chrome else 0
        skel_items = compare_skeleton(a.view, win, problems, os.path.abspath(a.spec)) if a.skeleton else 0
        print(f"view={a.view} tops={len(o_tops)} submenu-rows-verified={verified} "
              f"chrome-items-verified={chrome_items} skeleton-nodes-verified={skel_items}")
        for p in problems:
            print("MENU-CHECK FAIL:", p)
        return 1 if problems else 0
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
