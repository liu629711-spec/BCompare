#!/usr/bin/env python3
"""Hypothesis: 140e725f0's histogram is case-folded exactly when the format's
case rules are insignificant (plain text: yes; syntax: no). Fold attaches to the
decoded case-significance concept, not the file tag.  fmt passed via module
global to keep ctx a 4-tuple (handler_gate unpacks 4)."""
from __future__ import annotations
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
for p in (REA/"product"/"verify", REA/"product"/"verify"/"tools", REA/"extracted"/"_scratch"/"m556"):
    sys.path.insert(0, str(p))
from m26_model_grade import collect, facts, fmt_of, split_bc
from m55_model_lab import parse_xml_rows
import m55_anchor_eval as E
import faithful

GAP = E.GAP
CUR_FMT = ["plain"]
def nw_fill_ci_plain(ls, rs, ctx):
    n, m = len(ls), len(rs)
    if n == 0 or m == 0: return []
    stl, str_, ids, un = ctx
    fold = (CUR_FMT[0] == "plain")
    f=[[0]*(n+1) for _ in range(m+1)]; d=[[0]*(n+1) for _ in range(m+1)]
    for c in range(1,n+1): f[0][c]=f[0][c-1]-GAP; d[0][c]=1
    for r in range(1,m+1):
        f[r][0]=f[r-1][0]-GAP; d[r][0]=2
        for c in range(1,n+1):
            a,b=ls[n-c],rs[m-r]
            same=(not un[0][a]) and ids[0][a]==ids[1][b]
            ta,tb=stl[a],str_[b]
            if fold: ta,tb=ta.lower(),tb.lower()
            best=f[r-1][c-1]+E.pair_similarity(ta,tb,same,len(ids[0][a]),len(ids[1][b]))
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

orig_build=E.build_ctx
def build_ctx_set_fmt(case):
    CUR_FMT[0]=case[4]
    return orig_build(case)

# faithful.model imports build_ctx? It calls E.build_ctx(case). Patch both.
try:
    E.build_ctx=build_ctx_set_fmt
    E.nw_fill=nw_fill_ci_plain
    cfg=dict(pred_break=False,bi_pending=False)
    def run(rf, fcases):
        rc=[]
        for c in collect():
            fmt=fmt_of(c["left_path"])
            rc.append((pathlib.PurePath(c["src"]).name,
                       (c["left"],c["right"],facts(c["left"],fmt),facts(c["right"],fmt),fmt),
                       [[s,i,j] for s,i,j in c["bc_rows"]]))
        rok=sum(faithful.model(c,**cfg)==w for _,c,w in rc)
        fok=sum(faithful.model(c,**cfg)==w for _,c,w in fcases)
        print(f"ci-plain-only  recorded {rok}/{len(rc)}  fuzz {fok}/{len(fcases)}")
        print("   fuzz fails:", [nm for nm,c,w in fcases if faithful.model(c,**cfg)!=w])
        print("   rec fails: ", [nm for nm,c,w in rc if faithful.model(c,**cfg)!=w])
        for nm,c,w in rc:
            if "f0092" in nm or nm=="m2-case-plain.xml": pass
    # build fuzz
    fz=REA/"product/verify/runs/m54-fuzz-20261014T170917Z"; fcases=[]
    for lp in sorted((fz/"fixtures").glob("*-L.*")):
        rp=pathlib.Path(str(lp).replace("-L.","-R.")); tag=lp.stem.split("-")[0]
        o=(fz/"reports"/f"{tag}.oracle.xml").read_bytes().decode("utf-8-sig",errors="replace")
        l,r=split_bc(lp.read_bytes()),split_bc(rp.read_bytes()); fmt=fmt_of(str(lp))
        fcases.append((tag,(l,r,facts(l,fmt),facts(r,fmt),fmt),parse_xml_rows(o)))
    run(None,fcases)
    for nm,c,w in fcases:
        if nm=="f0092": print("   f0092 fmt =", c[4])
finally:
    E.build_ctx=orig_build
