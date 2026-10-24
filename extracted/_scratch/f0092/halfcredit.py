#!/usr/bin/env python3
"""Hypothesis (fit to f0092 + f0057 jointly): BC's 140e725f0 histogram counts
case-folded extra matches at HALF weight (ceiling).  cs = exact-byte common,
ci = case-folded common, credit = cs + ceil((ci - cs)/2).
  f0092 (L3 vs 'Node'): cs 3, ci 4, k=1 -> credit 4 -> raw -3 -> -13 -> pairs L3  (BC)
  f0057 (L3 vs 'ITEM VALUE YY VALUE'): cs 3, ci 16, k=13 -> credit 10 -> raw -8
        -> -33 -> orphan L3, pair (L4,R4) at -21                       (BC)
Full-corpus test: replace E.intersect in pair_similarity's raw branch only.
"""
from __future__ import annotations
import pathlib, sys
from collections import Counter
REA = pathlib.Path(r"D:\Rea")
for p in (REA/"product"/"verify", REA/"product"/"verify"/"tools", REA/"extracted"/"_scratch"/"m556"):
    sys.path.insert(0, str(p))
from m26_model_grade import collect, facts, fmt_of, split_bc
from m55_model_lab import parse_xml_rows
import m55_anchor_eval as E
import faithful

def intersect(a, b):
    fa = Counter(a)
    cs = sum(min(fa.get(ch, 0), nb) for ch, nb in Counter(b).items())
    fl = Counter(a.lower())
    ci = sum(min(fl.get(ch, 0), nb) for ch, nb in Counter(b.lower()).items())
    return cs + (ci - cs + 1) // 2

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
    raw = common * 3 - len(a) - len(b)
    if raw < 1:
        return max(raw * 4 - 1, -40)
    return (raw * 25) // min(len(a), len(b))

orig_i, orig_p = E.intersect, E.pair_similarity
try:
    E.intersect = intersect
    E.pair_similarity = pair_similarity
    cfg = dict(pred_break=False, bi_pending=False)
    rcases=[(pathlib.PurePath(c["src"]).name,
             (c["left"],c["right"],facts(c["left"],fmt_of(c["left_path"])),
              facts(c["right"],fmt_of(c["left_path"])),fmt_of(c["left_path"])),
             [[s,i,j] for s,i,j in c["bc_rows"]]) for c in collect()]
    fz=REA/"product/verify/runs/m54-fuzz-20261014T170917Z"; fcases=[]
    for lp in sorted((fz/"fixtures").glob("*-L.*")):
        rp=pathlib.Path(str(lp).replace("-L.","-R.")); tag=lp.stem.split("-")[0]
        o=(fz/"reports"/f"{tag}.oracle.xml").read_bytes().decode("utf-8-sig",errors="replace")
        l,r=split_bc(lp.read_bytes()),split_bc(rp.read_bytes()); fmt=fmt_of(str(lp))
        fcases.append((tag,(l,r,facts(l,fmt),facts(r,fmt),fmt),parse_xml_rows(o)))
    rok=sum(faithful.model(c,**cfg)==w for _,c,w in rcases)
    fok=sum(faithful.model(c,**cfg)==w for _,c,w in fcases)
    print(f"half-credit  recorded {rok}/{len(rcases)}  fuzz {fok}/{len(fcases)}")
    print("   fuzz fails:", [nm for nm,c,w in fcases if faithful.model(c,**cfg)!=w])
    print("   rec fails: ", sorted({nm for nm,c,w in rcases if faithful.model(c,**cfg)!=w}))
finally:
    E.intersect, E.pair_similarity = orig_i, orig_p
