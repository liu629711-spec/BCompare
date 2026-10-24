#!/usr/bin/env python3
"""Single-variable: does 140e726b0's overlap histogram run over WHITESPACE
TOKENS instead of CHARACTERS?  The `raw = 3*common - la - lb` formula and the
NW fill are untouched; only `common`, and (optionally) `la`/`lb`, switch from
character counts to token counts.  f0092 is the discriminator: L3 `x node beta`
shares the TOKEN `node` with R2 `Node`; L4 `beta` shares none."""
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

def make_sim(ci, use_tok_len):
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
        key = (lambda s: s.lower()) if ci else (lambda s: s)
        fa = Counter(key(w) for w in a.split())
        common = sum(min(fa.get(key(w), 0), nb)
                     for w, nb in Counter(key(w) for w in b.split()).items())
        la, lb = (len(a.split()), len(b.split())) if use_tok_len else (len(a), len(b))
        raw = common * 3 - la - lb
        if raw < 1:
            return max(raw * 4 - 1, -40)
        return (raw * 25) // min(la, lb)
    return pair_similarity

def build():
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
    return rcases,fcases

def score(tag, ci, lt):
    E.pair_similarity=make_sim(ci,lt)
    cfg=dict(pred_break=False,bi_pending=False)
    rok=sum(faithful.model(c,**cfg)==w for _,c,w in rc)
    fok=sum(faithful.model(c,**cfg)==w for _,c,w in fc)
    ffails=[nm for nm,c,w in fc if faithful.model(c,**cfg)!=w]
    rfails=[nm for nm,c,w in rc if faithful.model(c,**cfg)!=w]
    print(f"{tag:16} recorded {rok}/{len(rc)}  fuzz {fok}/{len(fc)}")
    print(f"    fuzz fails: {ffails}")
    print(f"    rec fails:  {rfails}")

rc,fc=build()
orig=E.pair_similarity
try:
    score("tok-ci-toklen", True, True)
    E.pair_similarity=orig
    score("tok-ci-charlen",True, False)
    E.pair_similarity=orig
    score("tok-cs-toklen",  False,True)
    E.pair_similarity=orig
    score("tok-cs-charlen", False,False)
finally:
    E.pair_similarity=orig
