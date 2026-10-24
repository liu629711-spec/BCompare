#!/usr/bin/env python3
"""Probe one failing case: dump sim band walk vs oracle rows around divergence."""
from __future__ import annotations
import sys, pathlib, xml.etree.ElementTree as ET
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import simulate_mode3 as S

RUNS = pathlib.Path(r"D:\Rea\product\verify\runs")

def find(tag):
    for d in sorted(RUNS.glob("gateb-*")):
        p = d / "reports" / f"{tag}.oracle.xml"
        if p.exists():
            fx = d / "fixtures"
            return d, fx / f"{tag}-L.txt", fx / f"{tag}-R.txt", p
    raise SystemExit(f"no case {tag}")

def oracle_rows(path):
    t = ET.parse(path); fc = t.getroot().find("filecomparison")
    out = []
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

def to1(rows):
    return [(s, (i + 1) if i is not None else None, (j + 1) if j is not None else None)
            for s, i, j in rows]

def sim_bands(L, R):
    """Replicate simulate() but record per-band row ranges + run tables."""
    n, m = len(L), len(R)
    LS_L = S.LineSet(L); LS_R = S.LineSet(R)
    uniq = {k: i for i, k in enumerate(sorted(set(LS_L.key) | set(LS_R.key)))}
    LS_L.codes = np.array([uniq[k] for k in LS_L.key], dtype=np.int64)
    LS_R.codes = np.array([uniq[k] for k in LS_R.key], dtype=np.int64)
    rows = []
    bands = []
    lc, rc = 0, 0
    le, re_ = n - 1, m - 1
    while lc <= le or rc <= re_:
        r0 = len(rows)
        bxL = min(le, lc + S.W - 1); bxR = min(re_, rc + S.W - 1)
        rec = {"start": (lc, rc), "box": (bxL, bxR), "rows": (r0, None), "runs": None}
        if lc > le:
            k = min(re_, rc + 199)
            for j in range(rc, k + 1):
                rows.append(("rightorphan", None, j))
            rec["kind"] = "one-sided-R"
            bands.append(rec)
            rc = k + 1
            continue
        if rc > re_:
            k = min(le, lc + 199)
            for i in range(lc, k + 1):
                rows.append(("leftorphan", i, None))
            rec["kind"] = "one-sided-L"
            bands.append(rec)
            lc = k + 1
            continue
        runs = S.collect_runs(LS_L, LS_R, L, R, lc, bxL, rc, bxR, le, re_)
        runs_r = S.resolve_runs(L, runs, bxL, bxR, whole_table=True)
        rec["runs"] = runs
        rec["runs_r"] = runs_r
        rec["kind"] = "band"
        cl, cr = lc, rc
        endL, endR = bxL, bxR
        for (sL, sR, ln) in runs_r:
            if cl <= sL - 1 or cr <= sR - 1:
                sub, _, _ = S.nw_fill(LS_L, LS_R, L, R, cl, sL - 1, cr, sR - 1, False)
                rows.extend(sub)
            for k in range(ln):
                st = "same" if L[sL + k] == R[sR + k] else "different"
                rows.append((st, sL + k, sR + k))
            cl = sL + ln; cr = sR + ln
        if runs_r:
            endL, endR = cl - 1, cr - 1
        else:
            sub, endL, endR = S.nw_fill(LS_L, LS_R, L, R, cl, bxL, cr, bxR, True)
            rows.extend(sub)
        rec["end"] = (endL, endR)
        rec["rows"] = (r0, len(rows))
        bands.append(rec)
        lc, rc = endL + 1, endR + 1
    return rows, bands

def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "W-off1990"
    d, lp, rpp, oxml = find(tag)
    L = lp.read_text(encoding="utf-8", newline="").splitlines()
    R = rpp.read_text(encoding="utf-8", newline="").splitlines()
    want = oracle_rows(oxml)
    print(f"{tag}: L={len(L)} R={len(R)} oracle rows={len(want)}")
    rows, bands = sim_bands(L, R)
    got1 = to1(rows)
    idx = None
    for i, (x, y) in enumerate(zip(got1, want)):
        if x != y: idx = i; break
    if idx is None and len(got1) != len(want):
        idx = min(len(got1), len(want))
    print(f"first diff idx={idx} (got len={len(got1)})")
    for bi, b in enumerate(bands):
        mark = " <<<" if b["rows"][0] <= (idx or 10**9) < (b["rows"][1] if b["rows"][1] is not None else len(rows)) else ""
        runs_r = b.get("runs_r")
        print(f"band{bi} {b['kind']} L{b['start'][0]+1}..{ (b.get('end') or b['box'])[0]+1 }"
              f" R{b['start'][1]+1}..{ (b.get('end') or b['box'])[1]+1 }"
              f" rows[{b['rows'][0]}..{b['rows'][1]}] "
              f"runs={ [(sL+1, sR+1, ln, w) for (sL,sR,ln,w) in (b.get('runs') or [])] }"
              f" resolved={ [(sL+1, sR+1, ln) for (sL,sR,ln) in (runs_r or [])] }{mark}")
    if idx is not None:
        lo = max(0, idx - 6)
        print("want:", want[lo:idx+10])
        print("got :", got1[lo:idx+10])
        st, l, r = want[idx]
        if l and r:
            print("content want idx:", repr(L[l-1]), repr(R[r-1]))
        if got1[idx][1] and got1[idx][2]:
            print("content got  idx:", repr(L[got1[idx][1]-1]), repr(R[got1[idx][2]-1]))

if __name__ == "__main__":
    main()
