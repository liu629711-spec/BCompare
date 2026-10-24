#!/usr/bin/env python3
"""M112c: refit the version-report geometry in DISPLAY columns.
For every archived sbs cell, print the four label positions, the marker
column, and the per-side max content widths (name/value, display cols).
"""
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

def positions(s):
    """[(display offset, ch)] for each char."""
    out, w = [], 0
    for ch in s:
        out.append((w, ch)); w += d(ch)
    return out

for run, tags in CELLS:
    for tag in tags:
        f = RUNS / run / "reports" / f"{tag}.out"
        if not f.exists():
            print(f"{tag}: MISSING"); continue
        ls = rd(f).splitlines()
        hi = next((i for i, l in enumerate(ls) if l.count("名称") >= 2), None)
        if hi is None:
            print(f"{tag}: no header"); continue
        hdr, rule, rows = ls[hi], ls[hi+1], ls[hi+2:]
        while rows and set(rows[-1].strip()) <= {"-"}: rows.pop()
        pos = positions(hdr)
        p1 = [o for o, c in pos if c == "名"]
        v1 = [o for o, c in pos if c == "值"]
        # marker column: display offset of the first '=' / '<>' etc in a row
        mcol = None
        for r in rows:
            pr = positions(r)
            for o, c in pr:
                if c in "=<>+-" and r[o:o+1] in "=<>+-":
                    # a marker sits alone: surrounded by spaces
                    prev = pr[pr.index((o, c)) - 1][1] if pr.index((o, c)) else " "
                    nxt = pr[pr.index((o, c)) + 1][1] if pr.index((o, c)) + 1 < len(pr) else " "
                    if prev == " " and nxt == " ":
                        mcol = o; break
            if mcol is not None: break
        # content maxima: split each row at the marker
        ln = lv = rn_ = rv = 0
        for r in rows:
            if mcol is None: break
            pr = positions(r)
            # left part: [0, mcol)
            L = [c for o, c in pr if o < mcol]
            R = [c for o, c in pr if o > mcol]
            ls_ = "".join(L); rs_ = "".join(R)
            # left name = up to the first run of >=2 spaces
            import re
            m1 = re.match(r"^(\S+(?: \S+)*?) {2,}", ls_)
            m2 = re.match(r"^(\S+(?: \S+)*?) {2,}", rs_)
            if m1: ln = max(ln, d(m1.group(1)))
            if m2: rn_ = max(rn_, d(m2.group(1)))
            if m1: lv = max(lv, d(ls_[m1.end():].rstrip()))
            if m2: rv = max(rv, d(rs_[m2.end():].rstrip()))
        print(f"{tag:24} ld={v1[0]:>4} rn={p1[1] if len(p1)>1 else -1:>4} rd={v1[1] if len(v1)>1 else -1:>4} "
              f"rule={len(rule):>4} mcol={mcol}  ln={ln:>3} lv={lv:>3} rnmax={rn_:>3} rv={rv:>3}")
