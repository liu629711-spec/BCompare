#!/usr/bin/env python3
"""Per-column formula brute-forcer: each geometry column lt/ld/M/rn/rt/rd/rule
is max(floor, content)+pad -- solve floor,pad independently over all cells."""
from __future__ import annotations
import json, glob, pathlib

RUNS = pathlib.Path(r"D:\Rea\product\verify\runs")
FRAME = ("已产生", "左边", "右边", "注册", "模式", "相同", "重要", "独有")

def hidx(line, tok):
    out, s = [], 0
    while True:
        j = line.find(tok, s)
        if j == -1: break
        out.append(j); s = j + len(tok)
    return out

cells = []
for f in sorted(glob.glob(str(RUNS / "m101*" / "*summary*.json"))):
    for c in json.load(open(f, encoding="utf-8")):
        lines = c.get("lines") or []
        hdr = next((ln for ln in lines if "名称" in ln and "类型" in ln), None)
        if hdr is None: continue
        rules = [len(ln) for ln in lines if ln and set(ln) == {"-"}]
        body, in_b = [], False
        for ln in lines:
            if ln == hdr: in_b = True; continue
            if not in_b: continue
            if ln and set(ln) == {"-"}: continue
            if ln and not any(ln.startswith(p) for p in FRAME):
                body.append(ln)
        if not body: continue
        lt = hidx(hdr, "类型")[0]; ld = hidx(hdr, "数据")[0]
        rn = hidx(hdr, "名称")[1]; rt = hidx(hdr, "类型")[1]; rd = hidx(hdr, "数据")[1]
        M = None; mlen = 0
        Ldata_R = None
        # content lengths using header cols (name col = slice; box prefix
        # included). For data columns: right side data extends to line end.
        Ln = Rn = Lt = Rt = Ldmax = Rdmax = 0
        for ln in body:
            m = None
            for tok in ("<>", "+-", "-+"):
                i = ln.rfind(tok, ld)
                if i != -1 and i < rn:
                    m = (tok, i); break
            if m is None:
                i = ln.rfind("=", ld)
                if i != -1 and i < rn and ln[i-1] == " ":
                    m = ("=", i)
            Ln = max(Ln, len(ln[:lt].rstrip()) if ln[:lt].strip() else len(ln[:lt]))
            # bare rows: name content = rstripped slice
            Ln = max(Ln, len(ln[:lt].rstrip()))
            Lt = max(Lt, len(ln[lt:ld].rstrip()))
            if m:
                tok, i = m
                M = i if M is not None else M
                mlen = max(mlen, len(tok))
                if tok != "-+":
                    Ldmax = max(Ldmax, len(ln[ld:i].rstrip()))
            if m and tok != "+-":
                Rn = max(Rn, len(ln[rn:rt].rstrip()))
                Rt = max(Rt, len(ln[rt:rd].rstrip()))
                Rdmax = max(Rdmax, len(ln[rd:].rstrip()))
            elif m is None and len(ln) > rn:
                Rn = max(Rn, len(ln[rn:].rstrip()))
        if mlen == 0 and M is None:
            # all-bare table: marker column concept absent; rn=ld+? model uses mlen=0
            pass
        cells.append(dict(tag=c["tag"], lt=lt, ld=ld, M=M, rn=rn, rt=rt, rd=rd,
                          mlen=mlen, rule=(rules[0] if rules else None),
                          Ln=Ln, Rn=Rn, Lt=Lt, Rt=Rt, Ld=Ldmax, Rd=Rdmax))

def solve(col, content, observed, extra=None):
    """find (floor,pad) in 0..9 with observed == max(floor, content)+pad for all."""
    sols = []
    for fl in range(0, 10):
        for pd in range(0, 6):
            if all(obs == max(fl, c) + pd for c, obs in zip(content, observed)):
                sols.append((fl, pd))
    return sols

def col_solve(name, key, content_key, extra_pred=None):
    obs = [c[key] for c in cells if c[key] is not None]
    cont = [c[content_key] for c in cells if c[key] is not None]
    if extra_pred:
        obs = [o for o, c in zip(obs, cells) if extra_pred(c)]
        cont = [k for k, c in zip(cont, cells) if extra_pred(c)]
    sols = []
    for fl in range(0, 12):
        for pd in range(0, 8):
            if all(o == max(fl, k) + pd for o, k in zip(obs, cont)):
                sols.append((fl, pd))
    print(f"{name}: {len(sols)} sols {sols[:6]}  (n={len(obs)})")
    return sols

col_solve("lt", "lt", "Ln")
col_solve("ld(lt+Wt)", "ld", "Lt")   # actually ld-lt-1 = max(fl,pad)
obs = [c["ld"] - c["lt"] - 1 for c in cells]
cont = [c["Lt"] for c in cells]
print("Wt:", [ (fl,pd) for fl in range(12) for pd in range(8) if all(o==max(fl,k)+pd for o,k in zip(obs,cont)) ][:6])
# M - ld - 1 vs Ld
obs = [c["M"] - c["ld"] - 1 for c in cells if c["M"] is not None]
cont = [c["Ld"] for c in cells if c["M"] is not None]
print("WdL:", [ (fl,pd) for fl in range(12) for pd in range(8) if all(o==max(fl,k)+pd for o,k in zip(obs,cont)) ][:6])
# rn - M - 1 vs mlen? rn = M + mlen + 1?
bad = [c["tag"] for c in cells if c["M"] is not None and c["rn"] != c["M"] + c["mlen"] + 1]
print("rn=M+mlen+1 violates:", bad[:10])
obs = [c["rt"] - c["rn"] - 1 for c in cells]
cont = [c["Rn"] for c in cells]
print("WnR:", [ (fl,pd) for fl in range(12) for pd in range(8) if all(o==max(fl,k)+pd for o,k in zip(obs,cont)) ][:6])
obs = [c["rd"] - c["rt"] - 1 for c in cells]
cont = [c["Rt"] for c in cells]
print("WtR:", [ (fl,pd) for fl in range(12) for pd in range(8) if all(o==max(fl,k)+pd for o,k in zip(obs,cont)) ][:6])
obs = [c["rule"] - c["rd"] - 1 for c in cells if c["rule"]]
cont = [c["Rd"] for c in cells if c["rule"]]
print("WdR:", [ (fl,pd) for fl in range(12) for pd in range(8) if all(o==max(fl,k)+pd for o,k in zip(obs,cont)) ][:6])
# lt vs max(Ln,Rn)?
obs = [c["lt"] for c in cells]
cont = [max(c["Ln"], c["Rn"]) for c in cells]
print("lt(max(Ln,Rn)):", [ (fl,pd) for fl in range(12) for pd in range(8) if all(o==max(fl,k)+pd for o,k in zip(obs,cont)) ][:6])
print()
