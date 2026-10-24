import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
for p in (REA/"product"/"verify", REA/"product"/"verify"/"tools", REA/"extracted"/"_scratch"/"m556"):
    sys.path.insert(0, str(p))
from m26_model_grade import split_bc, facts, fmt_of, collect
from m55_model_lab import parse_xml_rows
import m55_anchor_eval as E
import faithful
GAP=E.GAP
CUR=["plain"]
def nw(ci):
    def f(ls, rs, ctx):
        n,m=len(ls),len(rs)
        if n==0 or m==0: return []
        stl,str_,ids,un=ctx
        fold=ci and CUR[0]=="plain"
        F=[[0]*(n+1) for _ in range(m+1)]; D=[[0]*(n+1) for _ in range(m+1)]
        for c in range(1,n+1): F[0][c]=F[0][c-1]-GAP; D[0][c]=1
        for r in range(1,m+1):
            F[r][0]=F[r-1][0]-GAP; D[r][0]=2
            for c in range(1,n+1):
                a,b=ls[n-c],rs[m-r]
                same=(not un[0][a]) and ids[0][a]==ids[1][b]
                ta,tb=stl[a],str_[b]
                if fold: ta,tb=ta.lower(),tb.lower()
                best=F[r-1][c-1]+E.pair_similarity(ta,tb,same,len(ids[0][a]),len(ids[1][b]))
                k=3
                if best<F[r][c-1]-GAP: best,k=F[r][c-1]-GAP,1
                if best<F[r-1][c]-GAP: best,k=F[r-1][c]-GAP,2
                F[r][c],D[r][c]=best,k
        pairs=[]; r,c=m,n
        while r or c:
            k=D[r][c]
            if k==3: pairs.append((ls[n-c],rs[m-r])); r-=1; c-=1
            elif k==2: r-=1
            else: c-=1
        return pairs
    return f

def full_rows(tag):
    fz=REA/"product/verify/runs/m54-fuzz-20261014T170917Z"
    lp=fz/"fixtures"/f"{tag}-L.txt"; rp=fz/"fixtures"/f"{tag}-R.txt"
    o=(fz/"reports"/f"{tag}.oracle.xml").read_bytes().decode("utf-8-sig",errors="replace")
    l,r=split_bc(lp.read_bytes()),split_bc(rp.read_bytes()); fmt=fmt_of(str(lp))
    case=(l,r,facts(l,fmt),facts(r,fmt),fmt)
    CUR[0]=fmt
    E.nw_fill=nw(True)
    cfg=dict(pred_break=False,bi_pending=False)
    return faithful.model(case,**cfg), parse_xml_rows(o), case

for tag in ("f0057","f0092"):
    got,want,case=full_rows(tag)
    print(f"{tag}: got {got}")
    print(f"{tag}: want {want}")
    print("  L:",case[0]); print("  R:",case[1])
    print("  impL:",case[2]); print("  impR:",case[3])
    # restore
import importlib
E.nw_fill=nw(False)
for tag in ("f0057","f0092"):
    got,want,case=full_rows(tag)
    print(f"[cs] {tag}: got {got}")
