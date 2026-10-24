#!/usr/bin/env python3
"""A vs MIXEDv2 flip sets, identical harness (2026-10-15)."""
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")
from handler_eval import run_case as run_a
from mixed2_eval import make_mixed2, MAXW
from model_s import load_cases

rcases, fcases = load_cases()
rc_m = make_mixed2(MAXW)
A_cfg = dict(anchors="scan", keep="overwrite-left")
ra = sum(run_a(c, **A_cfg) == w for _, c, w in rcases)
fa = sum(run_a(c, **A_cfg) == w for _, c, w in fcases)
rm = sum(rc_m(c, w) for _, c, w in rcases)
fm = sum(rc_m(c, w) for _, c, w in fcases)
print(f"A       recorded {ra}/{len(rcases)}  fuzz {fa}/{len(fcases)}")
print(f"MIXEDv2 recorded {rm}/{len(rcases)}  fuzz {fm}/{len(fcases)}")
only_a = [nm for nm, c, w in rcases + fcases
          if run_a(c, **A_cfg) == w and not rc_m(c, w)]
only_m = [nm for nm, c, w in rcases + fcases
          if not run_a(c, **A_cfg) == w and rc_m(c, w)]
print("A only:", only_a)
print("S only:", only_m)
