#!/usr/bin/env python3
"""Threshold demonstration (2026-10-15): at what maximal equal-hash diagonal
run length does the SmartAlign window engine record a >500-weight candidate?
Every line weight is len(key), so a run of length L over lines of avg key
length K has weight ~ 2*K*L; the gate 2*K*L > 500 needs L >= ~250/K. Show the
smallest L that fires for K=20 and confirm the model anchors it as a run."""
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")
from scan2_eval import nw_fill
from mixed_eval import collect_runs, resolve
from model_s import run_weight_line

def fire_len(K):
    # identical block of L lines, each a distinct key of length K; unique
    # prefix/suffix so the block is its own interval; one side gets an extra
    # orphan to force it into a handler interval rather than scan pair.
    for L in range(1, 600):
        ids_l = [f"L{i:05d}_{'x'*K}" for i in range(L)]
        ids_r = list(ids_l)
        wl = [len(k) for k in ids_l]
        wr = [len(k) for k in ids_r]
        cands, aborted = collect_runs(0, 0, L-1, L-1, ids_l, ids_r, wl, wr, 10**9)
        if cands:
            w = max(c[1] for c in cands)
            return L, w
    return None, None

for K in (10, 20, 30, 50):
    L, w = fire_len(K)
    print(f"key length {K:2}: first run length that records a candidate "
          f"L={L} weight={w}  (needs 2*K*L>500 -> L>{500//(2*K)})")
