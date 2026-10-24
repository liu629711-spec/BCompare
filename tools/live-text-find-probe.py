#!/usr/bin/env python3
"""Live Find-bar probe (docs/20 §6 step 5, 查找通道侦察).

ONE reference-BCompare launch (Job Object, CREATE_SUSPENDED, strictly serial,
zero residue expected) capturing BC's in-view Find frame behavior that the
static DFM (extracted/forms/TFILEFINDFRAME.dfm: 750x82 dock frame, MRU combo,
RegExp/Case/WholeWords/Wrap AutoCheck speed-buttons, Prev/Next, Sides combo,
Close-automatically) cannot answer:

  step0            initial compare view (control)
  find-open        after Ctrl+F: frame appears; DEFAULT toggle states + Sides
                   default value + focus location
  find-typed       typed 'totally' (matches case-INsensitive in both panes'
                   row 2 text): marks? how many? footer? (marks-all vs
                   current-only question)
  case-on          toggle Match Character Case: marks vanish? (case semantics)
  case-off         restore
  find-next        Enter -> cursor moves: footers + details change (which
                   pane does the cursor live in? both paners' marks sync?)
  find-again       Enter again: wraps? advances? footer
  closed           Escape: frame gone, view restored

Also dumps Toggle/Value pattern state for every control we can read (BC's
filter radios exposed NOTHING via UIA — find toggles may differ; record
whatever is actually exposed, no assumptions).

Usage: python tools/live-text-find-probe.py <BCompare.exe> <outdir> <left> <right>
"""
import ctypes
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_probe_job import (launch, create_kill_job, top_windows, get_class,
                            shutdown)  # noqa: E402
from live_text_px import capture_window  # noqa: E402

u32 = ctypes.windll.user32
VK_F = 0x46
VK_CONTROL = 0x11


def tap_combo():
    u32.keybd_event(VK_CONTROL, 0, 0, 0)
    u32.keybd_event(VK_F, 0, 0, 0)
    time.sleep(0.03)
    u32.keybd_event(VK_F, 0, 2, 0)
    u32.keybd_event(VK_CONTROL, 0, 2, 0)


def tap(vk):
    u32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.03)
    u32.keybd_event(vk, 0, 2, 0)


def pattern_states(el):
    """Toggle/Value/LegacyIAccessible states if the provider exposes them
    (recorded, never assumed — BC filter radios exposed nothing)."""
    st = {}
    try:
        st["toggle"] = int(el.iface_toggle.get_ToggleState())
    except Exception:
        pass
    try:
        st["value"] = el.iface_value.get_Value()
    except Exception:
        pass
    try:
        st["legacy_value"] = el.legacy_iface.Value
    except Exception:
        pass
    try:
        st["legacy_state"] = int(el.legacy_iface.State)
    except Exception:
        pass
    return st


def preorder(el, out, d=0, refs=None):
    if d > 24:
        return
    try:
        ei = el.element_info
        r = el.rectangle()
        cls = ei.class_name or ""
        name = ei.name or ""
        rec = [ei.control_type or "", cls, name,
               [r.left, r.top, r.width(), r.height()]]
        ps = pattern_states(el) if cls in ("TUiSpeedButton", "TUiComboBox",
                                           "TUiCheckBox", "Edit") else {}
        if ps:
            rec.append(ps)
        out.append(rec)
        if refs is not None:
            refs.setdefault(cls, []).append(el)
            if name:
                refs.setdefault("n:" + name, []).append(el)
        for c in el.children():
            preorder(c, out, d + 1, refs)
    except Exception:
        pass


def main():
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    left, right = os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
    prof = os.path.join(outdir, "_profile")
    os.makedirs(prof, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    meta = {"exe": exe}
    job = create_kill_job()
    si, pi = launch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof}, args=[left, right])
    try:
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1F0FFF, False, pi.dwProcessId)
        if not k32.AssignProcessToJobObject(job, h):
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
            meta["error"] = "no TViewForm"
            print(json.dumps(meta))
            return 1
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        win.set_focus()
        time.sleep(1.5)

        def snap(tag):
            refs = {}
            tree = []
            preorder(win, tree, 0, refs)
            json.dump(tree, open(os.path.join(outdir, f"tree-{tag}.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=1)
            img, rect = capture_window(main_h)
            img.save(os.path.join(outdir, f"window-{tag}.png"))
            meta[f"rect-{tag}"] = list(rect)
            return refs

        snap("step0")
        tap_combo()                      # Ctrl+F
        time.sleep(1.5)
        refs1 = snap("find-open")

        # type into the find edit (focus should be there; verify by typing)
        from pywinauto import keyboard
        keyboard.send_keys("totally")
        time.sleep(1.5)
        snap("find-typed")

        # toggle case button by NAME lookup in the open frame
        casebtn = None
        for el in refs1.get("TUiSpeedButton", []):
            try:
                if "case" in (el.element_info.name or "").lower() or \
                   "case" in (el.element_info.control_type or "").lower():
                    casebtn = el
            except Exception:
                pass
        # TUiSpeedButton names were empty in DFM (hint only) — fallback:
        # click by hint tooltip text match via legacy? record what exists:
        hints = {}
        for el in refs1.get("TUiSpeedButton", []):
            try:
                hints[str(el.element_info.name)] = el
            except Exception:
                pass
        meta["speedbutton_names"] = sorted(hints.keys())
        if casebtn is not None:
            casebtn.click_input()
            time.sleep(1.2)
            snap("case-on")
            casebtn.click_input()
            time.sleep(1.2)
            snap("case-off")

        tap(0x0D)                        # Enter = Find Next
        time.sleep(1.2)
        snap("find-next")
        tap(0x0D)
        time.sleep(1.2)
        snap("find-again")

        tap(0x1B)                        # Escape closes the frame
        time.sleep(1.2)
        snap("closed")

        json.dump(meta, open(os.path.join(outdir, "meta.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
        print("done", meta.get("speedbutton_names"))
        return 0
    finally:
        shutdown(job, pi)


if __name__ == "__main__":
    sys.exit(main())
