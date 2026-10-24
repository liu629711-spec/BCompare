#!/usr/bin/env python3
"""Single-variable: what TEXT does 140e726b0's char-intersection feed on for
plain text?  Baseline faithful A feeds score_text = line.strip(), case-
sensitive.  Candidate axes:
  lower  : strip then lower-case  (keep whitespace)
  imp    : important_text (lowercase + whitespace removed)
Every other layer untouched.
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

# Save original nw_fill; build one parameterized by a text-mapping fn.
def make_nw(tmap):
    def nw_fill(ls, rs, ctx):
        stl_raw, str_raw, ids, un = ctx
        stl = [tmap(x) for x in stl_raw]; str_ = [tmap(x) for x in str_raw]
        n, m = len(ls), len(rs)
        if n == 0 or m == 0: return []
        f=[[0]*(n+1) for _ in range(m+1)]; d=[[0]*(n+1) for _ in range(m+1)]
        GAP=E.GAP
        for c in range(1,n+1): f[0][c]=f[0][c-1]-GAP; d[0][c]=1
        for r in range(1,m+1):
            f[r][0]=f[r-1][0]-GAP; d[r][0]=2
            for c in range(1,n+1):
                a,b=ls[n-c],rs[m-r]
                same=(not un[0][a]) and ids[0][a]==ids[1][b]
                best=f[r-1][c-1]+E.pair_similarity(stl[a],str_[b],same,len(ids[0][a]),len(ids[1][b]))
                k=3
                if best < f[r][c-1]-GAP: best,k=f[r][c-1]-GAP,1
                if best < f[r-1][c]-GAP: best,k=f[r-1][c]-GAP,2
                f[r][c],d[r][c]=best,k
        pairs=[]; r,c=m,n
        while r or c:
            k=d[r][c]
            if k==3: pairs.append((ls[n-c],rs[m-r])); r-=1; c-=1
            elif k==2: r-=1
            else: c-=1
        return pairs
    return nw_fill

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

def score(tag,tmap):
    E.nw_fill=make_nw(tmap)
    cfg=dict(pred_break=False,bi_pending=False)
    rok=sum(faithful.model(c,**cfg)==w for _,c,w in rc); fok=sum(faithful.model(c,**cfg)==w for _,c,w in fc)
    ffails=[nm for nm,c,w in fc if faithful.model(c,**cfg)!=w]
    rfails=[nm for nm,c,w in rc if faithful.model(c,**cfg)!=w]
    print(f"{tag:10} recorded {rok}/{len(rc)}  fuzz {fok}/{len(fc)}")
    print(f"   fuzz fails: {ffails}")
    print(f"   rec fails:  {rfails}")

rc,fc=build()
orig=E.nw_fill
score("raw-strip", lambda x:x)          # baseline: already stripped by build_ctx
E.nw_fill=orig
score("lower",    lambda x:x.lower())
E.nw_fill=orig
score("imp-nospc",lambda x:"".join(x.lower().split()))
E.nw_fill=orig
