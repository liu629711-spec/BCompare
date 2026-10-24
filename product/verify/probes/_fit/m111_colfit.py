#!/usr/bin/env python3
"""M111 offline column-geometry fit for the registry sbs table.

Observed integers per report (from headers via substring find; row fields
split at header column indices; marker = last `=`/`<>`/`+-`/`-+` inside the
window [ld, rn)):

  lt = header 类型 col;  ld = header 数据 col;  rn/rt/rd right cols; rule len.
  Fit targets:
    Wn_L  : left name column  -> lt  = ?
    Wt    : type column       -> ld  = lt + Wt + 1?
    Wd_L  : left data column  -> Mcol= ld + Wd_L ?
    Wd_R  : right data column -> rule= rd + Wd_R ?
    Wn_R/Wt_R: rt = rn + Wn_R + 1; rd = rt + Wt_R + 1

Also records the left/right CONTENT length maxes so the pad model
(floor? global-across-sides?) can be decided from the numbers.
"""
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

def load():
    for f in sorted(glob.glob(str(RUNS / "m101*" / "*summary*.json"))):
        for c in json.load(open(f, encoding="utf-8")):
            lines = c.get("lines", [])
            hdr = next((ln for ln in lines if "名称" in ln and "类型" in ln), None)
            if hdr is None: continue
            rules = [len(ln) for ln in lines if ln and set(ln) == {"-"}]
            body, in_body = [], False
            for ln in lines:
                if ln == hdr: in_body = True; continue
                if not in_body: continue
                if ln and set(ln) == {"-"}: continue
                if ln and not any(ln.startswith(p) for p in FRAME):
                    body.append(ln)
            yield c["tag"], hdr, body, (rules[0] if rules else None)

res = []
for tag, hdr, body, rule in load():
    lt = hidx(hdr, "类型")[0]; ld = hidx(hdr, "数据")[0]
    rn = hidx(hdr, "名称")[1]
    rt = hidx(hdr, "类型")[1]; rd = hidx(hdr, "数据")[1]
    Mn = hidx(hdr, "名称")[0]
    Mcol = None
    Ln = Ld = Rn = Rt = Rd = Lt_ = 0
    has_marker = False
    for ln in body:
        m = None
        for tok in ("<>", "+-", "-+", "="):
            i = ln.rfind(tok, ld)
            if i != -1 and i < rn:
                m = (tok, i); break
        # box-prefixed rows: the prefix sits inside name col; field split at
        # header cols still valid
        if m:
            has_marker = True
            tok, i = m
            Mcol = i if Mcol is None else Mcol
            mlen = len(tok)
        # left name [0,lt), left type [lt,ld)
        Ln = max(Ln, len(ln[:lt].rstrip()))
        Lt_ = max(Lt_, len(ln[lt:ld].rstrip()))
        if m and tok != "-+":
            Ld = max(Ld, len(ln[ld:Mcol].rstrip()))
        if m and tok == "-+":
            # empty left block up to rn: padding; content 0
            pass
        if m and tok not in ("+-",):
            Rn = max(Rn, len(ln[rn:rt].rstrip()))
            Rt = max(Rt, len(ln[rt:rd].rstrip()))
            Rd = max(Rd, len(ln[rd:].rstrip()))
        elif not m:
            # bare header row: name columns
            Rn = max(Rn, len(ln[rn:].rstrip()) if len(ln) > rn else 0)
    res.append(dict(tag=tag, Mn=Mn, lt=lt, ld=ld, rn=rn, rt=rt, rd=rd, rule=rule,
                    Mcol=Mcol, Ln=Ln, Lt=Lt_, Ld=Ld, Rn=Rn, Rt=Rt, Rd=Rd,
                    marker=has_marker))

print(f"{'tag':24}{'Mn':>3}{'Ln':>3}{'Rn':>3}{'Lt':>3}{'Rt':>3}{'Ld':>3}{'Rd':>3} "
      f"{'lt':>3}{'ld':>3}{'M':>4}{'rn':>4}{'rt':>3}{'rd':>3}{'rule':>5}   model?")
bad = []
for r in res:
    # candidate model
    Wn = max(r["Ln"], r["Rn"]) + 1              # name col incl intercol space?
    p_lt = max(r["Ln"], 1) + 2                   # tentative: content + 2
    p_ld = r["lt"] + max(r["Lt"], r["Rt"]) + 1
    Wd = max(r["Ld"], r["Rd"])
    p_M = r["ld"] + Wd + 1
    p_rn2 = (r["Mcol"] or 0) + 3
    p_rt = r["rn"] + max(r["Rn"], 1) + 2
    p_rd = r["rt"] + max(r["Rt"], r["Lt"]) + 1
    p_rule = r["rd"] + Wd + 1
    errs = []
    if p_lt != r["lt"]: errs.append(f"lt={r['lt']}~{p_lt}(Ln={r['Ln']},Rn={r['Rn']})")
    if p_ld != r["ld"]: errs.append(f"ld={r['ld']}~{p_ld}(Lt={r['Lt']},Rt={r['Rt']})")
    if r["Mcol"] is not None:
        if p_M != r["Mcol"]: errs.append(f"M={r['Mcol']}~{p_M}(Ld={r['Ld']},Rd={r['Rd']})")
        if p_rt != r["rt"]: errs.append(f"rt={r['rt']}~{p_rt}")
        if p_rd != r["rd"]: errs.append(f"rd={r['rd']}~{p_rd}")
        if r["rule"] and p_rule != r["rule"]: errs.append(f"rule={r['rule']}~{p_rule}")
    flag = "  ".join(errs)
    if errs: bad.append(r["tag"])
    print(f"{r['tag']:24}{r['Mn']:>3}{r['Ln']:>3}{r['Rn']:>3}{r['Lt']:>3}{r['Rt']:>3}"
          f"{r['Ld']:>3}{r['Rd']:>3} {r['lt']:>3}{r['ld']:>3}{str(r['Mcol']):>4}"
          f"{r['rn']:>4}{r['rt']:>3}{r['rd']:>3}{str(r['rule']):>5}  {flag}")
print("bad:", len(bad), "/", len(res))
