#!/usr/bin/env python3
"""Locate divergent cells for W-off1990 band1 (variant B scoring).

Grid: r in 1..n over LEFT lines a0+r-1, c in 1..m over RIGHT lines b0+c-1.
F[r,c] = max(F[r-1,c-1]+score(Lr,Rc), F[r,c-1]-G (skip right, dir1),
             F[r-1,c]-G (skip left, dir2)); tie order diag > right-skip > left-skip
exactly as nw_fill/140e74660 but forward (equivalent transpose of reversed walk).
Walk the ORACLE path forward; report each cell whose stored dir disagrees, with
the 2x2 neighborhood scores/values."""
from __future__ import annotations
import sys, pathlib, xml.etree.ElementTree as ET
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import simulate_mode3 as S

fx = pathlib.Path(r"D:\Rea\product\verify\runs\gateb-width6-20261015T182844Z\fixtures")
rp = pathlib.Path(r"D:\Rea\product\verify\runs\gateb-width6-20261015T182844Z\reports\W-off1990.oracle.xml")
L = (fx / "W-off1990-L.txt").read_text(encoding="utf-8", newline="").splitlines()
R = (fx / "W-off1990-R.txt").read_text(encoding="utf-8", newline="").splitlines()
t = ET.parse(rp); fc = t.getroot().find("filecomparison")
want = []
for el in fc:
    st = el.get("status")
    if st is None: continue
    l = r = None
    for c in el:
        if c.tag == "text":
            if c.get("ltid") is not None: l = int(c.get("ltid"))
            if c.get("rtid") is not None: r = int(c.get("rtid"))
    want.append((st, l, r))

a0, a1, b0, b1 = 100, 2092, 2090, 4082
LS_L = S.LineSet(L); LS_R = S.LineSet(R)
uniq = {k: i for i, k in enumerate(sorted(set(LS_L.key) | set(LS_R.key)))}
LS_L.codes = np.array([uniq[k] for k in LS_L.key], dtype=np.int64)
LS_R.codes = np.array([uniq[k] for k in LS_R.key], dtype=np.int64)
n = a1 - a0 + 1; m = b1 - b0 + 1
G = S.GAP
Sfull = S.score_matrix(LS_L, LS_R, range(a0, a1 + 1), range(b0, b1 + 1))
F = np.zeros((n + 1, m + 1), dtype=np.int64)
D = np.zeros((n + 1, m + 1), dtype=np.int8)   # 3 diag, 1 skip-right, 2 skip-left
F[0, 1:] = -G * np.arange(1, m + 1); D[0, 1:] = 1
F[1:, 0] = -G * np.arange(1, n + 1); D[1:, 0] = 2
for r in range(1, n + 1):
    for c in range(1, m + 1):
        diag = F[r-1, c-1] + Sfull[r-1, c-1]
        skipR = F[r, c-1] - G
        skipL = F[r-1, c] - G
        best, dirv = diag, 3
        if skipR > best: best, dirv = skipR, 1
        if skipL > best: best, dirv = skipL, 2
        F[r, c] = best; D[r, c] = dirv

# oracle segment inside the box (forward doc order)
seg = []
for st, l, r in want:
    if l is None and r is not None and b0 <= r-1 <= b1:
        seg.append(("ro", None, r-1))
    elif r is None and l is not None and a0 <= l-1 <= a1:
        seg.append(("lo", l-1, None))
    elif l is not None and r is not None:
        if a0 <= l-1 <= a1 and b0 <= r-1 <= b1:
            seg.append(("p", l-1, r-1))
print("oracle steps in box:", len(seg), "expected", n + m - (n+m-len([s for s in seg if s[0]=='p'])) )
i = j = 0  # consumed left/right counts
report = []
for k, (kind, li, rj) in enumerate(seg):
    r, c = i + 1, j + 1
    dv = int(D[r, c])
    exp = {"p": 3, "ro": 1, "lo": 2}[kind]
    if dv != exp:
        diagv = F[r-1, c-1] + Sfull[r-1, c-1]
        skipRv = F[r, c-1] - G
        skipLv = F[r-1, c] - G
        li_ = a0 + i; rj_ = b0 + j
        report.append(dict(step=k, kind=kind, cell=(r, c), l=li_, r=rj_,
                           L=L[li_], R=R[rj_],
                           score=int(Sfull[i, j]), F_d=int(F[r-1,c-1]),
                           diag=int(diagv), skipR=int(skipRv), skipL=int(skipLv),
                           dpdir=dv, samekey=LS_L.key[li_] == LS_R.key[rj_]))
        if len(report) >= 20:
            break
    if kind == "p": i += 1; j += 1
    elif kind == "lo": i += 1
    else: j += 1
print("inconsistent:", len(report))
for x in report:
    print(x)
