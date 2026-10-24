#!/usr/bin/env python3
"""Which cases flip between model A (scan + 140e74b60 handler) and
model S (scan + 140e73b40 window engine)? (2026-10-15)"""
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")
from scan2_eval import scan2, nw_fill, emit_rows
from handler_eval import handler, run_case as run_a
from model_s import load_cases, make_model
from m26_model_grade import facts, fmt_of  # noqa

rcases, fcases = load_cases()
rc = make_model(W=10**9, wgt="key", un_id="unique")
A_cfg = dict(anchors="scan", keep="overwrite-left")
only_a = []
only_s = []
both = 0
neither = []; 
for nm, c, w in rcases + fcases:
    oa = run_a(c, **A_cfg) == w
    os_ = rc(c, w)
    if oa and os_: both += 1
    elif oa: only_a.append(nm)
    elif os_: only_s.append(nm)
    else: neither.append(nm)
print(f"both pass: {both}")
print(f"A only ({len(only_a)}):", only_a)
print(f"S only ({len(only_s)}):", only_s)
print(f"neither ({len(neither)}):", neither[:40])
