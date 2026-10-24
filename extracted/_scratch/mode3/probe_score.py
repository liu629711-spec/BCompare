#!/usr/bin/env python3
"""Scoring-variant experiment on W-off1990 band1 box.

Variants of 140e726b0 cross-key scoring (same-key branch fixed separately):
  B  current sim: histogram remap (raw<1 -> max(4r-1,-40); else 25r/minlen), walls.
  C  +0xac==0 branch: every differing-key pair = -18 (job+0x80==0).
  A  +0xac!=0 && +0x58!=0: raw char-intersection count (>=0), empty-text -> -18.
Also same-key variants:
  k0 current sim: (la+lb)*2 - (la!=lb)
  k1 binary-faithful: 2*(wa+wb) - (la!=lb), w = line weight (len+30 / 2len+50),
     and 2*(wa+wb)-... note: (wa+wb)*2 where wa=len+30 => (la+lb)*2+120 for non-blank.
     empty same-key: -10 in all.

Question: under which variant is the ORACLE path the DP-optimum of the band1 box?
"""
from __future__ import annotations
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import simulate_mode3 as S

fx = pathlib.Path(r"D:\Rea\product\verify\runs\gateb-width6-20261015T182844Z\fixtures")
rp = pathlib.Path(r"D:\Rea\product\verify\runs\gateb-width6-20261015T182844Z\reports\W-off1990.oracle.xml")
L = (fx / "W-off1990-L.txt").read_text(encoding="utf-8", newline="").splitlines()
R = (fx / "W-off1990-R.txt").read_text(encoding="utf-8", newline="").splitlines()
import xml.etree.ElementTree as ET
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

a0, a1, b0, b1 = 100, 2092, 2090, 4082  # band1 box (0-based)

# oracle path restricted to this box (rows emitted within [a0..a1] x [b0..b1] and orphans)
seg = []
for st, l, r in want:
    if l is not None and a0 <= l - 1 <= a1:
        if r is not None and b0 <= r - 1 <= b1:
            seg.append(("p", l - 1, r - 1))
        else:
            seg.append(("lo", l - 1, None))
    elif l is None and r is not None and b0 <= r - 1 <= b1:
        seg.append(("ro", None, r - 1))
print(f"oracle segment in box: {len(seg)} steps")
# summarize structure: runs of pure diagonal / orphans
prev = None; cnt = 0; struct = []
for s in seg:
    if s == prev: cnt += 1
    else:
        if prev is not None: struct.append((prev[0], cnt))
        prev = s; cnt = 1
struct.append((prev[0], cnt))
print("structure:", struct[:10], "...")
print("first steps:", seg[:6], "last steps:", seg[-6:])

LS_L = S.LineSet(L); LS_R = S.LineSet(R)
uniq = {k: i for i, k in enumerate(sorted(set(LS_L.key) | set(LS_R.key)))}
LS_L.codes = np.array([uniq[k] for k in LS_L.key], dtype=np.int64)
LS_R.codes = np.array([uniq[k] for k in LS_R.key], dtype=np.int64)

def score_block(a_idx, b_idx, variant, samek):
    la = list(a_idx); lb = list(b_idx)
    A = LS_L.klen[la][:, None]; B = LS_R.klen[lb][None, :]
    # char intersection
    common = np.zeros((len(la), len(lb)), dtype=np.int64)
    idxb = LS_R.idx
    ha = LS_L.hist[la]; hb = LS_R.hist[lb]
    for ci, ch in enumerate(LS_L.chars):
        cj = idxb.get(ch)
        if cj is None: continue
        common += np.minimum(ha[:, ci][:, None], hb[:, cj][None, :])
    raw = 3 * common - A - B
    if variant == "B":
        s = np.where(raw < 1, np.maximum(raw * 4 - 1, -40), (raw * 25) // np.maximum(np.minimum(A, B), 1))
        v = -4 * (A + B) - 1
        wall = np.where(v < -39, -40, np.minimum(v, -11))
        s = np.where((A == 0) | (B == 0), wall, s)
    elif variant == "C":
        s = np.full((len(la), len(lb)), -18, dtype=np.int64)
    elif variant == "A":
        s = common
        s = np.where((A == 0) | (B == 0), -18, s)
    ka = np.array([LS_L.key[i] for i in la]); kb = np.array([LS_R.key[j] for j in lb])
    same = ka[:, None] == kb[None, :]
    wa = LS_L.weights[la][:, None]; wb = LS_R.weights[lb][None, :]
    if samek == "k0":
        sc = (A + B) * 2 - (A != B)
    else:
        sc = (wa + wb) * 2 - (A != B)
    s = np.where(same & (A > 0) & (B > 0), sc, s)
    s = np.where(same & ((A == 0) | (B == 0)), -10, s)
    return s

def path_score(Sfull, seg, a0, b0):
    # walk: 'p' uses Sfull[i-a0, j-b0]; 'lo'/'ro' cost -20
    tot = 0
    for st, i, j in seg:
        if st == "p": tot += int(Sfull[i - a0, j - b0])
        else: tot -= 20
    return tot

def dp_opt(Sfull):
    m_, n_ = Sfull.shape
    G = 20
    F = np.zeros((m_ + 1, n_ + 1), dtype=np.int64)
    F[0, 1:] = -G * np.arange(1, n_ + 1); F[1:, 0] = -G * np.arange(1, m_ + 1)
    for r in range(1, m_ + 1):
        row = F[r]; prev = F[r - 1]
        for c in range(1, n_ + 1):
            d = prev[c - 1] + Sfull[r - 1, c - 1]
            left = row[c - 1] - G
            up = prev[c] - G
            row[c] = max(d, left, up)
    return F[m_, n_]

for variant in ["B", "C", "A"]:
    for samek in ["k0", "k1"]:
        Sfull = score_block(range(a0, a1 + 1), range(b0, b1 + 1), variant, samek)
        ps = path_score(Sfull, seg, a0, b0)
        opt = dp_opt(Sfull)
        print(f"variant {variant} samek {samek}: oracle-path={ps} dp-opt={opt} gap={opt-ps}")
