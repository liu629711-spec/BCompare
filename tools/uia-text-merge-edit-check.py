#!/usr/bin/env python3
"""Live Text Merge EDIT + SAVE gate (docs/19 §6.17 semantics, tier-2 GUI).

Claims under test (positive) — all traced to merge-edit-findings.json:
  1. OPEN does NOT write the save target (measured Q2: OUT_after_step0 ==
     preset). Preset sentinel 'PRESETPANE_LINE_A' must stay on disk.
  2. OUTPUT INITIAL = AUTO-MERGE (measured Q1): after save the file shows
     the base's lines (unresolved conflict holds center), NOT the preset.
  3. TYPING does NOT write (measured Q2 again): the marker lives in the
     document only until an explicit Ctrl+S.
  4. Ctrl+S writes DIRECTLY (named target -> no dialog; measured): the file
     now holds auto-merge + marker; byte shape = LF joins, no trailing
     newline, no BOM (measured OUT_after_ctrl_s verbatim).

Negative (REACMP_MERGE_SAVE_NEG=1): Ctrl+S silently no-ops — the gate must
catch the file STILL holding the preset sentinel.

Usage: python tools/uia-text-merge-edit-check.py <spec.json> <L> <R> <C> [negative]
A throwaway OUT copy is created under _tmp for each run (nothing user-owned
is touched).
"""
import ctypes
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import top_windows, get_class  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.exe"
MARKER = "ZZGATEMARKER42"
PRESET = "PRESETPANE_LINE_A\nPRESETPANE_LINE_B\n"


def find_output(win):
    hit = []

    def rec(n, d=0):
        try:
            if d > 22:
                return
            if (n.element_info.class_name or "") == "MergeOutput":
                hit.append(n)
                return
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return hit[0] if hit else None


def main():
    spec = os.path.abspath(sys.argv[1])
    L, R, C = (os.path.abspath(sys.argv[i]) for i in (2, 3, 4))
    negative = len(sys.argv) > 5 and sys.argv[5] == "negative"
    OUT = os.path.abspath(r"D:\Rea\_tmp\merge-edit-target.txt")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(PRESET)

    def read():
        try:
            return open(OUT, encoding="utf-8", errors="replace").read()
        except Exception as e:
            return f"<ERR {e}>"

    env = dict(os.environ, DOTNET_NOLOGO="1",
               REACMP_MERGE_SAVE_NEG="1" if negative else "0")
    proc = subprocess.Popen([DLL, "--menu-spec", spec, "--merge",
                             L, R, C, OUT, "--show"], env=env)
    try:
        hwnd = None
        t0 = time.time()
        while time.time() - t0 < 20:
            for w in top_windows(proc.pid):
                if get_class(w).startswith("HwndWrapper") and u32.IsWindowVisible(w):
                    hwnd = w
                    break
            if hwnd:
                break
            time.sleep(0.4)
        if not hwnd:
            print("product window not found", file=sys.stderr)
            return 2
        time.sleep(2.4)
        from pywinauto import Desktop, keyboard, mouse
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        for _ in range(25):
            if u32.GetForegroundWindow() == hwnd:
                break
            win.set_focus()
            time.sleep(0.2)
        time.sleep(0.4)
        problems = []

        # --- 1. open must NOT touch the target (measured Q2) ---
        if read() != PRESET:
            problems.append(f"[open-no-write] target mutated by opening: {read()[:60]!r}")

        out = find_output(win)
        if out is None:
            print("[geometry] MergeOutput pane not found", file=sys.stderr)
            return 1
        r = out.rectangle()
        pitch = 15
        # click BELOW the content (void area) -> caret lands on a fresh last
        # line, mirroring the measured probe placement ('...eight\n<MARKER>').
        # click_input + win.type_keys (NOT mouse.click + global send_keys):
        # physical clicks steal the foreground on this host (§6.14 lesson)
        # and global keypost then lands in the wrong window — that is exactly
        # why the first run of this gate saw no marker and no Ctrl+S write.
        out.click_input(coords=(r.width() // 2, 8 * pitch + 2))
        time.sleep(0.6)

        # --- 2/3. typing must NOT write (measured Q2) ---
        win.type_keys(MARKER, set_foreground=True, pause=0.05)
        time.sleep(1.0)
        if MARKER in read():
            problems.append("[typing-no-write] file written WITHOUT Ctrl+S — "
                            "measured rule is explicit-save-only")

        # --- 4. Ctrl+S: direct write, measured byte shape ---
        win.type_keys("^s", set_foreground=True, pause=0.05)
        time.sleep(1.4)
        saved = read()

        if negative:
            if MARKER in saved and "PRESETPANE" not in saved:
                print("NEGATIVE FAILED: Ctrl+S wrote despite injection", file=sys.stderr)
                return 1
            print(f"NEGATIVE OK: Ctrl+S did not write (target still "
                  f"{saved[:40]!r}) — caught")
            return 0

        if MARKER not in saved:
            problems.append(f"[ctrl-s] marker missing after save: {saved[:80]!r}")
        if "PRESETPANE" in saved:
            problems.append("[ctrl-s] target content leaked (measured Q1: "
                            "output = auto-merge, never the target's disk content)")
        if "line one" not in saved or "line eight" not in saved:
            problems.append(f"[ctrl-s] auto-merge body missing: {saved[:80]!r}")
        if "\r" in saved:
            problems.append("[byte shape] CR found — measured save uses LF joins")
        if saved.endswith("\n"):
            problems.append("[byte shape] trailing newline added — measured "
                            "bytes end verbatim ('...eight\\nZZEDITMARKER7')")
        if saved.startswith("\ufeff"):
            problems.append("[byte shape] BOM found — measured UTF-8 no BOM")

        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("OK: open/typing never write (explicit-save rule) + Ctrl+S writes "
              "auto-merge+marker, LF-joined, no BOM, no trailing newline")
        return 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=8)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
