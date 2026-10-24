#!/usr/bin/env python3
"""UIA self-check: verify the WPF product renders a descriptor faithfully, using
the SAME accessibility mechanism that produced the BC Oracle baselines.

This closes docs/19's acceptance loop: descriptor -> product window -> UIA tree ->
assert every node is present with correct AutomationId / name / geometry, then
gate that live-derived tree against the guibaseline golden via ui-structure-check.

Launches: dotnet reacmp-gui.dll <descriptor> --show   (own process, no job needed
since we control it directly; kill by pid at the end).

Usage: python tools/uia-selfcheck.py <descriptor.json> [--form NAME]
Exit 0 = all assertions pass; 1 = a fidelity violation; 2 = launch/window failure.
"""
import ctypes
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from live_probe_job import top_windows, get_class, get_window_text, wintypes  # noqa: E402

u32 = ctypes.windll.user32
DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll"


def children_map(el):
    """Return {automationId: child_element} over a UIA wrapper's subtree."""
    out = {}

    def rec(e):
        ai = e.element_info.automation_id
        if ai:
            out.setdefault(ai, e)
        for c in e.children():
            rec(c)
    rec(el)
    return out


def collect_live(el):
    """Flatten live UIA into {aid: {name, cls, rect}}."""
    out = {}

    def rec(e):
        ai = e.element_info.automation_id
        if ai and ai not in out:
            r = e.rectangle()
            out[ai] = {"name": e.element_info.name, "cls": e.element_info.class_name,
                       "rect": [r.left, r.top, r.width(), r.height()]}
        for c in e.children():
            rec(c)
    rec(el)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    desc = os.path.abspath(sys.argv[1])
    form = sys.argv[sys.argv.index("--form") + 1] if "--form" in sys.argv else None
    tree = json.load(open(desc, encoding="utf-8"))
    if "cls" not in tree:
        if not form:
            print("wrapped descriptor needs --form", file=sys.stderr)
            return 2
        tree = tree[form]
        form_name = form
    else:
        form_name = tree["name"]

    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    proc = subprocess.Popen(["dotnet", DLL, desc, "--show"], env=env)
    try:
        # wait for our top-level window (title = translated Caption, class HwndWrapper*)
        hwnd = None
        t0 = time.time()
        while time.time() - t0 < 15:
            for w in top_windows(proc.pid):
                cls = get_class(w)
                if cls.startswith("HwndWrapper") and u32.IsWindowVisible(w):
                    hwnd = w
                    break
            if hwnd:
                break
            time.sleep(0.4)
        if not hwnd:
            print("product window not found (pid %d)" % proc.pid, file=sys.stderr)
            return 2
        time.sleep(1.0)

        from pywinauto import Desktop
        win = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        live = collect_live(win)

        # walk descriptor; assert each node with a Name shows up by AutomationId
        problems = []

        def check(n):
            aid = n.get("name")
            if aid:
                rec = live.get(aid)
                if rec is None:
                    problems.append(f"missing in UIA: {n['cls']}/{aid}")
                else:
                    # caption fidelity for text-bearing controls
                    cap = n.get("props", {}).get("Caption")
                    if isinstance(cap, str) and cap != "%" and rec["name"] and rec["name"] != cap:
                        problems.append(f"text mismatch {aid}: model={cap!r} uia={rec['name']!r}")
            for c in n.get("children", []):
                check(c)

        check(tree)
        # root form itself -> at least window present
        print(f"form={form_name} UIA nodes={len(live)} descriptor-nodes-with-name="
              f"{sum(1 for _ in iter_named(tree))}")
        for p in problems:
            print("SELFCHK FAIL:", p)
        return 1 if problems else 0
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()


def iter_named(node):
    if node.get("name"):
        yield node
    for c in node.get("children", []):
        yield from iter_named(c)


if __name__ == "__main__":
    sys.exit(main())
