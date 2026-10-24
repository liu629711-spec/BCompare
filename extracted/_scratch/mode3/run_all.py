#!/usr/bin/env python3
"""Validate simulate_mode3.py against EVERY archived gateb oracle XML.

For each run/tag pair: read fixtures {tag}-L.txt / {tag}-R.txt, simulate the
mode3 row stream, parse the oracle XML rows, compare (status, ltid, rtid)
1-based. Prints PASS/FAIL + first-diff context; writes results.json.

Usage: cd D:\Rea\extracted\_scratch\mode3 && python run_all.py [--only TAG...]
"""
from __future__ import annotations
import json, pathlib, sys, xml.etree.ElementTree as ET
from simulate_mode3 import simulate

RUNS = pathlib.Path(r"D:\Rea\product\verify\runs")
CASES = []
for d in sorted(RUNS.glob("gateb-*")):
    fx = d / "fixtures"; rp = d / "reports"
    if not fx.exists():
        continue
    for oxml in sorted(rp.glob("*.oracle.xml")):
        tag = oxml.name[: -len(".oracle.xml")]
        lp = fx / f"{tag}-L.txt"; rpp = fx / f"{tag}-R.txt"
        if lp.exists() and rpp.exists():
            CASES.append((d.name, tag, lp, rpp, oxml))

def oracle_rows(path):
    t = ET.parse(path); fc = t.getroot().find("filecomparison")
    out = []
    for el in fc:
        st = el.get("status")
        if st is None:
            continue
        l = r = None
        for c in el:
            if c.tag == "text":
                if c.get("ltid") is not None: l = int(c.get("ltid"))
                if c.get("rtid") is not None: r = int(c.get("rtid"))
        out.append((st, l, r))
    return out

def to1(rows):
    return [(s, (i + 1) if i is not None else None, (j + 1) if j is not None else None)
            for s, i, j in rows]

def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i, x, y
    if len(a) != len(b):
        return min(len(a), len(b)), None, None
    return None, None, None

def main():
    only = set(sys.argv[2:]) if len(sys.argv) > 2 and sys.argv[1] == "--only" else None
    results = []
    ok = 0
    for run, tag, lp, rpp, oxml in CASES:
        if only and tag not in only:
            continue
        L = lp.read_text(encoding="utf-8", newline="").splitlines()
        R = rpp.read_text(encoding="utf-8", newline="").splitlines()
        want = oracle_rows(oxml)
        try:
            got = to1(simulate(L, R))
        except Exception as e:
            print(f"FAIL {run}/{tag}: EXCEPTION {e!r}")
            results.append({"run": run, "tag": tag, "status": "exception", "err": repr(e)})
            continue
        if got == want:
            print(f"PASS {tag}")
            results.append({"run": run, "tag": tag, "status": "pass"})
            ok += 1
        else:
            i, x, y = first_diff(got, want)
            n = min(len(got), len(want))
            ctx_w = want[max(0,(i or 0)-2):(i or 0)+4]
            ctx_g = got[max(0,(i or 0)-2):(i or 0)+4]
            print(f"FAIL {tag}: len got={len(got)} want={len(want)} first diff idx={i}\n"
                  f"   want {ctx_w}\n   got  {ctx_g}")
            results.append({"run": run, "tag": tag, "status": "fail", "idx": i,
                            "len_got": len(got), "len_want": len(want),
                            "want_ctx": list(ctx_w), "got_ctx": list(ctx_g)})
    print(f"\n== {ok}/{len([c for c in CASES if not only or c[1] in only])} pass ==")
    pathlib.Path(__file__).with_name("results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
