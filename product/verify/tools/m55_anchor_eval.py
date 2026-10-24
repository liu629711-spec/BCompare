#!/usr/bin/env python3
"""M5.5-9 clean evaluation: the anchor-layer candidate vs the shipped model.

Self-contained (no imports from the earlier probe scripts) so the numbers
are reproducible from this file alone. Two models, one emitter:

  A  shipped: myers over AnchorKey ids, intervals filled by the decoded
     NW (score_text + pair_similarity `140e726b0`, gap 20, reversed
     coordinates). This is what product/core/src/align.rs does today.
  C  candidate: the decoded scan `140e738a0` (one pending-interval
     discipline, faithful branch polarities) over the SAME ids, with each
     flushed interval handed to the decoded interval handler
     `140e74b60`: common prefix/suffix trim, unique-unique key pairs,
     patience LIS with the decoded slot-overwrite rule (iterate left
     order, tails hold right indices, chain by the right index), recurse
     into the gaps, and the NW filler when no unique pair exists.

Both graded on the recorded corpus (290) and the m54 fuzz fixtures (120)
against the stored oracle rows. Writes runs/m55-anchor-eval-<ts>.json.
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))

from m26_model_grade import collect, facts, fmt_of, split_bc, myers, order_events
from m55_model_lab import parse_xml_rows

GAP = 20


# ---------------------------------------------------------------- scoring

def intersect(a, b):
    fa = Counter(a)
    return sum(min(fa.get(ch, 0), nb) for ch, nb in Counter(b).items())


def pair_similarity(a, b, same_key, wl, wr):
    """FUN_140e726b0, all three branches (as ported into the product)."""
    if same_key:
        if not a or not b:
            return -10
        s = (wl + wr) * 2
        return s - 1 if len(a) != len(b) else s
    if not a or not b:
        v = -4 * (len(a) + len(b)) - 1
        if v > -12:
            v = -11
        if v < -39:
            v = -40
        return v
    common = intersect(a, b)
    raw = common * 3 - len(a) - len(b)
    if raw < 1:
        return max(raw * 4 - 1, -40)
    return (raw * 25) // min(len(a), len(b))


def nw_fill(ls, rs, ctx):
    """FUN_140e74660: reversed-coordinate NW, gap 20, diag > left > right."""
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    stl, str_, ids, un = ctx
    f = [[0] * (n + 1) for _ in range(m + 1)]
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for c in range(1, n + 1):
        f[0][c] = f[0][c - 1] - GAP
        d[0][c] = 1
    for r in range(1, m + 1):
        f[r][0] = f[r - 1][0] - GAP
        d[r][0] = 2
        for c in range(1, n + 1):
            a, b = ls[n - c], rs[m - r]
            same = (not un[0][a]) and ids[0][a] == ids[1][b]
            best = f[r - 1][c - 1] + pair_similarity(
                stl[a], str_[b], same, len(ids[0][a]), len(ids[1][b]))
            k = 3
            if best < f[r][c - 1] - GAP:
                best, k = f[r][c - 1] - GAP, 1
            if best < f[r - 1][c] - GAP:
                best, k = f[r - 1][c] - GAP, 2
            f[r][c], d[r][c] = best, k
    pairs = []
    r, c = m, n
    while r != 0 or c != 0:
        k = d[r][c]
        if k == 3:
            pairs.append((ls[n - c], rs[m - r]))
            r -= 1
            c -= 1
        elif k == 2:
            r -= 1
        else:
            c -= 1
    return pairs


# ------------------------------------------------------- scan + handler (C)

def greedy_scan(ids_l, ids_r, un_l, un_r):
    """Faithful FUN_140e738a0 over the AnchorKey ids. Returns (pairs,
    intervals). Unimportant lines carry unique ids, so the both-unimportant
    unequal branch ends the scan (all-unimportant runs go to the handler)."""
    n, m = len(ids_l), len(ids_r)
    i = j = 0
    pi = pj = -1
    pairs, intervals = [], []
    while i < n and j < m:
        li, rj = not un_l[i], not un_r[j]
        if li and rj:
            if pi < 0 and pj < 0:
                if ids_l[i] == ids_r[j]:
                    pairs.append((i, j))
                else:
                    pi, pj = i, j
            else:
                if pi < 0:
                    pi = i
                if pj < 0:
                    pj = j
            i += 1
            j += 1
        elif li:                      # left important, right unimportant
            if pi < 0:
                pi = i
            i += 1
        elif rj:                      # left unimportant, right important
            if pj < 0:
                pj = j
            j += 1
        else:                         # both unimportant: unique ids -> end
            break
    if pi >= 0:
        i = pi
    if pj >= 0:
        j = pj
    intervals.append((i, j, n - 1, m - 1))
    return pairs, intervals


def unique_pairs(ls, rs, ids):
    cl = Counter(ids[0][i] for i in ls)
    cr = Counter(ids[1][j] for j in rs)
    left_pos = {ids[0][i]: i for i in ls if cl[ids[0][i]] == 1}
    out = []
    for j in rs:
        k = ids[1][j]
        if cr[k] == 1 and k in left_pos:
            out.append((left_pos.pop(k), j))
    return out


def lis_overwrite_left(pairs):
    """Patience LIS, decoded slot-overwrite rule: iterate in LEFT order,
    tails hold the right indices, and the chain is reconstructed by the
    right-index back links (the decoded local_50 array)."""
    seq = sorted(pairs, key=lambda p: p[0])
    tails, slots, back, left_of = [], [], {}, {}
    for (l, r) in seq:
        k = 0
        while k < len(tails) and tails[k] < r:
            k += 1
        if k == len(tails):
            tails.append(r)
            slots.append((l, r))
            left_of[r] = l
            if k > 0:
                back[r] = slots[k - 1][1]
        else:
            # overwrite the slot with the smaller right index (the decoded
            # `*(local_60 + local_38*4) = id` slot replacement)
            slots[k] = (l, r)
            tails[k] = r
            left_of[r] = l
            if k > 0:
                back[r] = slots[k - 1][1]
            else:
                back.pop(r, None)
    if not slots:
        return []
    chain, r = [], slots[-1][1]
    while True:
        chain.append(r)
        if r not in back:
            break
        r = back[r]
    return [(left_of[x], x) for x in reversed(chain)]


def handler(ls, rs, ctx, depth=0):
    """FUN_140e74b60 over one interval: prefix/suffix trim -> unique pairs
    -> LIS -> recurse into gaps -> NW when there is nothing unique."""
    if not ls or not rs or depth > 64:
        return []
    stl, str_, ids, un = ctx
    pairs = []
    pre = 0
    while (pre < len(ls) and pre < len(rs)
           and ids[0][ls[pre]] == ids[1][rs[pre]]):
        pairs.append((ls[pre], rs[pre]))
        pre += 1
    ls, rs = ls[pre:], rs[pre:]
    if not ls or not rs:
        return pairs
    suf = 0
    while (suf < len(ls) - 1 and suf < len(rs) - 1
           and ids[0][ls[-1 - suf]] == ids[1][rs[-1 - suf]]):
        suf += 1
    tail = [(ls[len(ls) - 1 - k], rs[len(rs) - 1 - k]) for k in range(suf)]
    if suf:
        ls, rs = ls[:len(ls) - suf], rs[:len(rs) - suf]
    up = unique_pairs(ls, rs, ids)
    if up:
        anchors = lis_overwrite_left(up)
        pairs.extend(_recurse(ls, rs, anchors, ctx, depth))
    else:
        pairs.extend(nw_fill(ls, rs, ctx))
    pairs.extend(tail)
    return pairs


def _recurse(ls, rs, anchors, ctx, depth):
    out = []
    li = ri = 0
    for (al, ar) in anchors:
        sub_l = [x for x in ls[li:] if x < al]
        sub_r = [x for x in rs[ri:] if x < ar]
        if sub_l and sub_r:
            out.extend(handler(sub_l, sub_r, ctx, depth + 1))
        out.append((al, ar))
        while li < len(ls) and ls[li] <= al:
            li += 1
        while ri < len(rs) and rs[ri] <= ar:
            ri += 1
    sub_l, sub_r = ls[li:], rs[ri:]
    if sub_l and sub_r:
        out.extend(handler(sub_l, sub_r, ctx, depth + 1))
    return out


# ---------------------------------------------------------------- drivers

def build_ctx(case):
    left, right, tl, tr, _fmt = case
    n, m = len(left), len(right)
    ids_l = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
    ids_r = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
    ctx = ([t.strip() for t in left], [t.strip() for t in right],
           (ids_l, ids_r), ([not t for t in tl], [not t for t in tr]))
    return n, m, ctx


def model_a(case):
    """Shipped model: myers anchors + NW interval filler."""
    n, m, ctx = build_ctx(case)
    ids_l, ids_r = ctx[2]
    pairs = list(myers(ids_l, ids_r))
    bounds = [(-1, -1)] + list(pairs) + [(n, m)]
    for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
        ls, rs = list(range(pl + 1, nl)), list(range(pr + 1, nr))
        if ls and rs:
            pairs.extend(nw_fill(ls, rs, ctx))
    return finish(case, pairs)


def model_c(case):
    """Candidate: decoded scan + interval handler."""
    n, m, ctx = build_ctx(case)
    ids_l, ids_r = ctx[2]
    pairs, intervals = greedy_scan(ids_l, ids_r, ctx[3][0], ctx[3][1])
    for (l0, r0, l1, r1) in intervals:
        ls = list(range(max(l0, 0), min(l1, n - 1) + 1))
        rs = list(range(max(r0, 0), min(r1, m - 1) + 1))
        if ls and rs:
            pairs.extend(handler(ls, rs, ctx))
    return finish(case, pairs)


def finish(case, pairs):
    left, right, tl, tr, _fmt = case
    n, m = len(left), len(right)
    pairs = sorted(set(pairs))
    used_l = {i for i, _ in pairs}
    used_r = {j for _, j in pairs}
    lo = [i for i in range(n) if i not in used_l]
    ro = [j for j in range(m) if j not in used_r]
    rows = []
    for kind, i, j in order_events(pairs, lo, ro):
        if kind == "pair":
            st = ("same" if left[i] == right[j]
                  else "similar" if tl[i] == tr[j] else "different")
            rows.append([st, i + 1, j + 1])
        elif kind == "left":
            rows.append(["leftsimilar" if not tl[i] else "leftorphan", i + 1, None])
        else:
            rows.append(["rightsimilar" if not tr[j] else "rightorphan", None, j + 1])
    return rows


def main() -> int:
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
        o = (fz / "reports" / f"{tag}.oracle.xml").read_bytes() \
            .decode("utf-8-sig", errors="replace")
        left, right = split_bc(lp.read_bytes()), split_bc(rp.read_bytes())
        fmt = fmt_of(str(lp))
        fcases.append((tag, (left, right, facts(left, fmt), facts(right, fmt), fmt),
                       parse_xml_rows(o)))

    res = {}
    for name, fn in (("A_shipped_myers_nw", model_a), ("C_scan_handler", model_c)):
        r_ok = sum(fn(c) == w for _, c, w in rcases)
        f_ok = sum(fn(c) == w for _, c, w in fcases)
        res[name] = {"recorded": [r_ok, len(rcases)], "fuzz": [f_ok, len(fcases)]}
        print(f"{name:22} recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}")

    flips = {"recorded": {"gain": [], "loss": []}, "fuzz": {"gain": [], "loss": []}}
    for nm, c, w in rcases:
        a, cc = model_a(c) == w, model_c(c) == w
        if a != cc:
            flips["recorded"]["gain" if cc else "loss"].append(nm)
    for nm, c, w in fcases:
        a, cc = model_a(c) == w, model_c(c) == w
        if a != cc:
            flips["fuzz"]["gain" if cc else "loss"].append(nm)
    print("recorded gains:", flips["recorded"]["gain"])
    print("recorded losses:", flips["recorded"]["loss"])
    print("fuzz gains:", flips["fuzz"]["gain"])
    print("fuzz losses:", flips["fuzz"]["loss"])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REA / "product/verify/runs" / f"m55-anchor-eval-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "m55-anchor-eval.json").write_text(json.dumps(
        {"results": res, "flips": flips}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"raw: {out / 'm55-anchor-eval.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
