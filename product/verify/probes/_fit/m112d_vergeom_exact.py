#!/usr/bin/env python3
"""M112d: exact geometry, slicing by DISPLAY column (no regex guessing)."""
from __future__ import annotations
import pathlib

RUNS = pathlib.Path(r"D:\Rea\product\verify\runs")
CELLS = [
    ("m112-versurface-20261019T135402Z", ["V1-sbs-equal","V3-sbs-diff","V5-sbs-com","V6-sbs-ms",
        "V7-sbs-plain-vs-pe","V8-sbs-plain-both","V23-sbs-reg-pair","V24-sbs-dll"]),
    ("m112b-verfields-20261019T153141Z", ["W1-one-field","W2a-filedescription","W2b-originalfilename",
        "W2c-legaltrademarks","W3-blank-comments","W5-long-value","W7-same-res-diff-size",
        "W8-truncated-pe","W11-ignore-one-field","W12-tail-differs"]),
]
def d(s): return sum(2 if ord(c) > 0x2e80 else 1 for c in s)
def rd(p):
    raw = p.read_bytes()
    return raw.decode("utf-16-le") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8-sig", errors="replace")
def cpos(s):
    """char -> (disp_offset, char)"""
    out, w = [], 0
    for ch in s:
        out.append((w, ch)); w += d(ch)
    return out
def slice_disp(s, a, b):
    return "".join(c for o, c in cpos(s) if a <= o < b)

for run, tags in CELLS:
    for tag in tags:
        f = RUNS / run / "reports" / f"{tag}.out"
        if not f.exists(): continue
        ls = rd(f).splitlines()
        hi = next((i for i, l in enumerate(ls) if l.count("名称") >= 2), None)
        if hi is None: continue
        hdr, rule = ls[hi], ls[hi+1]
        rows = [r for r in ls[hi+2:] if not (r.strip() and set(r.strip()) <= {"-"})]
        pos = cpos(hdr)
        ld = next(o for o, c in pos if c == "值")
        rn = [o for o, c in pos if c == "名"][1]
        rd_ = [o for o, c in pos if c == "值"][1]
        # marker col: the '=' position in the first row that has one (from cpos)
        mcol = None
        for r in rows:
            for o, c in cpos(r):
                if c in "=<>+-":
                    i = [x[0] for x in cpos(r)].index(o)
                    seq = cpos(r)
                    if i > 0 and i + 1 < len(seq) and seq[i-1][1] == " " and seq[i+1][1] == " ":
                        mcol = o; break
            if mcol is not None: break
        ln = max((d(slice_disp(r, 0, ld).rstrip()) for r in rows), default=0)
        lv = max((d(slice_disp(r, ld, mcol if mcol else d(r)).rstrip()) for r in rows), default=0)
        if mcol is not None:
            rnmax = max((d(slice_disp(r, mcol+2, rd_).rstrip()) for r in rows), default=0)
            rvmax = max((d(slice_disp(r, rd_, 10**6).rstrip()) for r in rows), default=0)
        else:
            rnmax = rvmax = 0
        print(f"{tag:24} ld={ld:>3} mcol={str(mcol):>4} rn={rn:>4} rd={rd_:>4} rule={len(rule):>4} | "
              f"ln={ln:>3} lv={lv:>3} rnmax={rnmax:>3} rv={rvmax:>3} | "
              f"ld-1-ln={ld-1-ln:>3} mcol-ld-lv={str(mcol and mcol-ld-lv):>4} rn-mcol={str(mcol and rn-mcol):>4} rd-rn-rnmax={rd_-rn-rnmax:>3} rule-rd-rv={len(rule)-rd_-rvmax:>4}")
