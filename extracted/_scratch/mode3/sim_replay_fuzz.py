#!/usr/bin/env python3
"""Replay the SIMULATOR over the fuzz fixtures vs stored oracle XML.

Usage: python sim_replay_fuzz.py [--limit N]
"""
import argparse, pathlib, re, sys
import xml.etree.ElementTree as ET
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import simulate_mode3 as S

REA = pathlib.Path(r"D:\Rea")
FUZZ = REA / "product/verify/runs/m54-fuzz-20261014T170917Z"

def orows(path):
    t = ET.parse(path); fc = t.getroot().find("filecomparison"); out = []
    for el in fc:
        st = el.get("status")
        if st is None: continue
        l = r = None
        for c in el:
            if c.tag == "text":
                if c.get("ltid") is not None: l = int(c.get("ltid"))
                if c.get("rtid") is not None: r = int(c.get("rtid"))
        out.append((st, l, r))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    cases = []
    for lp in sorted((FUZZ / "fixtures").glob("*-L.*")):
        rp = pathlib.Path(str(lp).replace("-L.", "-R."))
        tag = lp.stem.split("-")[0]
        op = FUZZ / "reports" / f"{tag}.oracle.xml"
        if rp.exists() and op.exists():
            cases.append((tag, lp, rp, op))
    if a.limit: cases = cases[:a.limit]
    ok = 0; fails = []
    for tag, lp, rp, op in cases:
        L = lp.read_text(encoding="utf-8-sig").splitlines()
        R = rp.read_text(encoding="utf-8-sig").splitlines()
        want = orows(op)
        got = [(st, (i+1) if i is not None else None, (j+1) if j is not None else None)
               for st, i, j in S.simulate(L, R)]
        if got == want: ok += 1
        else: fails.append(tag)
    print(f"sim fuzz replay: {ok}/{len(cases)}")
    print("fails:", fails)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
