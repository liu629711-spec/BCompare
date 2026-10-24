#!/usr/bin/env python3
"""Mixed model: 140e74b60 handler as the main tier, but its EMPTY-UNIQUE-LIS
intervals delegate to the 140e73b40 window engine (decoded gate branch,
140e74b60 lines 303-306) instead of the plain NW filler.

Motivation (2026-10-15): pure Model S (window engine everywhere) closes
f0059/f0062 but loses the 9 unique-tier cases (case-swap-align, al-swap-blocks,
similar-preference, al-move-down, f0041). Model A (unique-LIS + NW) keeps those
9 but leaves f0059/f0062 open. The window engine is what 140e74b60 ALREADY
delegates to when the unique tier is empty, so a faithful port keeps LIS where
it fires and uses the window only where BC itself would.

The window engine here is a corrected, self-contained port of the decode:
  140e733b0 L-shape walk (up-then-left) collecting 140e73040 diagonal runs at
  unvisited cells (earliest-run-per-diagonal), visited-bitmap marks each cell;
  run = maximal equal-hash diagonal, weight = sum of (wl+wr) per line;
  >4999 aborts the window, >500 records a candidate {len, weight, l, r}.
  140e74100 truncates to the interval, quicksort by weight desc, resolves
  overlaps against later candidates (containment trims the head, recompute
  weight, sub-500 -> drop; partial-not-inside -> drop), then emits anchors in
  ascending (l,r) with NW between.
"""
from __future__ import annotations

import pathlib
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")

from scan2_eval import scan2, nw_fill, emit_rows  # noqa: E402
from handler_eval import unique_pairs, patience_pairs  # noqa: E402
from model_s import load_cases, run_weight_line  # noqa: E402

GAP = 20
MAXW = 10 ** 9


def collect_runs(l0, r0, lend, rend, ids_l, ids_r, wl, wr, W):
    """140e733b0 + 140e73040 over the window [l0..wl_][r0..wr_].
    Returns candidate lists [ln, weight, l, r] in discovery order."""
    wl_ = min(l0 + W - 1, lend)
    wr_ = min(r0 + W - 1, rend)
    visited = set()
    cands = []

    def start(l, r):
        if (l, r) in visited:
            return None
        i, j = l, r
        acc = 0
        ln = 0
        while i <= lend and j <= rend and ids_l[i] == ids_r[j]:
            acc += run_weight_line(wl[i], wr[j], True)
            ln += 1
            visited.add((i, j))
            i += 1
            j += 1
            if acc > 4999:
                return "ABORT"
        if ln > 0 and acc > 500:
            return [ln, acc, l, r]
        return None

    res = start(l0, r0)
    if res == "ABORT":
        return [], True
    if res:
        cands.append(res)
    x, y = l0, r0
    while x < wl_ or y < wr_:
        if x + 1 <= wl_:
            x += 1
            res = start(x, y)
            if res == "ABORT":
                return cands, True
            if res:
                cands.append(res)
        if y + 1 <= wr_:
            y += 1
            res = start(x, y)
            if res == "ABORT":
                return cands, True
            if res:
                cands.append(res)
    return cands, False


def resolve(cands, lend, rend, wl, wr):
    """140e74100: truncate, weight-desc sort, overlap-resolve vs LATER."""
    out = []
    for c in cands:
        ln, acc, l, r = c
        if lend < l + ln - 1 or rend < r + ln - 1:
            ln = min(ln, lend - l + 1, rend - r + 1)
            if ln <= 0:
                continue
        # recomputed weight always (matches 140e74080 recompute on trim; for
        # untrimmed this is a no-op sum equal to acc)
        acc = sum(run_weight_line(wl[l + k], wr[r + k], True) for k in range(ln))
        if acc < 500:
            continue
        out.append([ln, acc, l, r])
    out.sort(key=lambda c: (-c[1], c[3], c[2]))
    k = 0
    while k < len(out):
        al, ar, la = out[k][2], out[k][3], out[k][0]
        ae_l, ae_r = al + la - 1, ar + la - 1
        m2 = k + 1
        trimmed = False
        while m2 < len(out):
            B = out[m2]
            if B[0] <= 0:
                m2 += 1
                continue
            bl, br, lb = B[2], B[3], B[0]
            be_l, be_r = bl + lb - 1, br + lb - 1
            overlap = (bl <= ae_l or br <= ae_r) and (al <= be_l or ar <= be_r)
            if not overlap:
                m2 += 1
                continue
            inside_ab = ((bl < al and br < ar) and (al <= be_l or ar <= be_r)
                         and (be_l < ae_l and be_r < ae_r))
            inside_ba = ((al < bl and ar < br) and (bl <= ae_l or br <= ae_r)
                         and (ae_l < be_l and ae_r < be_r))
            if inside_ab:
                d = min(al - bl, ar - br)
                B[2] += d
                B[3] += d
                B[0] = lb - d
                if B[0] > 0:
                    B[1] = sum(run_weight_line(wl[B[2] + t], wr[B[3] + t], True)
                               for t in range(B[0]))
                    if B[1] < 500:
                        B[0] = 0
                else:
                    B[0] = 0
                trimmed = True
            elif inside_ba:
                d = max(ae_l - bl + 1, ae_r - br + 1)
                B[0] = max(lb - d, 0)
                B[2] += d
                B[3] += d
                if B[0] > 0:
                    B[1] = sum(run_weight_line(wl[B[2] + t], wr[B[3] + t], True)
                               for t in range(B[0]))
                    if B[1] < 500:
                        B[0] = 0
                trimmed = True
            else:
                B[0] = -1
            m2 += 1
        if trimmed:
            out[k + 1:] = sorted(out[k + 1:], key=lambda c: (-c[1], c[3], c[2]))
        k += 1
    out = [c for c in out if c[0] > 0]
    out.sort(key=lambda c: (c[3], c[2]))
    return out


def window_fill(ls, rs, ids, un, stl, str_, wl, wr, W):
    """Engine over a rectangular interval given as index lists ls, rs."""
    if not ls or not rs:
        return []
    ids_l, ids_r = ids
    un_l, un_r = un
    # map local positions to global doc indices via ls/rs (already global)
    l0, r0 = ls[0], rs[0]
    lend, rend = ls[-1], rs[-1]
    pairs = []
    pos = (l0, r0)
    while pos[0] <= lend and pos[1] <= rend:
        cands, aborted = collect_runs(pos[0], pos[1], lend, rend,
                                      ids_l, ids_r, wl, wr, W)
        anchors = resolve(cands, lend, rend, wl, wr)
        cur_l, cur_r = pos
        for (ln, acc, l, r) in anchors:
            g_l = [i for i in range(cur_l, l)]
            g_r = [j for j in range(cur_r, r)]
            g_l = [i for i in g_l if i in set(ls)]
            g_r = [j for j in g_r if j in set(rs)]
            if g_l and g_r:
                pairs.extend(nw_fill(g_l, g_r, stl, str_, ids, un))
            for t in range(ln):
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


def mixed_handler(ls, rs, ids, un, stl, str_, wl, wr, *, W, depth=0):
    """140e74b60 main tier; empty-unique-LIS intervals -> window engine."""
    pairs = []
    if not ls or not rs or depth > 64:
        return pairs
    ids_l, ids_r = ids
    pre = 0
    while (pre < len(ls) and pre < len(rs)
           and ids_l[ls[pre]] == ids_r[rs[pre]]):
        pairs.append((ls[pre], rs[pre]))
        pre += 1
    ls = ls[pre:]
    rs = rs[pre:]
    if not ls or not rs:
        return pairs
    suf = 0
    while (suf < len(ls) - 1 and suf < len(rs) - 1
           and ids_l[ls[-1 - suf]] == ids_r[rs[-1 - suf]]):
        suf += 1
    tail = [(ls[len(ls) - 1 - k], rs[len(rs) - 1 - k]) for k in range(suf)]
    ls = ls[:len(ls) - suf]
    rs = rs[:len(rs) - suf]
    if not ls or not rs:
        pairs.extend(tail)
        return pairs
    up = unique_pairs(ls, rs, ids_l, ids_r)
    if up:
        anchors = patience_pairs(up, keep="overwrite-left")
        li = ri = 0
        for (al, ar) in anchors:
            sub_l = [x for x in ls[li:] if x < al]
            sub_r = [x for x in rs[ri:] if x < ar]
            if sub_l and sub_r:
                pairs.extend(mixed_handler(sub_l, sub_r, ids, un, stl, str_,
                                           wl, wr, W=W, depth=depth + 1))
            pairs.append((al, ar))
            while li < len(ls) and ls[li] <= al:
                li += 1
            while ri < len(rs) and rs[ri] <= ar:
                ri += 1
        sub_l = ls[li:]
        sub_r = rs[ri:]
        if sub_l and sub_r:
            pairs.extend(mixed_handler(sub_l, sub_r, ids, un, stl, str_,
                                       wl, wr, W=W, depth=depth + 1))
    else:
        pairs.extend(window_fill(ls, rs, ids, un, stl, str_, wl, wr, W))
    pairs.extend(tail)
    return pairs


def make_mixed(W, wgt, un_id):
    def run_case(case, want=None):
        left, right, tl, tr, fmt = case
        n, m = len(left), len(right)
        stl = [t.strip() for t in left]
        str_ = [t.strip() for t in right]
        un_l = [not t for t in tl]
        un_r = [not t for t in tr]
        if un_id == "strip":
            ids_l = [t if t else stl[i] for i, t in enumerate(tl)]
            ids_r = [t if t else str_[j] for j, t in enumerate(tr)]
        else:
            ids_l = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
            ids_r = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
        if wgt == "key":
            wl = [len(k) for k in ids_l]
            wr = [len(k) for k in ids_r]
        else:
            wl = [len(t) for t in stl]
            wr = [len(t) for t in str_]
        ids = (ids_l, ids_r)
        un = (un_l, un_r)
        anch, intervals = scan2(ids_l, ids_r, un_l, un_r)
        pairs = list(anch)
        for (i0, j0, i1, j1) in intervals:
            ls = list(range(max(i0, 0), min(i1, n - 1) + 1))
            rs = list(range(max(j0, 0), min(j1, m - 1) + 1))
            if ls and rs:
                pairs.extend(mixed_handler(ls, rs, ids, un, stl, str_,
                                          wl, wr, W=W))
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
    watch = ["f0059", "f0062", "f0040", "f0092", "f0017"]
    rc = make_mixed(MAXW, "key", "unique")
    r_ok = sum(rc(c, w) for _, c, w in rcases)
    f_ok = sum(rc(c, w) for _, c, w in fcases)
    det = {nm: rc(c, w) for nm, c, w in fcases if nm in watch}
    print(f"MIXED wgt=key ids=unique  recorded {r_ok}/{len(rcases)}"
          f"  fuzz {f_ok}/{len(fcases)}  {det}")
    # which unique-tier cases remain and which f-cases are new failures
    failr = [nm for nm, c, w in rcases if not rc(c, w)]
    print(f"  recorded fails ({len(failr)}): {failr}")
    failf = [nm for nm, c, w in fcases if not rc(c, w)]
    print(f"  fuzz fails ({len(failf)}): {failf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
