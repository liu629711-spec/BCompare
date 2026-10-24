#!/usr/bin/env python3
"""Scratch: faithful-scan variants A/B/C/D (2026-10-15, §18 prep).

Decode facts driving the variants:

* both significant, ids equal -> flush pending + pair; ids differ -> BREAK.
* both insignificant -> decode compares ids: equal (and no pending) -> pair;
  otherwise set pending and advance both.
* one side insignificant -> call the ctx predicate (vtable+0x28) first:
  nonzero -> BREAK the whole scan; zero -> advance the insignificant side.
  ctxB's predicate is `return 0`; ctxA's is a byte-table lookup whose value
  is not yet pinned, so both readings are tested.

A third fix is orthogonal and required: a flushed interval whose right (or
left) range is empty must NOT go to the handler (decode emits one-sided
runs there); passing it in with a `j-1` underflow is a bug.

Variants:
  A  current best: no pending-branch (break on both-insig), no predicate
  B  + both-insignificant pending branch (decode)
  C  + predicate always breaks
  D  B + C (fully faithful decode except the predicate's unknown value)
"""
from __future__ import annotations

import pathlib
import sys
from collections import Counter

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))

from m26_model_grade import collect, facts, fmt_of, split_bc  # noqa: E402
from m55_model_lab import parse_xml_rows  # noqa: E402
import m55_anchor_eval as E  # noqa: E402

GAP = 20


def scan_faithful(ids_l, ids_r, sig_l, sig_r, *, pred_break, bi_pending):
    n, m = len(ids_l), len(ids_r)
    i = j = 0
    pl = pr = -1
    pairs, intervals = [], []
    while i < n and j < m:
        sl, sr = sig_l[i], sig_r[j]
        if not sl and not sr:
            if bi_pending:
                if pl < 0 and pr < 0 and ids_l[i] == ids_r[j]:
                    pairs.append((i, j))
                else:
                    if pl < 0:
                        pl = i
                    if pr < 0:
                        pr = j
            else:
                break
            i += 1
            j += 1
        elif sl and sr:
            if ids_l[i] != ids_r[j]:
                break
            if pl >= 0 or pr >= 0:
                if pl < 0:
                    pl = i
                if pr < 0:
                    pr = j
                if pl <= i - 1 and pr <= j - 1:
                    intervals.append((pl, pr, i - 1, j - 1))
                pl = pr = -1
            pairs.append((i, j))
            i += 1
            j += 1
        elif not sl and sr:
            if pred_break:
                break
            if pl < 0:
                pl = i
            i += 1
        else:
            if pred_break:
                break
            if pr < 0:
                pr = j
            j += 1
    l0 = pl if pl >= 0 else i
    r0 = pr if pr >= 0 else j
    if l0 < n and r0 < m:
        intervals.append((l0, r0, n - 1, m - 1))
    return pairs, intervals


def handler_gate(ls, rs, ctx, depth=0):
    """§17 handler + suffix-trim gate (stop at a repeated key)."""
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
        if lc[ids[0][ls[-1 - suf]]] > 1 or rc[ids[1][rs[-1 - suf]]] > 1:
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
        pairs.extend(_rec(ls, rs, anchors, ctx, depth))
    else:
        pairs.extend(E.nw_fill(ls, rs, ctx))
    pairs.extend(tail)
    return pairs


def _rec(ls, rs, anchors, ctx, depth):
    out = []
    li = ri = 0
    for (al, ar) in anchors:
        sl = [x for x in ls[li:] if x < al]
        sr = [x for x in rs[ri:] if x < ar]
        if sl and sr:
            out.extend(handler_gate(sl, sr, ctx, depth + 1))
        out.append((al, ar))
        while li < len(ls) and ls[li] <= al:
            li += 1
        while ri < len(rs) and rs[ri] <= ar:
            ri += 1
    sl, sr = ls[li:], rs[ri:]
    if sl and sr:
        out.extend(handler_gate(sl, sr, ctx, depth + 1))
    return out


def model(case, *, pred_break, bi_pending):
    n, m, ctx = E.build_ctx(case)
    ids_l, ids_r = ctx[2]
    sig_l = [0 if u else 1 for u in ctx[3][0]]
    sig_r = [0 if u else 1 for u in ctx[3][1]]
    pairs, intervals = scan_faithful(ids_l, ids_r, sig_l, sig_r,
                                     pred_break=pred_break, bi_pending=bi_pending)
    out = list(pairs)
    for (l0, r0, l1, r1) in intervals:
        ls = list(range(max(l0, 0), min(l1, n - 1) + 1))
        rs = list(range(max(r0, 0), min(r1, m - 1) + 1))
        if ls and rs:
            out.extend(handler_gate(ls, rs, ctx))
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

    variants = {
        "A no-pred no-bi": dict(pred_break=False, bi_pending=False),
        "B no-pred +bi": dict(pred_break=False, bi_pending=True),
        "C +pred no-bi": dict(pred_break=True, bi_pending=False),
        "D +pred +bi": dict(pred_break=True, bi_pending=True),
    }
    for name, cfg in variants.items():
        r_ok = sum(model(c, **cfg) == w for _, c, w in rcases)
        f_ok = sum(model(c, **cfg) == w for _, c, w in fcases)
        rfails = [nm for nm, c, w in rcases if model(c, **cfg) != w]
        ffails = [nm for nm, c, w in fcases if model(c, **cfg) != w]
        print(f"{name:16} recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}")
        print(f"    rec fails: {rfails}")
        print(f"    fuzz fails: {ffails}")

    # the two edge cases must behave
    edge = [
        ("orphan-ws-line", ["   ", "int x;"], ["int x;"],
         [["leftsimilar", 1, None], ["same", 2, 1]]),
        ("f0015-shape", ["", "x"], ["yy alpha data alpha", "x"],
         [["different", 1, 1], ["same", 2, 2]]),
    ]
    for nm, l, r, w in edge:
        case = (l, r, facts(l, "plain"), facts(r, "plain"), "plain")
        print(f"\n{nm}:")
        for name, cfg in variants.items():
            got = model(case, **cfg)
            print(f"   {name:16} {'PASS' if got == w else 'fail'} {got if got != w else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
