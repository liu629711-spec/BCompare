#!/usr/bin/env python3
"""Mixed model v2: faithful `140e74b60` handler (prefix trim, suffix trim WITH
the duplicate gate, unique-LIS main tier, recursion), but the EMPTY-LIS
interval falls back to the `140e73b40` window engine instead of plain NW
(140e74b60's decoded gate branch, lines 303-306). (2026-10-15)

v1 forgot the suffix-trim duplicate gate; this restores it (as in faithful.py).
Baseline to beat: 281/290 + 119/120.
"""
from __future__ import annotations

import pathlib
import sys
from collections import Counter

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")

from scan2_eval import scan2, nw_fill, emit_rows  # noqa: E402
from handler_eval import unique_pairs, patience_pairs  # noqa: E402
from mixed_eval import collect_runs, resolve  # noqa: E402
from model_s import load_cases, run_weight_line, make_model  # noqa: E402
import m55_anchor_eval as E  # noqa: E402
from handler_eval import run_case as run_a  # noqa: E402

MAXW = 10 ** 9


def window_fill(ls, rs, ids, un, stl, str_, wl, wr, W=MAXW):
    if not ls or not rs:
        return []
    ids_l, ids_r = ids
    l0, r0, lend, rend = ls[0], rs[0], ls[-1], rs[-1]
    ls_set, rs_set = set(ls), set(rs)
    pairs = []
    pos = (l0, r0)
    while pos[0] <= lend and pos[1] <= rend:
        cands, aborted = collect_runs(pos[0], pos[1], lend, rend,
                                      ids_l, ids_r, wl, wr, W)
        anchors = resolve(cands, lend, rend, wl, wr)
        cur_l, cur_r = pos
        for (ln, acc, l, r) in anchors:
            gl = [i for i in range(cur_l, l) if i in ls_set]
            gr = [j for j in range(cur_r, r) if j in rs_set]
            if gl and gr:
                pairs.extend(nw_fill(gl, gr, stl, str_, ids, un))
            for t in range(ln):
                if (l + t) in ls_set and (r + t) in rs_set:
                    pairs.append((l + t, r + t))
            cur_l, cur_r = l + ln, r + ln
        tl = [i for i in ls if cur_l <= i <= lend]
        tr = [j for j in rs if cur_r <= j <= rend]
        if tl and tr:
            pairs.extend(nw_fill(tl, tr, stl, str_, ids, un))
        if aborted or not anchors:
            break
        pos = (cur_l, cur_r)
    return sorted(set(pairs))


def mixed_handler(ls, rs, ctx, *, W, depth=0):
    stl, str_, ids, un, wl, wr = ctx
    if not ls or not rs or depth > 64:
        return []
    pairs = []
    pre = 0
    while (pre < len(ls) and pre < len(rs)
           and ids[0][ls[pre]] == ids[1][rs[pre]]):
        pairs.append((ls[pre], rs[pre]))
        pre += 1
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
                pairs.extend(mixed_handler(sl, sr, ctx, W=W, depth=depth + 1))
            pairs.append((al, ar))
            while li < len(ls) and ls[li] <= al:
                li += 1
            while ri < len(rs) and rs[ri] <= ar:
                ri += 1
        sl, sr = ls[li:], rs[ri:]
        if sl and sr:
            pairs.extend(mixed_handler(sl, sr, ctx, W=W, depth=depth + 1))
    else:
        pairs.extend(window_fill(ls, rs, ids, un, stl, str_, wl, wr, W))
    pairs.extend(tail)
    return pairs


def make_mixed2(W=MAXW):
    def run_case(case, want=None):
        left, right, tl, tr, fmt = case
        n, m = len(left), len(right)
        stl = [t.strip() for t in left]
        str_ = [t.strip() for t in right]
        un_l = [not t for t in tl]
        un_r = [not t for t in tr]
        ids_l = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
        ids_r = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
        wl = [len(k) for k in ids_l]
        wr = [len(k) for k in ids_r]
        ids = (ids_l, ids_r)
        un = (un_l, un_r)
        ctx = (stl, str_, ids, un, wl, wr)
        anch, intervals = scan2(ids_l, ids_r, un_l, un_r)
        pairs = list(anch)
        for (i0, j0, i1, j1) in intervals:
            ls = list(range(max(i0, 0), min(i1, n - 1) + 1))
            rs = list(range(max(j0, 0), min(j1, m - 1) + 1))
            if ls and rs:
                pairs.extend(mixed_handler(ls, rs, ctx, W=W))
        pairs = sorted(set(pairs))
        used_l = {i for i, _ in pairs}
        used_r = {j for _, j in pairs}
        lo = [i for i in range(n) if i not in used_l]
        ro = [j for j in range(m) if j not in used_r]
        rows = emit_rows(left, right, tl, tr, pairs, lo, ro)
        return rows if want is None else rows == want
    return run_case


def main():
    rcases, fcases = load_cases()
    watch = ["f0059", "f0062", "f0040", "f0092", "f0073", "f0021", "f0115",
             "f0041"]
    for W in (MAXW, 100, 32):
        rc = make_mixed2(W)
        r_ok = sum(rc(c, w) for _, c, w in rcases)
        f_ok = sum(rc(c, w) for _, c, w in fcases)
        det = {nm: rc(c, w) for nm, c, w in fcases if nm in watch}
        print(f"MIXEDv2 W={W:>10}  recorded {r_ok}/{len(rcases)}  "
              f"fuzz {f_ok}/{len(fcases)}  {det}")
    rc = make_mixed2()
    rfails = [nm for nm, c, w in rcases if not rc(c, w)]
    print(f"  recorded fails ({len(rfails)}): {rfails}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
