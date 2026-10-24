#!/usr/bin/env python3
"""Empty-LIS emission triage (2026-10-15): 140e74b60 lines 243-307 show THREE
emission modes when the unique tier is empty:
  D  +0xac==0: diagonal 1:1 fill of min(n,m)+1 rows (paired by position,
     score-independent), remainder pure add/delete  -- lines 244-260
  N  +0xac!=0, gates pass: NW 140e74660            -- lines 275-302
  W  +0xac!=0, gate A/B fail: window engine 140e73b40 (no-op at size)
The handler model always picked N. f0059/f0062 want 4 positional pairs where
NW gives 0 -> test D. Same faithful harness (scan_faithful + handler_gate)."""
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")
from collections import Counter
import m55_anchor_eval as E
import faithful as F

def diag_fill(ls, rs, ctx):
    """D: pair (ls[k], rs[k]) for k in 0..min(n,m) (inclusive diagonal:
    min+1 rows per the decode at line 251 local_2c = min(n,m)+1)."""
    k = min(len(ls), len(rs)) + 1
    return [(ls[t], rs[t]) for t in range(min(k, len(ls), len(rs)))]

orig_handler = F.handler_gate

def make_handler(filler):
    def h(ls, rs, ctx, depth=0):
        if not ls or not rs or depth > 64:
            return []
        stl, str_, ids, un = ctx
        pairs = []
        pre = 0
        while (pre < len(ls) and pre < len(rs)
               and ids[0][ls[pre]] == ids[1][rs[pre]]):
            pairs.append((ls[pre], rs[pre])); pre += 1
        ls, rs = ls[pre:], rs[pre:]
        if not ls or not rs:
            return pairs
        lc = Counter(ids[0][i] for i in ls)
        rc = Counter(ids[1][j] for j in rs)
        suf = 0
        while (suf < len(ls) - 1 and suf < len(rs) - 1
               and ids[0][ls[-1 - suf]] == ids[1][rs[-1 - suf]]):
            if lc[ids[0][ls[-1 - suf]]] > 1 or rc[ids[1][rs[-1 - suf]]] > 1:
                break
            suf += 1
        tail = [(ls[len(ls) - 1 - k], rs[len(rs) - 1 - k]) for k in range(suf)]
        if suf:
            ls, rs = ls[:len(ls) - suf], rs[:len(rs) - suf]
        if not ls or not rs:
            pairs.extend(tail)
            return pairs
        up = E.unique_pairs(ls, rs, ids)
        if up:
            anchors = E.lis_overwrite_left(up)
            pairs.extend(F._rec(ls, rs, anchors, ctx, depth))
        else:
            pairs.extend(filler(ls, rs, ctx))
        pairs.extend(tail)
        return pairs
    return h

rcases = []
for c in E.collect():
    fmt = E.fmt_of(c["left_path"])
    rcases.append((pathlib.PurePath(c["src"]).name,
                   (c["left"], c["right"], E.facts(c["left"], fmt),
                    E.facts(c["right"], fmt), fmt),
                   [[s, i, j] for s, i, j in c["bc_rows"]]))
fz = REA / "product/verify/runs/m54-fuzz-20261014T170917Z"
from m55_model_lab import parse_xml_rows
fcases = []
for lp in sorted((fz / "fixtures").glob("*-L.*")):
    rp = pathlib.Path(str(lp).replace("-L.", "-R."))
    tag = lp.stem.split("-")[0]
    o = (fz / "reports" / f"{tag}.oracle.xml").read_bytes() \
        .decode("utf-8-sig", errors="replace")
    left, right = E.split_bc(lp.read_bytes()), E.split_bc(rp.read_bytes())
    fmt = E.fmt_of(str(lp))
    fcases.append((tag, (left, right, E.facts(left, fmt), E.facts(right, fmt), fmt),
                   parse_xml_rows(o)))

def grade(h):
    F.handler_gate = h
    def model(case):
        n, m, ctx = E.build_ctx(case)
        ids_l, ids_r = ctx[2]
        sig_l = [0 if u else 1 for u in ctx[3][0]]
        sig_r = [0 if u else 1 for u in ctx[3][1]]
        pairs, intervals = F.scan_faithful(ids_l, ids_r, sig_l, sig_r,
                                           pred_break=False, bi_pending=False)
        out = list(pairs)
        for (l0, r0, l1, r1) in intervals:
            ls = list(range(max(l0, 0), min(l1, n - 1) + 1))
            rs = list(range(max(r0, 0), min(r1, m - 1) + 1))
            if ls and rs:
                out.extend(h(ls, rs, ctx))
        return E.finish(case, out)
    r_ok = sum(model(c) == w for _, c, w in rcases)
    f_ok = sum(model(c) == w for _, c, w in fcases)
    fails = [nm for nm, c, w in fcases if model(c) != w]
    rfails = [nm for nm, c, w in rcases if model(c) != w]
    return r_ok, f_ok, rfails, fails

for name, h in [("N (nw, current)", make_handler(E.nw_fill)),
                ("D (diag fill)", make_handler(diag_fill))]:
    r_ok, f_ok, rfails, fails = grade(h)
    print(f"{name:18} recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}")
    print(f"    rec fails: {rfails}")
    print(f"    fuzz fails: {fails}")
