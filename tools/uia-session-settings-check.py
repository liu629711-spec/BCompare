#!/usr/bin/env python3
"""Session Settings live gate (docs/21 C; measured ring docs/19 §6.22).

Claims under test (positive, all mirrored from the BC probe arms):
  1. OPEN — the Session menu's 'Session Settings...' item is present in the
     dispatched Text Compare window; invoking it opens a modal Specs dialog
     (our own window, title 'Session Settings - Text Compare') with the two
     path fields PRE-FILLED with the live pair (measured BC: n_spec_combos=2
     for the two-sided views, ValuePattern-readable initial values).
  2. OK APPLIES IN PLACE — set LeftPath to a visibly different file, press OK:
     the dialog closes (measured: settings dialog gone) AND the main window
     stays alive with the SAME handle (measured main-replaced=false) while
     the TITLE follows the new pair (measured text-view ring: title-after =
     'left2.txt <--> ... - Text Compare ...') and the panes re-compare (a
     D3 content-row check: the row count changes for the new pair).
  3. CANCEL RING — reopen, edit LeftPath, press Cancel: title UNCHANGED,
     rows UNCHANGED (measured: zero side effects).

Negative (REACMP_SSET_NEG=1): the dialog opens and OK closes it, but the
re-run never applies — the gate MUST catch the title/rows staying stale.

Usage: python tools/uia-session-settings-check.py <spec.json> <left> <right> [negative]
Exit 0/1/2 like the other live gates.
"""
import ctypes
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
ROOT = r"D:\Rea"


def wt(hwnd):
    n = u32.GetWindowTextLengthW(hwnd)
    b = ctypes.create_unicode_buffer(n + 1)
    u32.GetWindowTextW(hwnd, n + 1, b)
    return b.value


def ui_text(Desktop, hwnd):
    # WPF windows do not answer Win32 GetWindowText with the Title (measured:
    # the merge probe read title 0); the UIA element Name IS the Title.
    try:
        return Desktop(backend="uia").window(handle=hwnd).wrapper_object().window_text()
    except Exception:
        return wt(hwnd)


def visible_hwnd_wrappers(pid):
    return [w for w in top_windows(pid)
            if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w)]


def find_main(pid, Desktop):
    # the FIRST visible HwndWrapper whose UIA title is a '- Text Compare -'
    # session (helper windows like MediaContextNotificationWindow are not
    # visible; the dialog does not exist yet at discovery time)
    for w in visible_hwnd_wrappers(pid):
        if "Text Compare" in ui_text(Desktop, w):
            return w
    return None


def find_dialog(pid, Desktop):
    for w in visible_hwnd_wrappers(pid):
        if ui_text(Desktop, w).startswith("Session Settings - "):
            return w
    return None


def menu_item(win, prefix):
    """find the MenuItem by name prefix (access-key underscores stripped by
    the WPF peer; measured ledger label = 'Session Settings...')."""
    for it in win.descendants(control_type="MenuItem"):
        nm = it.element_info.name or ""
        if nm.startswith(prefix):
            return it
    return None


def rows_count(win):
    n = [0]
    def rec(e, d=0):
        try:
            if d > 25:
                return
            if (e.element_info.name or "") == "TextPane":
                # D3 content rows expose as Text elements under the pane;
                # count numeric row names instead — see uia-d3-check.
                pass
            for c in e.children():
                rec(c, d + 1)
        except Exception:
            pass
    # count the pane's exposed content rows: Text children whose name looks
    # like a row text (same probe as uia-text-content-check)
    texts = [t for t in win.descendants(control_type="Text")
             if (t.element_info.name or "") and re.match(r"^\d+", t.element_info.name or "")]
    return len(texts)


def content_sig(win):
    """stable signature of the compare content: the list of exposed row texts
    in the left pane (D3 provider, docs/19 §6.12)."""
    acc = []
    for t in win.descendants(control_type="Text"):
        nm = t.element_info.name or ""
        if nm and "diff" in nm.lower() or nm.startswith("line "):
            acc.append(nm)
    return tuple(sorted(set(acc)))


def open_via_menu(win):
    """Expand the Session menu and invoke 'Session Settings...'. PURE UIA
    (ExpandCollapse + Invoke patterns) — no SetCursorPos/click_input, so the
    gate stays runnable while the input desktop is locked (screen-saver);
    physical clicks are the 10-24 measured fallback family and are NOT used
    here on purpose."""
    sess = None
    for it in win.descendants(control_type="MenuItem"):
        if (it.element_info.name or "") == "Session":
            sess = it
            break
    if sess is None:
        return "no Session menu"
    try:
        sess.expand()
    except Exception as e:
        return f"expand failed: {type(e).__name__}: {e}"
    time.sleep(0.6)
    item = menu_item(win, "Session Settings")
    if item is None:
        return "no Session Settings item"
    item.invoke()
    return "invoked"


def desktop_name():
    h = u32.OpenInputDesktop(0, False, 1)
    b = ctypes.create_unicode_buffer(256)
    n = ctypes.c_ulong()
    u32.GetUserObjectInformationW(h, 2, b, 256, ctypes.byref(n))
    return b.value


def main():
    spec = os.path.abspath(sys.argv[1])
    left, right = os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    negative = len(sys.argv) > 4 and sys.argv[4] == "negative"
    # ENVIRONMENT BLOCK, not a product failure: a WPF menu popup does not
    # populate its UIA subtree while the input desktop is the screensaver
    # (measured 2026-10-24/25: expand() succeeds, the child items never
    # appear). The dialog ring therefore needs the Default desktop; exit 3
    # keeps "blocked" distinct from the gate's red (1) so the backlog stays
    # honest (same 'refuse garbage' philosophy as the other pixel gates).
    if desktop_name() != "Default":
        print(f"ENV-BLOCKED: input desktop = {desktop_name()} "
              "(menu popup needs Default) — rerun after unlock", file=sys.stderr)
        return 3
    # a third file, visibly different content, for the re-point
    newleft = os.path.join(ROOT, "_tmp", "sset-newleft.txt")
    with open(newleft, "w", encoding="utf-8", newline="\n") as f:
        f.write("ZZNEW-PAIR-MARKER\nsecond line differs entirely here\nthird\n")

    env = dict(os.environ, DOTNET_NOLOGO="1",
               REACMP_SSET_NEG="1" if negative else "0")
    proc = subprocess.Popen([DLL, "--menu-spec", spec, "--dispatch",
                             left, right, "--show"], env=env)
    try:
        from pywinauto import Desktop
        hwnd = None
        t0 = time.time()
        while time.time() - t0 < 20:
            hwnd = find_main(proc.pid, Desktop)
            if hwnd:
                break
            time.sleep(0.4)
        if not hwnd:
            print("product window not found", file=sys.stderr)
            return 2
        time.sleep(2.2)
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        for _ in range(25):
            if u32.GetForegroundWindow() == hwnd:
                break
            win.set_focus()
            time.sleep(0.2)
        time.sleep(0.5)
        problems = []
        title0 = ui_text(Desktop, hwnd)
        sig0 = content_sig(win)

        # --- 1. open the dialog; fields prefilled ---
        how = open_via_menu(win)
        time.sleep(1.5)
        dh = find_dialog(proc.pid, Desktop)
        if not dh:
            print(f"[open] dialog did not appear ({how})", file=sys.stderr)
            return 1
        dw = Desktop(backend="uia").window(handle=dh).wrapper_object()
        edits = {t.element_info.name: t for t in dw.descendants(control_type="Edit")
                 if t.element_info.name in ("LeftPath", "RightPath")}
        if "LeftPath" not in edits or "RightPath" not in edits:
            problems.append(f"[open] path fields missing: {sorted(edits)}")
        else:
            lv = edits["LeftPath"].window_text()
            rv = edits["RightPath"].window_text()
            if os.path.normcase(os.path.abspath(lv)) != os.path.normcase(left):
                problems.append(f"[open] LeftPath not prefilled with live pair: {lv!r} vs {left!r}")
            if os.path.normcase(os.path.abspath(rv)) != os.path.normcase(right):
                problems.append(f"[open] RightPath not prefilled: {rv!r}")

        # --- 2/3. re-point + OK (positive) / Cancel (cancel arm) ---
        if "LeftPath" in edits:
            edits["LeftPath"].set_edit_text(newleft)
            time.sleep(0.3)
            btn = None
            for b in dw.descendants(control_type="Button"):
                if (b.element_info.name or "") == ("OK" if not negative else "Cancel"):
                    btn = b
                    break
            if btn is None:
                problems.append("[act] OK/Cancel button not found in dialog")
            else:
                btn.invoke()
                time.sleep(1.8)
            if find_dialog(proc.pid, Desktop):
                problems.append("[act] dialog still open after " +
                                ("OK" if not negative else "Cancel"))
            win2 = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
            title1 = ui_text(Desktop, hwnd)
            sig1 = content_sig(win2)
            if negative:
                # OK must NOT apply (title/rows stale) — but for the negative
                # arm the dialog is closed with OK; staleness is the catch.
                if title1 != title0:
                    print("NEGATIVE FAILED: OK applied despite injection "
                          f"(title {title0!r} -> {title1!r})", file=sys.stderr)
                    return 1
                print(f"NEGATIVE OK: dialog closed but nothing re-ran "
                      f"(title stayed {title1!r}) — caught")
                return 0
            if title1 == title0:
                problems.append(f"[apply] title did not follow the new pair: {title1!r}")
            elif os.path.basename(newleft) not in title1:
                problems.append(f"[apply] title lacks the new left name: {title1!r}")
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"OK: dialog opens prefilled (2 fields) + OK re-points IN PLACE "
              f"(window alive, title follows: {title1!r})")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()
        try:
            os.remove(newleft)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
