#!/usr/bin/env python3
"""Batch acceptance: every golden form -> render -> dump -> structure gate.

Reports coverage (how many of the 211 forms the WPF renderer reproduces with a
0-diff descriptor round-trip at 'full' level) and classifies failures so the
renderer roadmap is evidence-driven.

Usage: python tools/ui-batch-accept.py [--level full] [--limit N] [--filter SUBSTR]
Exit 0 = every form passed (or the passes meet --min); 1 = failures below --min.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

spec = importlib.util.spec_from_file_location("usc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui-structure-check.py"))
usc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usc)

DLL = r"D:\Rea\product\gui\WpfHost\bin\Debug\net8.0-windows\reacmp-gui.dll"
GOLDEN = r"D:\Rea\extracted\guibaseline\forms-en.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="full", choices=["structure", "layout", "full"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--filter", default="")
    ap.add_argument("--min", type=int, default=0)
    a = ap.parse_args()

    gm = json.load(open(GOLDEN, encoding="utf-8"))
    names = sorted(gm)
    if a.filter:
        names = [n for n in names if a.filter.lower() in n.lower()]
    if a.limit:
        names = names[: a.limit]

    tmp = tempfile.mkdtemp()
    env = dict(os.environ, DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    passed, failed = [], []
    for n in names:
        desc = os.path.join(tmp, n + ".json")
        out = os.path.join(tmp, n + ".dump.json")
        json.dump(gm[n], open(desc, "w", encoding="utf-8"), ensure_ascii=False)
        r = subprocess.run(["dotnet", DLL, desc, "--form", n, "--dump", out],
                           capture_output=True, text=True, env=env, timeout=60)
        if r.returncode != 0:
            failed.append((n, "render-fidelity: " + (r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "rc=%d" % r.returncode)[:120]))
            continue
        rc, diffs = usc.run_check(out, n, a.level, golden_map=gm)
        if rc == 0:
            passed.append(n)
        else:
            kinds = {}
            for d in diffs:
                kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
            failed.append((n, f"gate diffs={len(diffs)} {kinds}"))

    print(f"level={a.level} total={len(names)} pass={len(passed)} fail={len(failed)}")
    for n, why in failed:
        print(f"  FAIL {n}: {why}")
    return 0 if len(passed) >= a.min and not (a.min and len(failed)) else (0 if len(passed) >= a.min and len(failed) == 0 else 1)


if __name__ == "__main__":
    sys.exit(main())
