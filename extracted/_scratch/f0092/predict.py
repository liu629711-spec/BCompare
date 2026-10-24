#!/usr/bin/env python3
"""Score the six probe fixtures under cs / ci / half-credit scorers through
the full faithful-A pipeline, so the Oracle result can be attributed."""
from __future__ import annotations
import pathlib, sys
from collections import Counter
REA = pathlib.Path(r"D:\Rea")
for p in (REA/"product"/"verify", REA/"product"/"verify"/"tools", REA/"extracted"/"_scratch"/"m556"):
    sys.path.insert(0, str(p))
from m26_model_grade import facts, split_bc
from m55_model_lab import parse_xml_rows
import m55_anchor_eval as E
import faithful

def make(ci_mode):
    def intersect(a, b):
        fa = Counter(a.lower() if ci_mode!="cs" else a)
        return sum(min(fa.get(ch, 0), nb) for ch, nb in
                   Counter((b.lower() if ci_mode!="cs" else b)).items())
    def pair_similarity(a, b, same_key, wl, wr):
        if same_key:
            if not a or not b: return -10
            s = (wl + wr) * 2
            return s - 1 if len(a) != len(b) else s
        if not a or not b:
            v = -4 * (len(a) + len(b)) - 1
            if v > -12: v = -11
            if v < -39: v = -40
            return v
        common = intersect(a, b)
        if ci_mode == "half":
            fa = Counter(a); cs = sum(min(fa.get(ch,0), nb) for ch, nb in Counter(b).items())
            common = cs + (common - cs + 1) // 2
        raw = common * 3 - len(a) - len(b)
        if raw < 1: return max(raw * 4 - 1, -40)
        return (raw * 25) // min(len(a), len(b))
    return pair_similarity

CASES = [
 ("P1-f0092", ["delta", "value value alpha", "x node beta", "beta"], ["DELTA", "Node"]),
 ("P2-foldx", ["NODEx", "beta", "alpha"], ["node", "x"]),
 ("P3-letters", ["abcdef", "zzzzzz"], ["abcxyz"]),
 ("P4-wordcap", ["x node beta", "beta"], ["Node"]),
 ("P5-allcaps", ["NODE X BETA", "BETA"], ["Node"]),
 ("P7-f0057shape", ["alpha node item value", "delta data"], ["yy beta", "ITEM VALUE YY VALUE"]),
]
orig = E.pair_similarity
cfg = dict(pred_break=False, bi_pending=False)
for mode in ("cs", "ci", "half"):
    E.pair_similarity = make(mode)
    print(f"--- {mode} ---")
    for tag, L, R in CASES:
        case = (L, R, facts(L, "plain"), facts(R, "plain"), "plain")
        rows = faithful.model(case, **cfg)
        pairs = [(s, i, j) for s, i, j in rows if i and j]
        print(f"  {tag:14} pairs={pairs}  rows={rows}")
E.pair_similarity = orig
