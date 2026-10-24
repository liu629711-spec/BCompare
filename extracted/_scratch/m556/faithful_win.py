#!/usr/bin/env python3
"""Clean discriminator (2026-10-15): faithful harness-A (scan_faithful +
handler_gate, pred_break=False/bi_pending=False, E.nw_fill fallback) vs the
SAME model with only the empty-unique-LIS fallback swapped to the 140e73b40
window engine. Any delta is attributable to the window layer alone.
Expect ZERO delta: the >500-weight candidate tier never fires at corpus size
(cand_stats: 0/334)."""
import pathlib, sys
REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")
from collections import Counter
import m55_anchor_eval as E
from scan2_eval import nw_fill, emit_rows
from handler_eval import unique_pairs, patience_pairs
from mixed_eval import collect_runs, resolve
from model_s import run_weight_line, load_cases
import faithful as F

MAXW = 10 ** 9

def window_fill(ls, rs, ctx, W=MAXW):
    stl, str_, ids, un = ctx
    if not ls or not rs:
        return []
    ids_l, ids_r = ids
    wl = [len(k) for k in ids_l]; wr = [len(k) for k in ids_r]
    l0, r0, lend, rend = ls[0], rs[0], ls[-1], rs[-1]
    pairs = []
    cands, aborted = collect_runs(l0, r0, lend, rend, ids_l, ids_r, wl, wr, W)
    anchors = resolve(cands, lend, rend, wl, wr)
    cur_l, cur_r = l0, r0
    for (ln, acc, l, r) in anchors:
        gl = [i for i in range(cur_l, l)]
        gr = [j for j in range(cur_r, r)]
        if gl and gr:
            pairs.extend(nw_fill(gl, gr, stl, str_, ids, un))
        for t in range(ln):
            pairs.append((l + t, r + t))
        cur_l, cur_r = l + ln, r + ln
    tl = [i for i in ls if cur_l <= i <= lend]
    tr = [j for j in rs if cur_r <= j <= rend]
    if tl and tr:
        pairs.extend(nw_fill(tl, tr, stl, str_, ids, un))
    return sorted(set(pairs))

def handler_win(ls, rs, ctx, depth=0):
    if not ls or not rs or depth > 64:
        return []
    stl, str_, ids, un = ctx
    pairs = []
    pre = 0
    while (pre < len(ls) and pre < len(rs)
           and ids[0][ls[pre]] == ids[1][rs[pre]]):
        pairs.append((ls[pre], rs[pre])); pre += 1
    ls, rs = ls[pre:], rs[pre:]
    if not ls or not rs:
        return pairs
    lc = Counter(ids[0][i] for i in ls)
    rc = Counter(ids[1][j] for j in rs)
    suf = 0
    while (suf < len(ls) - 1 and suf < len(rs) - 1
           and ids[0][ls[-1 - suf]] == ids[1][rs[-1 - suf]]):
        if lc[ids[0][ls[-1 - suf]]] > 1 or rc[ids[1][rs[-1 - suf]]] > 1:
            break
        suf += 1
    tail = [(ls[len(ls) - 1 - k], rs[len(rs) - 1 - k]) for k in range(suf)]
    if suf:
        ls, rs = ls[:len(ls) - suf], rs[:len(rs) - suf]
    if not ls or not rs:
        pairs.extend(tail)
        return pairs
    up = unique_pairs(ls, rs, ids[0], ids[1])
    if up:
        anchors = patience_pairs(up, keep="overwrite-left")
        li = ri = 0
        for (al, ar) in anchors:
            sl = [x for x in ls[li:] if x < al]
            sr = [x for x in rs[ri:] if x < ar]
            if sl and sr:
                pairs.extend(handler_win(sl, sr, ctx, depth + 1))
            pairs.append((al, ar))
            while li < len(ls) and ls[li] <= al: li += 1
            while ri < len(rs) and rs[ri] <= ar: ri += 1
        sl, sr = ls[li:], rs[ri:]
        if sl and sr:
            pairs.extend(handler_win(sl, sr, ctx, depth + 1))
    else:
        pairs.extend(window_fill(ls, rs, ctx))
    pairs.extend(tail)
    return pairs

def model_win(case):
    n, m, ctx = E.build_ctx(case)
    ids_l, ids_r = ctx[2]
    sig_l = [0 if u else 1 for u in ctx[3][0]]
    sig_r = [0 if u else 1 for u in ctx[3][1]]
    pairs, intervals = F.scan_faithful(ids_l, ids_r, sig_l, sig_r,
                                       pred_break=False, bi_pending=False)
    out = list(pairs)
    for (l0, r0, l1, r1) in intervals:
        ls = list(range(max(l0, 0), min(l1, n - 1) + 1))
        rs = list(range(max(r0, 0), min(r1, m - 1) + 1))
        if ls and rs:
            out.extend(handler_win(ls, rs, ctx))
    return E.finish(case, out)

rcases, fcases = load_cases()
ra_fa = sum(F.model(c, pred_break=False, bi_pending=False) == w for _, c, w in rcases)
fa_fa = sum(F.model(c, pred_break=False, bi_pending=False) == w for _, c, w in fcases)
ra_w = sum(model_win(c) == w for _, c, w in rcases)
fa_w = sum(model_win(c) == w for _, c, w in fcases)
print(f"faithful A          recorded {ra_fa}/{len(rcases)}  fuzz {fa_fa}/{len(fcases)}")
print(f"A + window fallback recorded {ra_w}/{len(rcases)}  fuzz {fa_w}/{len(fcases)}")
