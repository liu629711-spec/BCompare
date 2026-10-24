#!/usr/bin/env python3
"""Offline replay of the Beyond Compare window engine (140e73b40 family).

Reads the real BC oracle XMLs under D:\\Rea\\product\\verify\\runs\\gateb-*\\
and checks them against the semantics recovered statically from the
decompiled pseudocode, WITHOUT running BComp.

Recovered semantics encoded here (evidence grade in ANALYSIS.md):

  Window origin / W:
    140e733b0 (window walk) sets the reachable box to
       [start .. start + W - 1]  on both sides, W = job+0x98 (140e733b0 line 25/31).
    Observed boundary: a shared run whose start is <= 1992 rows from the window
    origin pairs; == 1993 does not  ->  W == 1993 (start..start+1992 inclusive).

  Candidate weight gate (140e73040 + 140e74080):
    A diagonal run is recorded as a candidate only if its summed line weight
    > 500   (140e73040 line 76 `if (500 < iVar10)`; re-check in 140e74080
    line 25 `if (param_2[1] < 500) param_2[1]=0;`).
    Line weight w = 2*len + 50 for a non-blank line, 10 for blank
    (140e75c50: present & len>0 -> 2*len+0x32; else +0x1e or *2+0x32).

  5000 raise (140e73040 line 45, `iVar10 > 4999`):
    Builds a Delphi EListError-style exception (0x0EEDFADE via 140052fe0) and
    RAISES it (140012e10 -> 140012cb0 -> RaiseException). It does NOT return /
    break the scan loop: after the raise pair the code falls through to the
    normal next-diagonal step at 140e73168.  So a run crossing 5000 aborts the
    WHOLE comparison via an exception (caught far up), it does not merely stop
    collecting -- which is why K=100 (weight 5580, crosses 5000 mid-run) still
    "pairs" only if the run is under 5000 at the moment of the weight-accum
    step.  (See anomaly (2) discussion.)

This script is a CHECKER, not a simulator: it re-derives expected pairings from
the recovered rules and diffs them against the oracle XML, to falsify/confirm
the rules on every fixture we have.
"""
from __future__ import annotations
import os, re, sys
from collections import Counter
from xml.etree import ElementTree as ET

BASE = r"D:/Rea/product/verify/runs"
W_OBS = 1993  # window size from boundary probes

def line_weight(s: str) -> int:
    # 140e75c50: non-blank present line -> 2*len + 50 (0x32); blank -> 10 (0xa)
    return 2*len(s) + 50 if len(s) > 0 else 10

def oracle_rows(path):
    t = ET.parse(path).getroot()
    fc = t.find("filecomparison")
    rows = []  # (status, ltid|None, rtid|None)
    for el in fc:
        st = el.get("status")
        l = r = None
        for c in el:
            if c.tag == "text":
                if c.get("ltid") is not None: l = int(c.get("ltid"))
                if c.get("rtid") is not None: r = int(c.get("rtid"))
        rows.append((st, l, r))
    return rows

def fixture_lines(path):
    return open(path, encoding="utf-8", newline="").read().splitlines()

def shared_run(fx_dir, tag):
    """Given fixtures {tag}-L.txt/-R.txt, find the shared block (contiguous run
    of lines common to a left range and a right range in the same order)."""
    try:
        L = fixture_lines(os.path.join(fx_dir, tag + "-L.txt"))
        R = fixture_lines(os.path.join(fx_dir, tag + "-R.txt"))
    except FileNotFoundError:
        return None
    return L, R

def predict_window_pairing(K, off):
    """Predict whether a K-length shared run at diagonal offset `off` pairs,
    using the recovered rules.  Both sides total >= 5001 (window path forced).
    Returns (paired_count, reason)."""
    run_weight = sum(line_weight(f"S{i}") for i in range(K))
    if run_weight <= 500:
        return 0, f"weight {run_weight} <= 500 (candidate gate fails)"
    # start within window?  window origin is the interval start; block sits at
    # `off` rows into the right side, left block at row 0 -> diagonal distance ~off
    if off + 1 > W_OBS:      # start index (0-based off) beyond window reach
        # window clips only the START scan; if start <= W-1 it pairs, else not
        return 0, f"start dist {off} > window W-1={W_OBS-1}"
    return K, f"weight {run_weight} > 500 and start dist {off} <= {W_OBS-1}"

def check(tag, K, off, fx_dir, rp_dir):
    xml = os.path.join(rp_dir, tag + ".oracle.xml")
    if not os.path.exists(xml):
        print(f"  [{tag}] MISSING xml"); return None
    rows = oracle_rows(xml)
    actual = sum(1 for st,l,r in rows
                 if l and r and 1 <= l <= K and off+1 <= r <= off+K)
    pred, why = predict_window_pairing(K, off)
    ok = "OK " if pred == actual else "XX "
    print(f"  [{ok}{tag}] K={K} off={off} actual={actual} predicted={pred}  ({why})")
    return pred == actual

def main():
    runs = {
      "gateb-width-20261015T182136Z":  (100, [1000,3000,4000,4096,4097,5000,6000,9000]),
      "gateb-width6-20261015T182844Z": (100, [1989,1990,1991,1992,1993]),
    }
    results=[]
    for run,(K,offs) in runs.items():
        d=os.path.join(BASE,run)
        fx=os.path.join(d,"fixtures"); rp=os.path.join(d,"reports")
        print(f"== {run} (K={K}) ==")
        for off in offs:
            results.append(check(f"W-off{off}", K, off, fx, rp))
    # big1 K=1 and k50/neg from width8
    d=os.path.join(BASE,"gateb-width8-20261015T183741Z")
    rp=os.path.join(d,"reports")
    print("== width8: big1 (K=1, 300-char Z) ==  [anomaly (1)]")
    for off in [1000,1992,1993,2500]:
        xml=os.path.join(rp,f"big1-off{off}.oracle.xml")
        if os.path.exists(xml):
            rows=oracle_rows(xml)
            zpair=sum(1 for st,l,r in rows if l==1 and r==off+1)
            print(f"  [big1-off{off}] Z paired={zpair} (predicted by weight: "
                  f"{line_weight('Z'*300)}>500 so SHOULD pair if pure window path)")
    done=[r for r in results if r is not None]
    print(f"\nreplay: {sum(1 for r in done if r)}/{len(done)} K=100 cases match "
          f"window+weight rules (K=1 cases reported separately above).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
