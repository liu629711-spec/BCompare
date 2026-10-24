#!/usr/bin/env python3
"""Corrected discriminator (2026-10-15): run weight = the TRUE decoded line
weight 140e75c50 composite (important: 2*raw+50; raw = verbatim line length),
NOT key length. Remeasure (a) candidate firings across corpora and (b) the
A vs A+window delta with correct weights."""
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")
from collections import Counter
import mixed_eval as MX
import mixed2_eval as M2
from model_s import load_cases

# true per-line weight: flag=1 -> 2*len+50 (140e75c50 with raw=verbatim len)
def build_weights(case):
    left, right, tl, tr, fmt = case
    wl = [2 * len(t) + 50 for t in left]
    wr = [2 * len(t) + 50 for t in right]
    return wl, wr

# monkeypatch the mixed2 run_case to inject true weights
orig_mixed_handler = M2.mixed_handler

def make_mixed_true(W=10**9):
    def run_case(case, want=None):
        left, right, tl, tr, fmt = case
        n, m = len(left), len(right)
        stl = [t.strip() for t in left]
        str_ = [t.strip() for t in right]
        un_l = [not t for t in tl]
        un_r = [not t for t in tr]
        ids_l = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
        ids_r = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
        wl, wr = build_weights(case)   # <-- true composite weights
        ids = (ids_l, ids_r)
        un = (un_l, un_r)
        ctx = (stl, str_, ids, un, wl, wr)
        from scan2_eval import scan2, emit_rows
        anch, intervals = scan2(ids_l, ids_r, un_l, un_r)
        pairs = list(anch)
        for (i0, j0, i1, j1) in intervals:
            ls = list(range(max(i0, 0), min(i1, n - 1) + 1))
            rs = list(range(max(j0, 0), min(j1, m - 1) + 1))
            if ls and rs:
                pairs.extend(M2.mixed_handler(ls, rs, ctx, W=W))
        pairs = sorted(set(pairs))
        used_l = {i for i, _ in pairs}
        used_r = {j for _, j in pairs}
        lo = [i for i in range(n) if i not in used_l]
        ro = [j for j in range(m) if j not in used_r]
        rows = emit_rows(left, right, tl, tr, pairs, lo, ro)
        return rows if want is None else rows == want
    return run_case

# count candidate firings with true weights
total = fired = 0
orig_cr = MX.collect_runs
def spy(l0, r0, lend, rend, ids_l, ids_r, wl, wr, W):
    global total, fired
    total += 1
    res = orig_cr(l0, r0, lend, rend, ids_l, ids_r, wl, wr, W)
    if res[0]:
        fired += 1
    return res
MX.collect_runs = spy
M2.collect_runs = spy

rcases, fcases = load_cases()
rc = make_mixed_true()
fire_cases = []
for nm, c, w in rcases + fcases:
    b = fired
    ok = rc(c, w)
    if fired > b:
        fire_cases.append((nm, fired - b, ok))
ra = sum(rc(c, w) for _, c, w in rcases)
fa = sum(rc(c, w) for _, c, w in fcases)
print(f"true weights: windows={total} fired={fired}")
print(f"MIXEDv2(true-w)  recorded {ra}/{len(rcases)}  fuzz {fa}/{len(fcases)}")
print("firing cases:", fire_cases[:20])
