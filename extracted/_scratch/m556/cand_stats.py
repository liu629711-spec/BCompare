#!/usr/bin/env python3
"""How often does the SmartAlign window record a >500-weight run candidate
on the two corpora? If never, the window engine is an NW no-op at these
sizes and Mode3-vs-Mode1 cannot separate on this data. (2026-10-15)"""
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")
import mixed_eval as MX
from model_s import load_cases, run_weight_line

cand_cases = 0
abort_cases = 0
total_windows = 0
per_case = []
orig = MX.collect_runs

def spy(l0, r0, lend, rend, ids_l, ids_r, wl, wr, W):
    global cand_cases, abort_cases, total_windows
    total_windows += 1
    res = orig(l0, r0, lend, rend, ids_l, ids_r, wl, wr, W)
    if res[1]:
        abort_cases += 1
    if res[0]:
        cand_cases += 1
    return res
MX.collect_runs = spy

def scan_intervals(case):
    left, right, tl, tr, fmt = case
    n, m = len(left), len(right)
    un_l = [not t for t in tl]; un_r = [not t for t in tr]
    ids_l = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
    ids_r = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
    from scan2_eval import scan2
    _, iv = scan2(ids_l, ids_r, un_l, un_r)
    return iv, (ids_l, ids_r)

rcases, fcases = load_cases()
# run MIXEDv2 on all cases and count spy hits
MXMAX = 10**9
import mixed2_eval as M2
M2.collect_runs = spy
rc = M2.make_mixed2(MXMAX)
worst = 0
max_run = 0
for nm, c, w in rcases + fcases:
    cand_cases = 0
    left, right, tl, tr, fmt = c
    iv, ids = scan_intervals(c)
    for (l0, r0, l1, r1) in iv:
        ls = list(range(max(l0,0), min(l1, len(left)-1)+1))
        rs = list(range(max(r0,0), min(r1, len(right)-1)+1))
        if ls and rs:
            for i in ls:
                for j in rs:
                    pass
# simpler global count: just run and report spy counters
M2.collect_runs = spy
cand_cases = abort_cases = total_windows = 0
per_case = []
rcases2, fcases2 = load_cases()
for nm, c, w in rcases2 + fcases2:
    before = cand_cases
    rc(c, w)
    if cand_cases > before:
        per_case.append((nm, cand_cases - before))
print(f"total window scans: {total_windows}; windows with candidates: {cand_cases}; aborts: {abort_cases}")
print("cases where a >500 run fired:", per_case[:20])
