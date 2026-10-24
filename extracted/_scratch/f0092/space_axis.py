#!/usr/bin/env python3
"""Text-axis for 140e726b0's scorer input: T1 = whitespace-removed, case-
sensitive; T2 = whitespace-removed + lower-cased. NW reads the transformed
text; everything else (anchors, scan, handler, same-key branch, verdicts) is
faithful A. P4/P5 hand-analysis says BC's scorer sees case-SENSITIVE text with
the INTERNAL whitespace gone: P4 'x node beta'->'xnodebeta' lifts (o,d,e) to
raw -4 -> -17 (pair), P5 'NODE X BETA'->'NODEXBETA' leaves common {N} only."""
from __future__ import annotations
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
for p in (REA/"product"/"verify", REA/"product"/"verify"/"tools", REA/"extracted"/"_scratch"/"m556"):
    sys.path.insert(0, str(p))
from m26_model_grade import collect, facts, fmt_of, split_bc
from m55_model_lab import parse_xml_rows
import m55_anchor_eval as E
import faithful

GAP=E.GAP
MODE=["T0"]
def nw_t(ls, rs, ctx):
    n,m=len(ls),len(rs)
    if n==0 or m==0: return []
    stl,str_,ids,un=ctx
    def tx(s):
        s="".join(s.split())
        return s.lower() if MODE[0]=="T2" else s
    f=[[0]*(n+1) for _ in range(m+1)]; d=[[0]*(n+1) for _ in range(m+1)]
    for c in range(1,n+1): f[0][c]=f[0][c-1]-GAP; d[0][c]=1
    for r in range(1,m+1):
        f[r][0]=f[r-1][0]-GAP; d[r][0]=2
        for c in range(1,n+1):
            a,b=ls[n-c],rs[m-r]
            same=(not un[0][a]) and ids[0][a]==ids[1][b]
            best=f[r-1][c-1]+E.pair_similarity(tx(stl[a]),tx(str_[b]),same,len(ids[0][a]),len(ids[1][b]))
            k=3
            if best<f[r][c-1]-GAP: best,k=f[r][c-1]-GAP,1
            if best<f[r-1][c]-GAP: best,k=f[r-1][c]-GAP,2
            f[r][c],d[r][c]=best,k
    pr=[]; r,c=m,n
    while r or c:
        k=d[r][c]
        if k==3: pr.append((ls[n-c],rs[m-r])); r-=1;c-=1
        elif k==2: r-=1
        else: c-=1
    return pr

orig=E.nw_fill
try:
    E.nw_fill=nw_t
    cfg=dict(pred_break=False,bi_pending=False)
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
    for mode in ("T1","T2"):
        MODE[0]=mode
        rok=sum(faithful.model(c,**cfg)==w for _,c,w in rcases)
        fok=sum(faithful.model(c,**cfg)==w for _,c,w in fcases)
        print(f"{mode}  recorded {rok}/{len(rcases)}  fuzz {fok}/{len(fcases)}")
        print("   fuzz fails:", [nm for nm,c,w in fcases if faithful.model(c,**cfg)!=w])
        print("   rec fails: ", sorted(set(nm for nm,c,w in rcases if faithful.model(c,**cfg)!=w)))
    # probe fixtures under T1/T2
    CASES=[("P1",["delta","value value alpha","x node beta","beta"],["DELTA","Node"]),
           ("P4",["x node beta","beta"],["Node"]),
           ("P5",["NODE X BETA","BETA"],["Node"]),
           ("P2",["NODEx","beta","alpha"],["node","x"]),
           ("P7",["alpha node item value","delta data"],["yy beta","ITEM VALUE YY VALUE"])]
    for mode in ("T1","T2"):
        MODE[0]=mode
        print(f"[{mode}]", {t: faithful.model((l,r,facts(l,"plain"),facts(r,"plain"),"plain"),**cfg) for t,l,r in CASES})
finally:
    E.nw_fill=orig
