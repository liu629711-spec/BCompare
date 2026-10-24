#!/usr/bin/env python3
"""Single-variable probe for f0092: is BC's 140e725f0 character-intersection
histogram CASE-INSENSITIVE under the default .txt (case-insensitive) rules?

Baseline faithful variant A vs A with only `intersect` case-folded.
Everything else (anchors, scan, handler, gates, NW shape, verdict layer)
untouched."""
from __future__ import annotations
import pathlib, sys
from collections import Counter

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, str(REA / "extracted" / "_scratch" / "m556"))

from m26_model_grade import collect, facts, fmt_of, split_bc
from m55_model_lab import parse_xml_rows
import m55_anchor_eval as E
import faithful

orig_intersect = E.intersect
def ci_intersect(a, b):
    fa = Counter(a.lower())
    return sum(min(fa.get(ch, 0), nb) for ch, nb in Counter(b.lower()).items())

def build_cases():
    rcases = []
    for c in collect():
        fmt = fmt_of(c["left_path"])
        rcases.append((pathlib.PurePath(c["src"]).name,
                       (c["left"], c["right"], facts(c["left"], fmt),
                        facts(c["right"], fmt), fmt),
                       [[s, i, j] for s, i, j in c["bc_rows"]]))
    fz = REA / "product/verify/runs/m54-fuzz-20261014T170917Z"
    fcases = []
    for lp in sorted((fz / "fixtures").glob("*-L.*")):
        rp = pathlib.Path(str(lp).replace("-L.", "-R."))
        tag = lp.stem.split("-")[0]
        o = (fz / "reports" / f"{tag}.oracle.xml").read_bytes().decode("utf-8-sig", errors="replace")
        left, right = split_bc(lp.read_bytes()), split_bc(rp.read_bytes())
        fmt = fmt_of(str(lp))
        fcases.append((tag, (left, right, facts(left, fmt), facts(right, fmt), fmt),
                       parse_xml_rows(o)))
    return rcases, fcases

def score(rf, label):
    rcases, fcases = rf
    cfg = dict(pred_break=False, bi_pending=False)
    r_ok = sum(faithful.model(c, **cfg) == w for _, c, w in rcases)
    f_ok = sum(faithful.model(c, **cfg) == w for _, c, w in fcases)
    rfails = [nm for nm, c, w in rcases if faithful.model(c, **cfg) != w]
    ffails = [nm for nm, c, w in fcases if faithful.model(c, **cfg) != w]
    print(f"{label}: recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}")
    print(f"   rec fails: {rfails}")
    print(f"   fuzz fails: {ffails}")
    return set(rfails), set(ffails)

def main():
    rf = build_cases()
    E.intersect = orig_intersect
    base_r, base_f = score(rf, "baseline   ")
    E.intersect = ci_intersect
    ci_r, ci_f = score(rf, "ci-fold int")
    print("\nregressed recorded:", sorted(ci_r - base_r))
    print("fixed recorded:    ", sorted(base_r - ci_r))
    print("regressed fuzz:    ", sorted(ci_f - base_f))
    print("fixed fuzz:        ", sorted(base_f - ci_f))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
