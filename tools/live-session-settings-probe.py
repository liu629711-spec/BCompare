#!/usr/bin/env python3
"""Session Settings OK-behavior probe (docs/21 C; the one open fork).

Already anchored (R4-dialog): TSessionDialog 599x602, four Tabs, Specs frame
has 4 TUiSpecComboBox (top order y=257 Left / 339 Right / 421 Center /
504 Output), each with an inner Edit + a 'open' browse Button; OK=TUiOkBtn
'name=OK', Cancel=TUiCancelBtn.

UNMEASURED and design-deciding: after editing a Specs path and pressing OK,
does BC RE-COMPARE in place (title / left-pane pixels / status bar change),
RESET the output, or do nothing until an explicit Reload Files? And does
Cancel truly discard? (docs/21 risk bar: no guessing — probe first.)

Two serial launches (Job Object, CREATE_SUSPENDED, temp profile, zero residue):
  mode=ok      open dialog -> set Left Edit to left2.txt (visibly different
               first line) -> OK -> capture main title + full-window screenshot
               + statusbar + dialog-still-open?
  mode=cancel  same edit -> Cancel -> expect NO change (baseline == post)

The left pane of a Text Merge is pixel-only (source panes expose no UIA text,
docs/19 §6.15/§6.17), so the re-compare signal is the LEFT PANE SCREENSHOT
region diff vs the baseline, plus the title/statusbar text which ARE readable.

Usage: python tools/live-session-settings-probe.py <BCompare.exe> <outdir> <ok|cancel>
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
IGN = ("TViewForm", "TApplication", "TUiMainMenu", "#32768",
       "TTBPopupWindow", "SysShadow", "Default IME",
       "MediaContextNotificationWindow", "SystemResourceNotifyWindow",
       "TabletPenServiceHelperClass", "IME", "HwndWrapper")


def preorder(el, out, d=0):
    try:
        ei = el.element_info
        r = el.rectangle()
        out.append([ei.control_type or "", ei.class_name or "", ei.name or "",
                    [r.left, r.top, r.width(), r.height()]])
        if d < 24:
            kids = []
            for c in el.children():
                preorder(c, kids, d + 1)
            out[-1].extend(kids)
    except Exception:
        pass


def fixtures(d):
    base = [f"line {w}" for w in ("one", "two", "three", "four", "five",
                                  "six", "seven", "eight")]
    def w(name, lines):
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
        return p
    left = list(base)
    left[0] = "LEFT-ONE-ORIGINAL"
    right = list(base)  # right == base: line 0 is a clean take-left, NOT a
    # conflict — the re-compare signal stays unambiguous (left pane row 0 text
    # changes when Left path is re-pointed).
    # left2: first line VISIBLY different -> a re-compare changes the left pane
    left2 = list(base)
    left2[0] = "NEWLEFT-ZZZ-REPLACED-ONE"
    return (w("left.txt", left), w("right.txt", right), w("base.txt", base),
            w("left2.txt", left2))


def visible_nonmain(pid):
    out = []
    for w in top_windows(pid):
        if not u32.IsWindowVisible(w):
            continue
        cls = get_class(w)
        if cls in IGN:
            continue
        out.append([cls, get_window_text(w), w])
    return out


def statusbar_texts(win):
    acc = []
    def rec(n, d=0):
        try:
            if d > 22:
                return
            ei = n.element_info
            if (ei.control_type or "") == "Text" and ei.name:
                acc.append(ei.name)
            for c in n.children():
                rec(c, d + 1)
        except Exception:
            pass
    rec(win)
    return acc


def set_combo_text(combo, text):
    """Put `text` into a TUiSpecComboBox's inner Edit. VCL combo: set_edit_text
    (WM_SETTEXT, bypasses ValuePattern) is the primary route; the value often
    does NOT read back through UIA, so the caller must confirm visually via
    the dialog screenshot — a read-back of '' does NOT mean the write failed."""
    edit = None
    for c in combo.descendants(control_type="Edit"):
        edit = c
        break
    if edit is None:
        return "no-edit"
    try:
        edit.set_edit_text(text)
        return "set_edit_text->read:" + (edit.window_text() or "<empty>")
    except Exception as e:
        pass
    try:
        edit.click_input()
        time.sleep(0.2)
        edit.type_keys("^a{BACKSPACE}", set_foreground=True, pause=0.03)
        edit.type_keys(text.replace("+", "++").replace("%", "%%")
                           .replace("^", "^^").replace("(", "^(")
                           .replace(")", "^)").replace("{", "^{")
                           .replace("}", "^}"),
                       set_foreground=True, pause=0.02)
        return "typed->read:" + (edit.window_text() or "<empty>")
    except Exception as e:
        return "err:" + str(e)


def run(exe, od, mode):
    L, R, C, L2 = fixtures(od)
    OUT = os.path.join(od, "out.txt")
    open(OUT, "w", encoding="utf-8", newline="\n").write("PRESETPANE_OUT\n")
    meta = {"mode": mode}
    prof = os.path.join(od, "_profile")
    os.makedirs(prof, exist_ok=True)
    # mode text-* runs the TWO-file dispatched Text Compare session (no
    # Center/Output panes, no merge output document) — the field count and
    # the confirm-modal behaviour there are exactly what the GUI first tier
    # needs to know and were NOT covered by the merge-view runs.
    textview = mode.startswith("text")
    args = [L, R] if textview else [L, R, C, OUT]
    job = create_kill_job()
    si, pi = plaunch(exe, {"APPDATA": prof, "LOCALAPPDATA": prof}, args=args)
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
        if not main_h:
            meta["no-main"] = visible_nonmain(pi.dwProcessId)
            meta["all-top"] = [[get_class(w), get_window_text(w), bool(u32.IsWindowVisible(w))]
                               for w in top_windows(pi.dwProcessId)]
            return meta
        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        win.set_focus(); time.sleep(2.0)

        # BASELINE
        meta["title-before"] = get_window_text(main_h)
        img, rect = capture_window(main_h); img.save(os.path.join(od, "base.png"))
        meta["rect"] = list(rect)
        meta["statusbar-before"] = statusbar_texts(win)

        # open dialog: physical click Session -> find popup -> PHYSICAL click
        # the item (UIA invoke on VCL menu popups is unreliable, measured in
        # the merge-to probe rounds — click_input is the only trusted trigger).
        items = [x for x in win.descendants(control_type="MenuItem")
                 if x.element_info.name == "Session"]
        meta["session-item-found"] = len(items)
        popup_h = None
        # first physical click can be swallowed (foreground transition), same
        # measured flakiness as the merge-to probes — retry up to 3 times,
        # each time ensuring the main window is the foreground first.
        for attempt in range(3):
            for _ in range(15):
                if u32.GetForegroundWindow() == main_h:
                    break
                win.set_focus()
                time.sleep(0.2)
            time.sleep(0.4)
            items[0].click_input()
            t0 = time.time()
            cand = None
            while time.time() - t0 < 5 and not cand:
                for w in top_windows(pi.dwProcessId):
                    if w == main_h or not u32.IsWindowVisible(w):
                        continue
                    cand = w
                    break
                if not cand:
                    time.sleep(0.3)
            if cand:
                # verify it really is the menu popup carrying the item —
                # an unrelated helper window must NOT be accepted (fallback
                # candidate above is intentionally loose)
                try:
                    pw = Desktop(backend="uia").window(handle=cand).wrapper_object()
                    subs = [it for it in pw.descendants(control_type="MenuItem")
                            if (it.element_info.name or "").startswith("Session Settings")]
                except Exception:
                    subs = []
                if subs:
                    popup_h = cand
                    popup_subs = subs
                    meta["popup-attempt"] = attempt + 1
                    meta["popup-class"] = get_class(cand)
                    break
                # wrong window: dismiss nothing, just retry the menu click
                time.sleep(0.6)
        meta["popup-found"] = get_class(popup_h) if popup_h else None
        if popup_h:
            pw = Desktop(backend="uia").window(handle=popup_h).wrapper_object()
            subs = [it for it in pw.descendants(control_type="MenuItem")
                    if (it.element_info.name or "").startswith("Session Settings")]
            meta["sub-found"] = len(subs)
            if not subs:
                meta["popup-names"] = [it.element_info.name for it in
                                       pw.descendants(control_type="MenuItem")][:25]
            if subs:
                subs[0].click_input()
        time.sleep(1.0)
        # poll up to 12s: a first-launch dialog under a fresh profile can be
        # slow (the profile DB initializes on demand)
        dlgs = []
        t0 = time.time()
        while time.time() - t0 < 12 and not dlgs:
            dlgs = [x for x in visible_nonmain(pi.dwProcessId)
                    if x[0] == "TSessionDialog" or "Session Settings" in x[1]]
            if not dlgs:
                time.sleep(0.5)
        meta["dialog-open"] = bool(dlgs)
        if not dlgs:
            return meta
        dh = dlgs[0][2]
        dwin = Desktop(backend="uia").window(handle=dh).wrapper_object()
        combos = [c for c in dwin.descendants()
                  if (c.element_info.class_name or "") == "TUiSpecComboBox"]
        combos = sorted(combos, key=lambda c: c.rectangle().top)
        meta["n_spec_combos"] = len(combos)
        def combo_val(c):
            ed = [e for e in c.descendants(control_type="Edit")]
            if not ed:
                return "?"
            e = ed[0]
            try:
                return "val:" + str(e.get_value())
            except Exception:
                pass
            try:
                return "win:" + e.window_text()
            except Exception as ex:
                return "err:" + str(ex)
        # dialog shot with the ORIGINAL paths
        try:
            dimgr, drect = capture_window(dh)
            dimgr.save(os.path.join(od, "dialog-before.png"))
            meta["dialog-rect"] = list(drect)
        except Exception as e:
            meta["dialog-shot-err"] = str(e)
        meta["left-before-value"] = combo_val(combos[0]) if combos else "no-combo"
        # set Left (combo index 0) to left2.txt, then COMMIT the combo edit:
        # a VCL TComboBox can keep typed text transient until the caret
        # leaves the field — send TAB so BC's internal path model updates;
        # without this, "OK re-compares?" cannot be distinguished from
        # "the path never committed".
        meta["set-result"] = set_combo_text(combos[0], L2) if combos else "no-combo"
        try:
            combos[0].descendants(control_type="Edit")[0].type_keys(
                "{TAB}", set_foreground=True, pause=0.05)
            meta["commit"] = "tab-sent"
        except Exception as e:
            meta["commit"] = "err:" + type(e).__name__
        time.sleep(0.6)
        # re-acquire the dialog wrapper AFTER the TAB (VCL may have rebuilt the
        # subtree; a stale wrapper raises COM 'no subscribers' on any query)
        try:
            dwin = Desktop(backend="uia").window(handle=dh).wrapper_object()
            combos = [c for c in dwin.descendants()
                      if (c.element_info.class_name or "") == "TUiSpecComboBox"]
            combos = sorted(combos, key=lambda c: c.rectangle().top)
            meta["left-after-set-value"] = combo_val(combos[0]) if combos else "?"
        except Exception as e:
            meta["left-after-set-value"] = "re-acquire-err:" + type(e).__name__
        try:
            dimgr2, _ = capture_window(dh)
            dimgr2.save(os.path.join(od, "dialog-edited.png"))
        except Exception as e:
            meta["dialog-shot2-err"] = str(e)
        time.sleep(0.5)

        def dlg_present(cls="TSessionDialog"):
            return bool([x for x in visible_nonmain(pi.dwProcessId)
                         if x[0] == cls])

        def find_dlg(cls):
            for x in visible_nonmain(pi.dwProcessId):
                if x[0] == cls:
                    return x[2]
            return None

        def dlg_dump(tag):
            """capture the currently visible TFileConfirmSaveDialog (tree +
            text + screenshot) — its QUESTION is part of the OK behavior ring"""
            h = find_dlg("TFileConfirmSaveDialog")
            if not h:
                return None
            info = {"handle": h}
            tree = []
            try:
                w = Desktop(backend="uia").window(handle=h).wrapper_object()
                preorder(w, tree)
                json.dump(tree, open(os.path.join(od, f"tree-{tag}.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)
                acc = []
                def rec(n, d=0):
                    try:
                        if d > 12:
                            return
                        ei = n.element_info
                        if ei.name:
                            acc.append((ei.control_type or "", ei.name))
                        for c in n.children():
                            rec(c, d + 1)
                    except Exception:
                        pass
                rec(w)
                info["texts"] = acc[:20]
                img, _ = capture_window(h)
                img.save(os.path.join(od, f"window-{tag}.png"))
            except Exception as e:
                info["err"] = str(e)
            return info

        # ---- DIAGNOSTIC: dialog child structure (one informative run) ----
        try:
            from pywinauto import Desktop as _D
            dw32 = _D(backend="win32").window(handle=dh)
            meta["win32-child-classes"] = sorted({c.element_info.class_name
                                                  for c in dw32.children()})[:30]
            meta["win32-okbtn-found"] = len(dw32.children(class_name="TUiOkBtn"))
        except Exception as e:
            meta["win32-enum-err"] = type(e).__name__
        try:
            meta["uia-buttons-rect"] = {b.element_info.name: list(
                [r.left, r.top, r.width(), r.height()])
                for b, r in [(b, b.rectangle()) for b in
                             dwin.descendants(control_type="Button")
                             if (b.element_info.name or "") in ("OK", "Cancel")]}
        except Exception as e:
            meta["uia-btn-rect-err"] = type(e).__name__

        def raise_dialog():
            for _ in range(10):
                if u32.GetForegroundWindow() == dh:
                    return True
                u32.SetForegroundWindow(dh)
                time.sleep(0.2)
            return False

        act = "Cancel" if (mode == "cancel" or mode == "text-cancel") else "OK"
        meta["out-before"] = open(OUT, encoding="utf-8", errors="replace").read() \
            if os.path.exists(OUT) else "<none>"

        def press_button(win, name):
            for bb in win.descendants(control_type="Button"):
                if (bb.element_info.name or "") == name:
                    bb.invoke()
                    return True
            return False

        # step 1: press OK / Cancel on the Session Settings dialog.
        # MEASURED: uia invoke on OK is EFFECTIVE — it either closes the
        # dialog (no output edits) or, when the merge output would change,
        # raises the modal 'Save merge output?' TFileConfirmSaveDialog FIRST
        # (that modal is what blocked every earlier "did OK work?" reading).
        b = None
        for bb in dwin.descendants(control_type="Button"):
            if (bb.element_info.name or "") == act:
                b = bb
                break
        raised = raise_dialog()
        press_button(dwin, act)
        time.sleep(1.2)

        # step 2: the confirm-save modal (Yes/No/Cancel) — answer per mode.
        #   ok-yes  -> 'Save merge output?' YES  (save new merge to OUT, then apply)
        #   ok-no   -> 'Save merge output?' NO   (discard, then apply the new spec)
        #   cancel  -> Cancel on Session Settings: NO confirm expected at all
        confirm = None
        ch = {"ok-yes": "Yes", "ok-no": "No", "text-ok": "Yes"}.get(mode)
        t0 = time.time()
        while time.time() - t0 < 6:
            confirm = dlg_dump("confirm")
            if confirm:
                break
            time.sleep(0.4)
        meta["confirm-raised"] = bool(confirm)
        meta["confirm-buttons"] = [t for (k, t) in (confirm or {}).get("texts", [])
                                   if k == "Button"]
        if confirm and ch:
            cph = confirm["handle"]
            cw = Desktop(backend="uia").window(handle=cph).wrapper_object()
            meta["confirm-answer"] = ch
            press_button(cw, ch)
            time.sleep(1.5)

        # step 3: did the Session Settings dialog close? (poll)
        closed = False
        t0 = time.time()
        while time.time() - t0 < 10:
            if not dlg_present("TSessionDialog"):
                closed = True
                break
            time.sleep(0.4)
        meta["act-closed-dialog"] = closed
        # any leftover modal?
        meta["windows-after"] = [[get_class(w), get_window_text(w)]
                                 for w in top_windows(pi.dwProcessId)
                                 if u32.IsWindowVisible(w)]
        time.sleep(1.2)  # let any re-compare settle

        # AFTER
        meta["act-closed-dialog"] = closed
        meta["dialog-still-open"] = bool([x for x in visible_nonmain(pi.dwProcessId)
                                          if x[0] == "TSessionDialog"])
        # did BC REPLACE the main window (close+reopen) or keep it in place?
        mains = [w for w in top_windows(pi.dwProcessId)
                 if get_class(w) == "TViewForm" and u32.IsWindowVisible(w)]
        meta["main-handle-before"] = main_h
        meta["main-handles-after"] = mains
        meta["main-replaced"] = bool(mains) and main_h not in mains
        if meta["main-replaced"]:
            main_h = mains[0]
            win = Desktop(backend="uia").window(handle=main_h).wrapper_object()
        meta["title-after"] = get_window_text(main_h)
        img2, rect2 = capture_window(main_h); img2.save(os.path.join(od, f"after-{mode}.png"))
        meta["statusbar-after"] = statusbar_texts(win)
        meta["out-after"] = open(OUT, encoding="utf-8", errors="replace").read() \
            if os.path.exists(OUT) else "<none>"
        # left-pane pixel diff (top source row, leftmost third)
        import numpy as np
        a = np.asarray(img.convert("RGB")); bimg = np.asarray(img2.convert("RGB"))
        WX, WY = rect[0], rect[1]
        # merge left pane approx window-rel x 8..487, y 154..380
        box = (slice(160, 360), slice(60, 470))  # left source body area
        try:
            d = (a[box].astype(int) - bimg[box].astype(int))
            meta["leftpane_diffpx"] = int((np.abs(d).max(axis=2) > 40).sum())
            # generic signal for ANY view layout (text = twin panes, not the
            # merge left column): whole-window changed pixels
            dw = (a.astype(int) - bimg.astype(int))
            meta["whole_diffpx"] = int((np.abs(dw).max(axis=2) > 40).sum())
        except Exception as e:
            meta["leftpane_diffpx"] = "err:" + str(e)
        return meta
    finally:
        k32.TerminateJobObject(job, 0)
        ctypes.windll.kernel32.CloseHandle(job)
        time.sleep(0.5)
        print("residue:", [w for w in top_windows(pi.dwProcessId) if u32.IsWindowVisible(w)])


def main():
    exe, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    mode = sys.argv[3] if len(sys.argv) > 3 else "ok-yes"
    if mode == "ok":
        mode = "ok-yes"
    od = os.path.join(outdir, f"R5-{mode}")
    if os.path.exists(od):
        shutil.rmtree(od)
    os.makedirs(od, exist_ok=True)
    meta = run(exe, od, mode)
    json.dump(meta, open(os.path.join(od, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: meta.get(k) for k in ("mode", "dialog-open",
                      "n_spec_combos", "left-before-value", "commit",
                      "left-after-set-value", "confirm-raised", "confirm-buttons",
                      "confirm-answer", "act-closed-dialog", "dialog-still-open",
                      "main-replaced", "title-before", "title-after",
                      "leftpane_diffpx", "out-before", "out-after")
                      if k in meta}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
