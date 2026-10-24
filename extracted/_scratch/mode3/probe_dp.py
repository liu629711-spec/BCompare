#!/usr/bin/env python3
"""Numerical probe of W-off1990 band1: compare sim scores vs hand scores, vectorized vs scalar DP."""
from __future__ import annotations
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import simulate_mode3 as S

fx = pathlib.Path(r"D:\Rea\product\verify\runs\gateb-width6-20261015T182844Z\fixtures")
L = (fx / "W-off1990-L.txt").read_text(encoding="utf-8", newline="").splitlines()
R = (fx / "W-off1990-R.txt").read_text(encoding="utf-8", newline="").splitlines()
LS_L = S.LineSet(L); LS_R = S.LineSet(R)
uniq = {k: i for i, k in enumerate(sorted(set(LS_L.key) | set(LS_R.key)))}
LS_L.codes = np.array([uniq[k] for k in LS_L.key], dtype=np.int64)
LS_R.codes = np.array([uniq[k] for k in LS_R.key], dtype=np.int64)

# band1 box (0-based): L 100..2092, R 2090..4082
a0, a1, b0, b1 = 100, 2092, 2090, 4082
print("sample lines: L2082(0b2081)=", repr(L[2081]), " R4082(0b4081)=", repr(R[4081]))
for pair in [(2081, 4081), (2083, 4081), (2084, 4082), (2082, 4082), (2082, 4081), (2081, 4082)]:
    i, j = pair
    sc = S.score_matrix(LS_L, LS_R, [i], [j])[0, 0]
    print(f"score L{i+1}={L[i]!r} vs R{j+1}={R[j]!r}: {sc}  keys {LS_L.key[i]!r} {LS_R.key[j]!r}")

# scalar NW over the FULL band1 box, direct indexing (no reversal trick)
def scalar_nw(a0, a1, b0, b1):
    n = a1 - a0 + 1; m = b1 - b0 + 1
    G = S.GAP
    F = np.zeros((m + 1, n + 1), dtype=np.int64)
    D = np.zeros((m + 1, n + 1), dtype=np.int8)
    F[0, 1:] = -G * np.arange(1, n + 1)
    D[0, 1:] = 1
    F[1:, 0] = -G * np.arange(1, m + 1)
    D[1:, 0] = 2
    Sfull = S.score_matrix(LS_L, LS_R, range(a0, a1 + 1), range(b0, b1 + 1))
    mm = m; nn = n
    for r in range(1, mm + 1):
        for c in range(1, nn + 1):
            diag = F[r - 1, c - 1] + Sfull[nn - c, mm - r]
            left = F[r, c - 1] - G
            up = F[r - 1, c] - G
            best, dirv = diag, 3
            if left > best:
                best, dirv = left, 1
            if up > best:
                best, dirv = up, 2
            F[r, c] = best; D[r, c] = dirv
    # traceback from (m, n): cell (r,c) pairs a0+(n-c) with b0+(m-r)
    steps = []
    r, c = mm, nn
    while r > 0 and c > 0:
        dv = D[r, c]
        if dv == 3:
            steps.append(("p", a0 + nn - c, b0 + mm - r)); r -= 1; c -= 1
        elif dv == 2:
            steps.append(("ro", None, b0 + mm - r)); r -= 1
        else:
            steps.append(("lo", a0 + nn - c, None)); c -= 1
    while c > 0:
        steps.append(("lo", a0 + nn - c, None)); c -= 1
    while r > 0:
        steps.append(("ro", None, b0 + mm - r)); r -= 1
    steps.reverse()
    return steps, F[mm, nn]

steps, tot = scalar_nw(a0, a1, b0, b1)
print("scalar NW corner F =", tot)
# path around divergence
sel = [s for s in steps if s[1] is not None and 2075 <= s[1] <= 2095 or s[2] is not None and 4075 <= s[2] <= 4095]
print("scalar path near L2076..2096/R4076..4096:")
for s in sel[:40]:
    print("  ", s)

# compare vectorized nw_fill on the same box
vsteps, eL, eR = S.nw_fill(LS_L, LS_R, L, R, a0, a1, b0, b1, True)
vset = [s for s in vsteps if s[1] is not None and 2075 <= s[1] <= 2095 or s[2] is not None and 4075 <= s[2] <= 4095]
print("vectorized path same region:")
for s in vset[:40]:
    print("  ", s)
