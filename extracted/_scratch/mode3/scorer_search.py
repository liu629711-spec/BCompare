#!/usr/bin/env python3
"""Which scorer variant makes BC's oracle path DP-optimal?

For each control cell (archived oracle XML), compute:
  * V_bc   = value of BC's own emitted alignment under the variant scorer
  * V_opt  = DP optimum over the same box under the variant scorer
A variant is consistent only if V_bc == V_opt for every control cell
(BC's alignment engine is a DP, so its output must be optimal).

Usage: python scorer_search.py
"""
from __future__ import annotations
import itertools, pathlib, sys, xml.etree.ElementTree as ET
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import simulate_mode3 as S

RUNS = pathlib.Path(r"D:\Rea\product\verify\runs")

# control cells: (tag, note) -- swap family (must stay) + zip family (must stay)
CONTROLS = [
    ("tiny", "swap"), ("MD-pad0", "swap"), ("MF-pad2", "swap"),
    ("MF-pad5", "swap"), ("GR-3x13", "swap"), ("GR-4x13", "swap"),
    ("GR-5x13", "swap"), ("GR-6x13", "swap"), ("MF-pad10", "swap"),
    ("AX-20x10", "swap"), ("AX-13x2", "swap"), ("AX-100x2", "swap"),
    ("AX-2x13", "swap"), ("AX-2x100", "swap"),
    ("AX-10x20", "zip"), ("GR-10x13", "zip"), ("GR-22x13", "zip"),
    ("MB-pad11", "zip"), ("MB-pad14", "zip"), ("AX-11x14", "zip"),
    ("AX-12x12", "zip"), ("AX-12x100", "zip"), ("AX-14x11", "zip"),
]


def find(tag):
    for d in sorted(RUNS.glob("gateb-*")):
        p = d / "reports" / f"{tag}.oracle.xml"
        if p.exists():
            return (d / "fixtures" / f"{tag}-L.txt",
                    d / "fixtures" / f"{tag}-R.txt", p)
    return None


def oracle_rows(path):
    t = ET.parse(path); fc = t.getroot().find("filecomparison")
    out = []
    for el in fc:
        st = el.get("status")
        if st is None:
            continue
        l = r = None
        for c in el:
            if c.tag == "text":
                if c.get("ltid") is not None:
                    l = int(c.get("ltid"))
                if c.get("rtid") is not None:
                    r = int(c.get("rtid"))
        out.append((st, l, r))
    return out


def make_scorer(variant):
    """Return score(li, rj) for one LineSet pair, parameterised by variant."""
    u = variant["u"]            # length multiplier inside raw
    pen = variant["pen"]        # ("4m1", "const", "3m1")
    floor = variant["floor"]    # clamp of the penalty branch
    same = variant["same"]      # "weights" | "lens"

    def build(LS_L, LS_R):
        def sc(li, rj):
            A, B = int(LS_L.klen[li]), int(LS_R.klen[rj])
            if LS_L.key[li] == LS_R.key[rj]:
                if A == 0 or B == 0:
                    return -10
                base = ((LS_L.weights[li] + LS_R.weights[rj]) if same == "weights"
                        else (A + B)) * 2
                return base - 1 if A != B else base
            if A == 0 or B == 0:
                v = -4 * (A + B) - 1
                return max(min(v, -11), -40)
            c = sum(min(a, b) for a, b in zip(LS_L.hist[li].tolist(),
                                              LS_R.hist[rj].tolist()))
            raw = 3 * c - u * A - u * B
            if raw < 1:
                if pen == "4m1":
                    return max(raw * 4 - 1, floor)
                if pen == "3m1":
                    return max(raw * 3 - 1, floor)
                return floor
            return (raw * 25) // min(A, B)
        return sc
    return build


def dp_optimum(n, m, sc, gap=20):
    F = np.zeros((n + 1, m + 1), dtype=np.int64)
    for i in range(1, n + 1):
        F[i, 0] = F[i - 1, 0] - gap
    for j in range(1, m + 1):
        F[0, j] = F[0, j - 1] - gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            F[i, j] = max(F[i - 1, j - 1] + sc(i - 1, j - 1),
                          F[i, j - 1] - gap, F[i - 1, j] - gap)
    return int(F[n, m])


def bc_path_value(rows, sc, gap, n, m):
    """Value of the oracle alignment; 'different'/'similar'/'same' rows are
    matched pairs, orphan rows cost one gap. Contiguity is not re-checked --
    an invalid oracle would show up as V_bc > V_opt."""
    v = 0
    for st, l, r in rows:
        if st in ("same", "similar", "different"):
            v += sc(l - 1, r - 1)
        else:
            v -= gap
    return v


VARIANTS = []
for u in (1, 2, 3, 4):
    for pen in ("4m1", "3m1", "const"):
        for floor in (-40, -24, -20):
            for same in ("weights", "lens"):
                VARIANTS.append({"u": u, "pen": pen, "floor": floor, "same": same})


def main() -> int:
    data = []
    for tag, fam in CONTROLS:
        hit = find(tag)
        if not hit:
            print(f"missing fixture {tag}")
            continue
        lp, rp, op = hit
        L = lp.read_text(encoding="utf-8-sig").splitlines()
        R = rp.read_text(encoding="utf-8-sig").splitlines()
        data.append((tag, fam, L, R, oracle_rows(op)))

    print(f"{len(data)} controls\n")
    winners = []
    for variant in VARIANTS:
        build = make_scorer(variant)
        ok = 0
        fails = []
        for tag, fam, L, R, rows in data:
            LS_L = S.LineSet(L); LS_R = S.LineSet(R)
            sc = build(LS_L, LS_R)
            vo = dp_optimum(len(L), len(R), sc)
            vb = bc_path_value(rows, sc, 20, len(L), len(R))
            if vb == vo:
                ok += 1
            else:
                fails.append((tag, fam, vb, vo))
        tag = (f"u={variant['u']} pen={variant['pen']} floor={variant['floor']} "
               f"same={variant['same']}")
        print(f"{ok:3}/{len(data)}  {tag}")
        if ok == len(data):
            winners.append(tag)
        elif ok >= len(data) - 3:
            for f in fails:
                print(f"        {f[0]:12} {f[1]:5} V_bc={f[2]:6} V_opt={f[3]:6}")
    print("\nFULLY CONSISTENT:", winners or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
