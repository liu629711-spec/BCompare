#!/usr/bin/env python3
"""Scratch: flag-polarity discriminator for the decoded scan (2026-10-15).

The decoded `FUN_140e738a0` branches are fixed; what is NOT yet pinned is
what the per-side flag table means:

  P0  F=1 ⟺ "line is unimportant"   (the shipping model)
  P1  F=1 ⟺ "line carries important content"

Same branch skeleton either way; the polarity swap changes which side is
advanced when the flags differ, and which branch runs when they agree:
  advance-differ: the F==0 side is advanced
  link-agree-important: equal -> flush pending + emit pair; unequal -> pin
  link-agree-unimportant: equal -> flush pending + emit pair; unequal -> break

Combined with the suffix-trim gate S (stop trimming when the key repeats
inside the interval), four configs are graded on both corpora.
"""
from __future__ import annotations

import pathlib
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))

from m26_model_grade import collect, facts, fmt_of, split_bc  # noqa: E402
from m55_model_lab import parse_xml_rows  # noqa: E402
import m55_anchor_eval as E  # noqa: E402
from collections import Counter  # noqa: E402


def scan_p(ids_l, ids_r, sig_l, sig_r):
    """Decoded scan with P1 semantics: F=1 ⟺ significant (has content).
    sig_* = the F table. Returns (pairs, intervals)."""
    n, m = len(ids_l), len(ids_r)
    i = j = 0
    pi = pj = -1
    pairs, intervals = [], []
    while i < n and j < m:
        fl, fr = sig_l[i], sig_r[j]
        if fl == 0:                     # branch 1: F_left == 0
            if fr != 0:
                # F_left==0 & F_right!=0 -> LAB -> F_left==0 -> advance LEFT
                if pi < 0:
                    pi = i
                i += 1
            else:
                # both insignificant: pair-or-pin on ids
                if pi < 0 and pj < 0:
                    if ids_l[i] != ids_r[j]:
                        pi, pj = i, j
                    else:
                        pairs.append((i, j))
                else:
                    if pi < 0:
                        pi = i
                    if pj < 0:
                        pj = j
                i += 1
                j += 1
        else:                           # branch 2: F_left != 0 -> LAB
            if fr == 0:
                # F_left!=0 & F_right==0 -> advance RIGHT
                if pj < 0:
                    pj = j
                j += 1
            else:
                # both significant: equal -> flush pending + emit pair;
                # unequal -> BREAK the whole scan
                if ids_l[i] != ids_r[j]:
                    break
                if pi >= 0 or pj >= 0:
                    if pi < 0:
                        pi = i
                    if pj < 0:
                        pj = j
                    intervals.append((pi, pj, i - 1, j - 1))
                    pi = pj = -1
                pairs.append((i, j))
                i += 1
                j += 1
    if pi >= 0:
        i = pi
    if pj >= 0:
        j = pj
    if i < n and j < m:
        intervals.append((i, j, n - 1, m - 1))
    return pairs, intervals


def handler_s(ls, rs, ctx, depth=0, *, gate=False):
    """Interval handler with optional suffix-trim gate S."""
    if not ls or not rs or depth > 64:
        return []
    stl, str_, ids, un = ctx
    pairs = []
    pre = 0
    while pre < len(ls) and pre < len(rs) and ids[0][ls[pre]] == ids[1][rs[pre]]:
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
        if gate and (rc[ids[1][rs[-1 - suf]]] > 1 or lc[ids[0][ls[-1 - suf]]] > 1):
            break
        suf += 1
    tail = [(ls[len(ls) - 1 - k], rs[len(rs) - 1 - k]) for k in range(suf)]
    if suf:
        ls, rs = ls[:len(ls) - suf], rs[:len(rs) - suf]
    if not ls or not rs:
        pairs.extend(tail)
        return pairs
    up = E.unique_pairs(ls, rs, ids)
    if up:
        anchors = E.lis_overwrite_left(up)
        pairs.extend(_rec(ls, rs, anchors, ctx, depth, gate))
    else:
        pairs.extend(E.nw_fill(ls, rs, ctx))
    pairs.extend(tail)
    return pairs


def _rec(ls, rs, anchors, ctx, depth, gate):
    out = []
    li = ri = 0
    for (al, ar) in anchors:
        sl = [x for x in ls[li:] if x < al]
        sr = [x for x in rs[ri:] if x < ar]
        if sl and sr:
            out.extend(handler_s(sl, sr, ctx, depth + 1, gate=gate))
        out.append((al, ar))
        while li < len(ls) and ls[li] <= al:
            li += 1
        while ri < len(rs) and rs[ri] <= ar:
            ri += 1
    sl, sr = ls[li:], rs[ri:]
    if sl and sr:
        out.extend(handler_s(sl, sr, ctx, depth + 1, gate=gate))
    return out


def model(case, *, polarity, gate):
    n, m, ctx = E.build_ctx(case)
    ids_l, ids_r = ctx[2]
    un_l, un_r = ctx[3]            # True = unimportant
    if polarity == "P0":
        # P0 reading (the shipping model): unimportant lines carry per-side
        # unique ids and the scan stops at a both-unimportant pair.
        pairs, intervals = E.greedy_scan(ids_l, ids_r, un_l, un_r)
    else:
        # P1 reading: F=1 ⟺ "significant content" over the same skeleton.
        sig_l = [0 if u else 1 for u in un_l]
        sig_r = [0 if u else 1 for u in un_r]
        pairs, intervals = scan_p(ids_l, ids_r, sig_l, sig_r)
    out = list(pairs)
    for (l0, r0, l1, r1) in intervals:
        ls = list(range(max(l0, 0), min(l1, n - 1) + 1))
        rs = list(range(max(r0, 0), min(r1, m - 1) + 1))
        if ls and rs:
            out.extend(handler_s(ls, rs, ctx, gate=gate))
    return E.finish(case, out)


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

    for polarity in ("P0", "P1"):
        for gate in (False, True):
            r_ok = sum(model(c, polarity=polarity, gate=gate) == w
                       for _, c, w in rcases)
            f_ok = sum(model(c, polarity=polarity, gate=gate) == w
                       for _, c, w in fcases)
            fails = [nm for nm, c, w in fcases
                     if model(c, polarity=polarity, gate=gate) != w]
            print(f"{polarity} gate={int(gate)}  recorded {r_ok}/{len(rcases)}"
                  f"  fuzz {f_ok}/{len(fcases)}  fails={fails}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
