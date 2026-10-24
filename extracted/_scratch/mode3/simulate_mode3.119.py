#!/usr/bin/env python3
"""Faithful offline simulator of BC's mode3 align engine (CLI descriptor
0x140e71510: interval vtable slot = FUN_140e73b40; NO anchor pass, NO gate B).

Evidence: _scratch/gateb/ANALYSIS.md, runs/gateb-alwaysbanded-*/ (D1),
140e73b40.c 140e733b0.c 140e73040.c 140e74100.c 140e74660.c 140e74080.c
140e75c50.c 140e726b0.c. 0-based internally; oracle XML ids are 1-based.

Key decoded facts encoded here:
  * CLI whole-file interval => uVar3/param_6 == 1 for EVERY band
    (140e73b40.c:19 ORs against the TABLE end, computed once). Consequences:
      - candidates are never box-clipped/re-weighted (140e74100.c:34 skip)
      - after emitting runs: tail NW SUPPRESSED, box end clips to cursor-1
        (140e74100.c:152-167)
      - with no runs, tail NW uses stop_at_edge=1 (walk halts when either
        index hits 0; *param_4/*param_5 clip to the consumed coordinate,
        140e74660.c:119-124)
      - gap NW between cursor and run start always param_6=0 => full consume
        (local_60=0 at 140e74100.c:135)
  * box = [cur .. min(end, cur+W-1)] per side, W=1993 (140e733b0.c:25-36)
  * wave: origin first, then per step advance head x,y and sweep column
    i=x..bL0 at row y, then rows j=y-1..bR0 at column x (140e733b0.c:43-76;
    re-scans are cheap because the seen bitmap skips covered cells)
  * run = diagonal while hash keys equal, EXTENDS PAST the box to the table
    end (140e73040.c:30-57, bounded by 140e722a0 clamp to table end only);
    recorded iff weight > 500; weight line = non-blank len+30 / blank 2*len+50
    / len0 blank 10 / len0 empty 1 (140e75c50 corrected)
  * resolve: sort (-weight, startR, startL); nested overlap
    (contained-later-run truncated to min(dL,dR); earlier-run overlap shifted
    by MAX(aEndL-bL+1, aEndR-bR+1); other overlap killed); re-sort by
    (startR, startL); emit walk with gap NW [cursor .. runStart-1] before each
  * NW 140e74660: F(r,c)=max(F(r-1,c-1)+score, F(r,c-1)-20, F(r-1,c)-20),
    in-place row recurrence (left is the SAME-ROW value -- sequential dep),
    BC tie priority: default diag; left wins only strict >; up wins only
    strict > current best. Walk from (m,n); reversed coords: cell (r,c) pairs
    L[a0+n-c] with R[b0+m-r]. stop_at_edge halts at first axis reaching 0.
  * score 140e726b0 + f0092 plain rule: ws-removed text, case kept;
    same-key: (wl+wr)*2 - (ka!=kb lengths) with wl/wr = important-text length;
    either empty: clamp [-40,-11] on -4*(la+lb)-1, same-key empty -> -10;
    else char-histogram intersection raw=3*common-la-lb, raw<1 ->
    max(raw*4-1,-40), else (raw*25)//min(la,lb).
  * one-sided tail chunks of <=200 rows (140e73b40.c:34-51, step +199)

Known accepted residuals (documented, do not hard-code around):
  big1 K=1 300-char line: provider vtbl+0x60 len semantics UNKNOWN (§3) --
  oracle never pairs it even at off=1000 while our weight reading would let
  NW pair same-key lines; marked UNRESOLVED.
"""
from __future__ import annotations
import numpy as np
from collections import defaultdict

W = 1993
GAP = 20
CAND_GATE = 500

# ---------------------------------------------------------------- weights/scores

def line_weight(text: str) -> int:
    if len(text) == 0:
        return 1
    if text.strip() == "":
        return 2 * len(text) + 50
    return len(text) + 30

def ws_removed(line: str) -> str:
    return "".join(line.split())

def fold_key(line: str) -> str:
    return ws_removed(line).lower()

def pair_status(ltxt: str, rtxt: str) -> str:
    """BC verdict for an emitted pair (plain grammar): raw equal -> same;
    anchor-key (ws-removed, case-folded) equal -> similar; else different."""
    if ltxt == rtxt:
        return "same"
    if fold_key(ltxt) and fold_key(ltxt) == fold_key(rtxt):
        return "similar"
    return "different"

class LineSet:
    """Precomputed inputs for one side.  Plain-format parity with the product:
    key = ws-removed LOWER-cased line (BC hash id; '' means unimportant ->
    never equal across sides); scorer text = ws-removed, case kept (f0092)."""
    def __init__(self, lines):
        kws = [ws_removed(ln) for ln in lines]
        # blank/unimportant lines get unique per-position keys (never pair via
        # run equality), mirroring AlignKey::Unimportant{side,index}.
        self.key = [t.lower() if t else "\0#%d" % i for i, t in enumerate(kws)]
        self.ktext = kws
        self.klen = np.array([len(t) for t in self.ktext], dtype=np.int64)
        self.rawlen = np.array([len(ln) for ln in lines], dtype=np.int64)
        chars = sorted({ch for t in self.ktext for ch in t})
        idx = {ch: k for k, ch in enumerate(chars)}
        self.chars = chars
        self.idx = idx
        self.hist = np.zeros((len(lines), max(len(chars), 1)), dtype=np.int64)
        for a, t in enumerate(self.ktext):
            h = self.hist[a]
            for ch in t:
                h[idx[ch]] += 1
        self.weights = np.array([line_weight(ln) for ln in lines], dtype=np.int64)

def score_matrix(LS_a, LS_b, la, lb):
    """Vectorized 140e726b0 over the given BLOCKS of left/right lines
    (ws-removed text, plain format). same_key uses normalized keys.
    All arrays are block-local: rows follow la order, cols follow lb."""
    A = LS_a.klen[la][:, None]
    B = LS_b.klen[lb][None, :]
    common = np.zeros((len(la), len(lb)), dtype=np.int64)
    idxb = LS_b.idx
    ha = LS_a.hist[la]
    hb = LS_b.hist[lb]
    for ci, ch in enumerate(LS_a.chars):
        cj = idxb.get(ch)
        if cj is None:
            continue
        common += np.minimum(ha[:, ci][:, None], hb[:, cj][None, :])
    import os
    variant = os.environ.get("S_VARIANT", "formula")
    raw = 3 * common - A - B
    lo = np.maximum(np.minimum(A, B), 1)
    if variant == "pen40":
        s = np.where(raw < 1, -40, (raw * 25) // lo).astype(np.int64)
    elif variant == "forbid":
        s = np.where(raw < 1, -5000, (raw * 25) // lo).astype(np.int64)
    elif variant == "sub18":
        s = np.where(raw < 1, -18, (raw * 25) // lo).astype(np.int64)
    else:
        s = np.where(raw < 1, np.maximum(raw * 4 - 1, -40), (raw * 25) // lo).astype(np.int64)
    v = -4 * (A + B) - 1
    wall = np.where(v < -39, -40, np.minimum(v, -11)).astype(np.int64)
    s = np.where((A == 0) | (B == 0), wall, s)
    ka = np.array([LS_a.key[i] for i in la])
    kb = np.array([LS_b.key[j] for j in lb])
    samek = ka[:, None] == kb[None, :]
    # same-key branch: FUN_140e74a70 weights (len+30 family), -1 when the
    # compared text lengths differ (A/B = ws-removed lengths).
    import os as _os
    if _os.environ.get("S_SAMEKEY", "weights") == "lens":
        Wa = A
        Wb = B
    else:
        Wa = LS_a.weights[la][:, None]
        Wb = LS_b.weights[lb][None, :]
    sc = (Wa + Wb) * 2 - (A != B).astype(np.int64)
    s = np.where(samek & (A > 0) & (B > 0), sc, s)
    s = np.where(samek & ((A == 0) | (B == 0)), -10, s)
    return s

# ---------------------------------------------------------------- NW fill

def nw_fill(LS_L, LS_R, L, R, a0, a1, b0, b1, stop_at_edge):
    """140e74660 over inclusive [a0..a1] x [b0..b1], in-place row recurrence
    solved per row via running max: F(c) = max(M(c), F(c-1)-G) where
    M(c)=max(D(c),U(c)); returns (steps, clipL, clipR).
    BC cell (r,c) in 1..: pairs left a1-(c-1) with right b1-(r-1)."""
    if a1 < a0:
        return [("rightorphan", None, j) for j in range(b0, b1 + 1)], a1, b1
    if b1 < b0:
        return [("leftorphan", i, None) for i in range(a0, a1 + 1)], a1, b1
    n = a1 - a0 + 1
    m = b1 - b0 + 1
    la = list(range(a0, a1 + 1))
    lb = list(range(b0, b1 + 1))
    # rows = right reversed (row r pairs right b1-(r-1)), cols = left reversed
    Sfull = score_matrix(LS_R, LS_L, lb[::-1], la[::-1])
    fprev = -GAP * np.arange(0, n + 1, dtype=np.int64)
    d = np.zeros((m + 1, n + 1), dtype=np.int8)
    d[0, 1:] = 1
    d[1:, 0] = 2
    cvec = np.arange(1, n + 1)
    for r in range(1, m + 1):
        D = fprev[:-1] + Sfull[r - 1]
        U = fprev[1:] - GAP
        M = np.maximum(D, U)
        V = np.maximum.accumulate(np.concatenate(([fprev[0] - GAP], M + GAP * cvec)))
        F = V[1:] - GAP * cvec
        chain = V[:-1] - GAP * cvec          # F(c-1)-G, with F(0)=fprev[0]-G
        dirv = np.full(n, 3, dtype=np.int8)
        m1 = chain > D
        dirv[m1] = 1
        best = np.where(m1, chain, D)
        m2 = U > best
        dirv[m2] = 2
        fcur = np.empty(n + 1, dtype=np.int64)
        fcur[0] = fprev[0] - GAP
        fcur[1:] = F
        d[r, 1:] = dirv
        fprev = fcur
    steps = []
    r, c = m, n
    while not (r == 0 and c == 0):
        dv = int(d[r, c])
        if dv == 3:
            i = a1 - (c - 1); j = b1 - (r - 1)
            steps.append((pair_status(L[i], R[j]), i, j))
            r -= 1; c -= 1
        elif dv == 2:
            steps.append(("rightorphan", None, b1 - (r - 1)))
            r -= 1
        else:
            steps.append(("leftorphan", a1 - (c - 1), None))
            c -= 1
        if stop_at_edge and (r == 0 or c == 0):
            break
    if not stop_at_edge:
        while c > 0:
            steps.append(("leftorphan", a1 - (c - 1), None))
            c -= 1
        while r > 0:
            steps.append(("rightorphan", None, b1 - (r - 1)))
            r -= 1
        return steps, a1, b1
    return steps, a1 - c, b1 - r

# ---------------------------------------------------------------- collect/resolve

def collect_runs(LS_L, LS_R, L, R, bL0, bL1, bR0, bR1, le, re_):
    """Wave-order diagonal run collection inside the box (runs extend past box
    to the table end); candidates weight > 500.  BC first-touch time of box
    cell (u,v) is max(u,v) (sweep 1 for v>=u at step v, sweep 2 for u>v at
    step u; 140e733b0.c:47-76), and a diagonal run's cells have strictly
    increasing max(), so the run START is always scanned before its interior:
    ordering candidate starts by max(u,v) asc reproduces BC exactly.  Non-equal
    cells only ever self-mark (k=0), so bulk-marking them is equivalent."""
    cl, cr = LS_L.codes, LS_R.codes
    wl = LS_L.weights
    seen = ~(cl[bL0:bL1 + 1, None] == cr[None, bR0:bR1 + 1])
    eq = ~seen
    runs = []
    iu, jv = np.nonzero(eq)
    if len(iu):
        order = np.lexsort((iu, np.maximum(iu, jv)))
        for p in order:
            u = int(iu[p]); v = int(jv[p])
            if seen[u, v]:
                continue
            i = bL0 + u; j = bR0 + v
            k = 0
            while i + k <= le and j + k <= re_ and cl[i + k] == cr[j + k]:
                k += 1
            # BC marks the k run cells plus one beyond (already non-eq/bulk);
            # interior cells of this diagonal fall at larger max -> skipped.
            # Runs may extend PAST the box; only in-box cells are markable.
            lim = min(seen.shape[0] - u, seen.shape[1] - v)
            for t in range(1, min(k, lim)):
                seen[u + t, v + t] = True
            w = int(wl[i:i + k].sum())
            if w > CAND_GATE:
                runs.append((i, j, k, w))
    return runs

def resolve_runs(L, runs, bxL, bxR, whole_table):
    """140e74100.c:33-123. whole_table(param_6==1): no clip/reweight branch."""
    cands = [[sL, sR, ln, w] for (sL, sR, ln, w) in runs if ln > 0 and w > 0]
    if not cands:
        return []
    if not whole_table:
        for c in cands:
            c[2] = min(c[2], bxL - c[0] + 1, bxR - c[1] + 1)
            c[3] = sum(line_weight(L[c[0] + t]) for t in range(c[2]))
            if c[3] < 500:
                c[3] = 0
    # 140e73e80 comparator = weight(pivot)-weight(elem) (secondary ties
    # elem-startR-pivot, elem-startL-pivot) under Hoare partition =>
    # weight DESCENDING, startR ASC, startL ASC.
    cands.sort(key=lambda c: (-c[3], c[1], c[0]))
    for idx, a in enumerate(cands):
        if a[3] <= 0:
            continue
        aEndL, aEndR = a[0] + a[2] - 1, a[1] + a[2] - 1
        changed = False
        for b in cands[idx + 1:]:
            if b[3] <= 0:
                continue
            bEndL, bEndR = b[0] + b[2] - 1, b[1] + b[2] - 1
            if (b[0] <= aEndL or b[1] <= aEndR) and (a[0] <= bEndL or a[1] <= bEndR):
                if (b[0] < a[0] and b[1] < a[1] and (a[0] <= bEndL or a[1] <= bEndR)
                        and bEndL < aEndL and bEndR < aEndR):
                    b[2] = min(a[0] - b[0], a[1] - b[1])
                    b[3] = sum(line_weight(L[b[0] + t]) for t in range(b[2]))
                    if b[3] < 500:
                        b[3] = 0
                    changed = True
                elif (a[0] < b[0] and a[1] < b[1]
                      and (b[0] <= aEndL or b[1] <= aEndR)
                      and aEndL < bEndL and aEndR < bEndR):
                    sh = max(aEndL - b[0] + 1, aEndR - b[1] + 1)
                    b[2] -= sh; b[0] += sh; b[1] += sh
                    b[3] = sum(line_weight(L[b[0] + t]) for t in range(b[2])) if b[2] > 0 else 0
                    if b[3] < 500:
                        b[3] = 0
                    changed = True
                else:
                    b[3] = -1
        if changed:
            tail = cands[idx + 1:]
            tail.sort(key=lambda c: (-c[3], c[1], c[0]))
            cands[idx + 1:] = tail
    live = [c for c in cands if c[3] > 0]
    live.sort(key=lambda c: (c[1], c[0]))
    return [(c[0], c[1], c[2]) for c in live]

# ---------------------------------------------------------------- handler (140e74b60)

L_STAR = 9        # router: band iff len(L) >= L_STAR and len(R) >= 13
R_STAR = 13
HANDLER_WALL = 5000
DUP_GATE = 1001

def _handler_body(LS_L, LS_R, L, R, l0, l1, r0, r1, out):
    """One 140e74b60 call over inclusive [l0..l1] x [r0..r1] (0-based), emitting
    (status, li, rj) rows in document order."""
    if l0 > l1 or r0 > r1:
        if l0 <= l1:
            out.extend(("leftorphan", i, None) for i in range(l0, l1 + 1))
        if r0 <= r1:
            out.extend(("rightorphan", None, j) for j in range(r0, r1 + 1))
        return
    # 1. prefix trim (140e74b60.c:63-85): equal keys emit as pairs outright.
    i, j = l0, r0
    while i <= l1 and j <= r1 and LS_L.key[i] == LS_R.key[j]:
        i += 1; j += 1
    out.extend((pair_status(L[k], R[k - l0 + r0]), k, k - l0 + r0)
               for k in range(l0, i))
    # 2. suffix trim.
    a, b = l1, r1
    while a >= i and b >= j and LS_L.key[a] == LS_R.key[b]:
        a -= 1; b -= 1
    suffix = [(k, k - l1 + r1) for k in range(a + 1, l1 + 1)]
    if i > a or j > b:
        if i <= a:
            out.extend(("leftorphan", k, None) for k in range(i, a + 1))
        if j <= b:
            out.extend(("rightorphan", None, k) for k in range(j, b + 1))
        out.extend((pair_status(L[k], R[rk]), k, rk) for k, rk in suffix)
        return
    # 3. left uniqueness dictionary (duplicates poison to -1, local_74 counts).
    ldict = {}
    dups = 0
    for k in range(i, a + 1):
        key = LS_L.key[k]
        if key in ldict:
            ldict[key] = -1
            dups += 1
        else:
            ldict[key] = k
    # 4. right pass: unique-unique pairs only.
    pairs = {}                    # right pos -> left pos
    rseen = {}
    for k in range(j, b + 1):
        key = LS_R.key[k]
        lp = ldict.get(key)
        if lp is None or lp == -1:
            continue
        if key in rseen:
            first = rseen[key]
            pairs.pop(first, None)
            ldict.pop(key, None)
            continue
        rseen[key] = k
        pairs[k] = lp
    # 5. patience LIS over right order; chain reconstructed from the last tail.
    tails = []                    # increasing left positions
    tail_r = []                   # their right positions
    prev = {}
    for k in range(j, b + 1):
        lv = pairs.get(k)
        if lv is None:
            continue
        if tails and tails[-1] < lv:
            pos = len(tails)
        else:
            pos = 0
            while pos < len(tails) and tails[pos] < lv:
                pos += 1
        if pos > 0:
            prev[k] = tail_r[pos - 1]
        if pos == len(tails):
            tails.append(lv); tail_r.append(k)
        else:
            tails[pos] = lv; tail_r[pos] = k
    chain = []
    if tails:
        cur = tail_r[-1]
        while cur is not None:
            chain.append((pairs[cur], cur))
            cur = prev.get(cur)
        chain.reverse()
    # 6. emit.
    if chain:
        cl, cr = i, j
        for al, ar in chain:
            _handler_body(LS_L, LS_R, L, R, cl, al - 1, cr, ar - 1, out)
            out.append((pair_status(L[al], R[ar]), al, ar))
            cl, cr = al + 1, ar + 1
        _handler_body(LS_L, LS_R, L, R, cl, a, cr, b, out)
    else:
        n, m = a - i + 1, b - j + 1
        if dups >= DUP_GATE or max(n, m) > HANDLER_WALL:
            out.extend(_band_rows(LS_L, LS_R, L, R, i, a, j, b))
        else:
            sub, _, _ = nw_fill(LS_L, LS_R, L, R, i, a, j, b, False)
            out.extend(sub)
    out.extend((pair_status(L[k], R[rk]), k, rk) for k, rk in suffix)


def handler_rows(LS_L, LS_R, L, R):
    out = []
    _handler_body(LS_L, LS_R, L, R, 0, len(L) - 1, 0, len(R) - 1, out)
    return out


def _band_rows(LS_L, LS_R, L, R, i, a, j, b):
    """The mode3 band walk restricted to [i..a] x [j..b] (positions absolute)."""
    rows = []
    lc, rc = i, j
    le, re_ = a, b
    while lc <= le or rc <= re_:
        if lc > le:
            k = min(re_, rc + 199)
            rows.extend(("rightorphan", None, t) for t in range(rc, k + 1))
            rc = k + 1
            continue
        if rc > re_:
            k = min(le, lc + 199)
            rows.extend(("leftorphan", t, None) for t in range(lc, k + 1))
            lc = k + 1
            continue
        bxL = min(le, lc + W - 1)
        bxR = min(re_, rc + W - 1)
        runs = collect_runs(LS_L, LS_R, L, R, lc, bxL, rc, bxR, le, re_)
        runs = resolve_runs(L, runs, bxL, bxR, whole_table=True)
        cl, cr = lc, rc
        for (sL, sR, ln) in runs:
            if cl <= sL - 1 or cr <= sR - 1:
                sub, _, _ = nw_fill(LS_L, LS_R, L, R, cl, sL - 1, cr, sR - 1, False)
                rows.extend(sub)
            for k in range(ln):
                rows.append((pair_status(L[sL + k], R[sR + k]), sL + k, sR + k))
            cl = sL + ln; cr = sR + ln
        if runs:
            endL, endR = cl - 1, cr - 1
        else:
            sub, endL, endR = nw_fill(LS_L, LS_R, L, R, cl, bxL, cr, bxR, True)
            rows.extend(sub)
        lc, rc = endL + 1, endR + 1
    return rows

# ---------------------------------------------------------------- top level

def simulate(L, R):
    import os
    n, m = len(L), len(R)
    LS_L = LineSet(L)
    LS_R = LineSet(R)
    uniq = {k: i for i, k in enumerate(sorted(set(LS_L.key) | set(LS_R.key)))}
    LS_L.codes = np.array([uniq[k] for k in LS_L.key], dtype=np.int64)
    LS_R.codes = np.array([uniq[k] for k in LS_R.key], dtype=np.int64)
    # Router (empirical, 42 archived cells, 0 misfits beyond the documented
    # min<3 exception): the interval goes to the 140e74b60 anchor handler when
    # `L <= 8 or R <= 12` (and both sides have >= 3 lines); otherwise the
    # 140e73b40 banded window engine runs. The asymmetry is measured:
    # (22,12) is handler-shaped while (12,22) is band-shaped, so the gate is
    # per-side, not on min/max.
    band = (min(n, m) < int(os.environ.get("MIN_TINY", 3))
            or (len(L) > int(os.environ.get("L_STAR", 8))
                and len(R) > int(os.environ.get("R_STAR", 12))))
    if not band:
        return handler_rows(LS_L, LS_R, L, R)
    rows = []
    lc, rc = 0, 0
    le, re_ = n - 1, m - 1
    while lc <= le or rc <= re_:
        if lc > le:
            k = min(re_, rc + 199)
            for j in range(rc, k + 1):
                rows.append(("rightorphan", None, j))
            rc = k + 1
            continue
        if rc > re_:
            k = min(le, lc + 199)
            for i in range(lc, k + 1):
                rows.append(("leftorphan", i, None))
            lc = k + 1
            continue
        bxL = min(le, lc + W - 1)
        bxR = min(re_, rc + W - 1)
        runs = collect_runs(LS_L, LS_R, L, R, lc, bxL, rc, bxR, le, re_)
        runs = resolve_runs(L, runs, bxL, bxR, whole_table=True)
        cl, cr = lc, rc
        endL, endR = bxL, bxR
        for (sL, sR, ln) in runs:
            if cl <= sL - 1 or cr <= sR - 1:
                sub, _, _ = nw_fill(LS_L, LS_R, L, R, cl, sL - 1, cr, sR - 1, False)
                rows.extend(sub)
            for k in range(ln):
                rows.append((pair_status(L[sL + k], R[sR + k]), sL + k, sR + k))
            cl = sL + ln; cr = sR + ln
        if runs:
            endL, endR = cl - 1, cr - 1
        else:
            sub, endL, endR = nw_fill(LS_L, LS_R, L, R, cl, bxL, cr, bxR, True)
            rows.extend(sub)
        lc, rc = endL + 1, endR + 1
    return rows
