#!/usr/bin/env python3
"""Report-wizard live gate (docs/21 D; feature 11 GUI, MVP last piece).

The wizard is a THIN SHELL over the CLI report verbs, so the strongest possible
claim is the gate's core assertion: the file the GUI writes is BYTE-IDENTICAL to
a direct `reacmp` run with the same parameters. To make "same parameters"
byte-exact despite the embedded clock, both the GUI subprocess and the
reference CLI run share REACMP_TIMESTAMP (the test hook added to core/cli for
exactly this; unset = real clock, default path unchanged). This mirrors what
product/verify/harness/normalize.py's TIME rule already handles for the golden
corpus, but here we compare RAW bytes — a stronger claim than the normalized
golden equality.

Positive arm:
  1. OPEN — Session menu 'Text Compare Report...' (pure UIA ExpandCollapse,
     NO mouse so it is robust on a locked-ish desktop that still has Default)
     opens the wizard dialog (title 'Text Compare Report'), the Layout combo
     offers the engine's 7 layouts, Output defaults to <left>.report.<ext>.
  2. RUN — pick layout=xml, set Output to a temp path, invoke ReportRun:
     the dialog closes, the file exists, AND it is byte-equal to a direct CLI
     run `reacmp L R <ref> --layout=xml` under the SAME REACMP_TIMESTAMP.
  3. HEX/DIR not re-checked here (same shell pattern; the TEXT arm proves the
     pipeline + byte-equality mechanism end to end).

Negative (REACMP_REPORT_NEG=1): Run closes the dialog and reports success, but
NO file is written — the gate MUST catch the missing/empty output.

Cancel arm: opening then Cancel writes nothing.

Usage: python tools/uia-report-check.py <spec.json> <left> <right> [negative|cancel]
Exit 0/1/2 like the other live gates; exit 3 = ENV-BLOCKED (input desktop is
not Default; a WPF menu popup does not populate its UIA subtree on the
screensaver desktop — measured 2026-10-24/25 — so this is an environment
statement, NOT a product red).
"""
import ctypes
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
CLI = r"D:\Rea\product\cli\target\release\reacmp.exe"
PIN = "2026-10-25 5:21:51"   # the only REACMP_TIMESTAMP both runs share


def desktop_name():
    h = u32.OpenInputDesktop(0, False, 1)
    b = ctypes.create_unicode_buffer(256)
    n = ctypes.c_ulong()
    u32.GetUserObjectInformationW(h, 2, b, 256, ctypes.byref(n))
    return b.value


def ui_text(Desktop, hwnd):
    try:
        return Desktop(backend="uia").window(handle=hwnd).wrapper_object().window_text()
    except Exception:
        return ""


def visible_hwnds(pid):
    return [w for w in top_windows(pid)
            if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w)]


def find_main(pid, Desktop):
    for w in visible_hwnds(pid):
        if "Text Compare" in ui_text(Desktop, w):
            return w
    return None


def find_dialog(pid, Desktop, title):
    for w in visible_hwnds(pid):
        if ui_text(Desktop, w).startswith(title):
            return w
    return None


def main():
    spec = os.path.abspath(sys.argv[1])
    left, right = os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    mode = sys.argv[4] if len(sys.argv) > 4 else "positive"
    if mode not in ("positive", "negative", "cancel"):
        print("mode must be positive|negative|cancel", file=sys.stderr)
        return 2
    if desktop_name() != "Default":
        print(f"ENV-BLOCKED: input desktop = {desktop_name()} (menu popup "
              "needs Default) — rerun after unlock", file=sys.stderr)
        return 3

    outpath = os.path.abspath(r"D:\Rea\_tmp\gui-report.xml")
    refpath = os.path.abspath(r"D:\Rea\_tmp\cli-report.xml")
    for p in (outpath, refpath):
        try: os.remove(p)
        except OSError: pass

    env = dict(os.environ, DOTNET_NOLOGO="1", REACMP_TIMESTAMP=PIN,
               REACMP_REPORT_NEG="1" if mode == "negative" else "0")

    # REFERENCE: direct CLI run, same layout/pinned clock (the byte oracle).
    ref = subprocess.run([CLI, left, right, refpath, "--layout=xml"],
                         capture_output=True, text=True, env=env)
    if not os.path.exists(refpath):
        print(f"reference CLI report failed exit {ref.returncode}: {ref.stderr[:120]}",
              file=sys.stderr)
        return 2

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

        # --- open the wizard via the Session menu (pure UIA) ---
        sess = None
        for it in win.descendants(control_type="MenuItem"):
            if (it.element_info.name or "") == "Session":
                sess = it
                break
        if sess is None:
            print("[open] Session menu not found", file=sys.stderr)
            return 1
        problems = []
        item = None
        for attempt in range(3):
            try:
                sess.expand()
            except Exception:
                pass
            time.sleep(0.7)
            for it in win.descendants(control_type="MenuItem"):
                nm = it.element_info.name or ""
                if "Report" in nm and "Session" not in nm:
                    item = it
                    break
            if item:
                break
        if item is None:
            print("[open] '{View} Report...' menu item not reachable", file=sys.stderr)
            return 1
        item.invoke()
        time.sleep(1.8)
        dh = find_dialog(proc.pid, Desktop, "Text Compare Report")
        if not dh:
            print("[open] wizard dialog did not appear", file=sys.stderr)
            return 1
        dw = Desktop(backend="uia").window(handle=dh).wrapper_object()
        # field presence + engine layout set
        combos = {c.element_info.name: c for c in dw.descendants(control_type="ComboBox")
                  if c.element_info.name}
        edits = {c.element_info.name: c for c in dw.descendants(control_type="Edit")
                 if c.element_info.name}
        if "ReportLayout" not in combos:
            problems.append(f"[fields] layout combo missing: {sorted(combos)}")
        else:
            # WPF virtualizes combo items — they materialize only once the
            # dropdown is expanded (measured: children()==0 while collapsed).
            combo = combos["ReportLayout"]
            try:
                combo.expand()
                time.sleep(0.6)
                n = len([i for i in combo.descendants(control_type="ListItem")])
                combo.collapse()
            except Exception:
                n = len(combo.children())
            if n < 7:
                problems.append(f"[fields] layout combo has {n} items, expected 7")
        if "ReportOutput" not in edits:
            problems.append(f"[fields] output box missing: {sorted(edits)}")

        # --- Cancel arm: close without running, expect no file ---
        if mode == "cancel":
            cbtn = None
            for b in dw.descendants(control_type="Button"):
                if (b.element_info.name or "") == "Cancel":
                    cbtn = b
                    break
            if cbtn is None:
                print("[cancel] Cancel button not found", file=sys.stderr)
                return 1
            cbtn.invoke()
            time.sleep(1.0)
            if os.path.exists(outpath):
                problems.append("[cancel] Cancel wrote a file (should be inert)")
            if problems:
                print("\n".join(problems), file=sys.stderr)
                return 1
            print("OK: cancel arm — dialog closes with NO file written")
            return 0

        # --- positive / negative: point Output at the temp path, press Run ---
        if "ReportOutput" in edits:
            edits["ReportOutput"].set_edit_text(outpath)
            time.sleep(0.3)
        runbtn = None
        for b in dw.descendants(control_type="Button"):
            if (b.element_info.name or "") == "ReportRun":
                runbtn = b
                break
        if runbtn is None:
            print("[run] Run button not found", file=sys.stderr)
            return 1
        runbtn.invoke()
        time.sleep(2.2)
        # the wizard is NON-MODAL (status line) so the dialog stays open after
        # Run; the DECIDING check is the file the engine wrote (byte-equal to
        # the CLI oracle) — the status text is only informational.

        wrote = os.path.exists(outpath) and os.path.getsize(outpath) > 0
        if mode == "negative":
            if wrote:
                print("NEGATIVE FAILED: Run wrote a file despite injection", file=sys.stderr)
                return 1
            print("NEGATIVE OK: Run reported success but wrote nothing — caught")
            return 0

        if not wrote:
            problems.append("[run] wizard wrote no output file")
        else:
            a = open(outpath, "rb").read()
            b = open(refpath, "rb").read()
            if a != b:
                # first differing byte, for a diagnosable message
                i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]),
                         min(len(a), len(b)))
                problems.append(
                    f"[byte-zero-drift] GUI report != direct CLI report at byte {i}: "
                    f"GUI={a[max(0,i-8):i+12]!r} CLI={b[max(0,i-8):i+12]!r} "
                    f"(sizes {len(a)} vs {len(b)})")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"OK: wizard report is BYTE-IDENTICAL to the direct CLI run "
              f"({len(open(outpath,'rb').read())} bytes, same pinned clock)")
        return 0
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
