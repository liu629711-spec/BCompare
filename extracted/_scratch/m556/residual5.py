#!/usr/bin/env python3
"""Scratch: isolate the residual-5 root cause (2026-10-15).

All five remaining fuzz failures involve a duplicated line inside a
mismatch interval, where the oracle pairs the EARLIEST partner and orphans
the later duplicate, while the shipped handler's suffix trim consumes the
later partner. Controlled variants (same scan, same scorer, same emitter):

  V0  shipped: prefix/suffix trim -> unique -> LIS -> NW
  V1  no handler stage: every interval -> NW directly (the Mode3 reading:
      `140e73b40` -> `140e733b0` window DP with no >500-weight run found ->
      `140e74100` -> `140e74660` NW over the whole interval)
  V2  V0 but the suffix trim stops when the RIGHT line's key is duplicated
      inside the interval
  V3  V0 but the suffix trim stops when EITHER line's key is duplicated
  V4  V0 without any suffix trim
"""
from __future__ import annotations

import pathlib
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, str(REA / "extracted" / "_scratch" / "m556"))

from m26_model_grade import collect, facts, fmt_of, split_bc, order_events  # noqa: E402
from m55_model_lab import parse_xml_rows  # noqa: E402
import m55_anchor_eval as E  # noqa: E402
from collections import Counter  # noqa: E402


def dup_counts(seq, ids_side):
    return Counter(ids_side[i] for i in seq)


def handler_v(ls, rs, ctx, depth=0, *, variant="V0"):
    """Parameterised interval handler."""
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
    if variant != "V4":
        rc = dup_counts(rs, ids[1])
        lc = dup_counts(ls, ids[0])
        while (suf < len(ls) - 1 and suf < len(rs) - 1
               and ids[0][ls[-1 - suf]] == ids[1][rs[-1 - suf]]):
            r_key = ids[1][rs[-1 - suf]]
            l_key = ids[0][ls[-1 - suf]]
            if variant == "V2" and rc[r_key] > 1:
                break
            if variant == "V3" and (rc[r_key] > 1 or lc[l_key] > 1):
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
        pairs.extend(_recurse_v(ls, rs, anchors, ctx, depth, variant))
    else:
        pairs.extend(E.nw_fill(ls, rs, ctx))
    pairs.extend(tail)
    return pairs


def _recurse_v(ls, rs, anchors, ctx, depth, variant):
    out = []
    li = ri = 0
    for (al, ar) in anchors:
        sub_l = [x for x in ls[li:] if x < al]
        sub_r = [x for x in rs[ri:] if x < ar]
        if sub_l and sub_r:
            out.extend(handler_v(sub_l, sub_r, ctx, depth + 1, variant=variant))
        out.append((al, ar))
        while li < len(ls) and ls[li] <= al:
            li += 1
        while ri < len(rs) and rs[ri] <= ar:
            ri += 1
    sub_l, sub_r = ls[li:], rs[ri:]
    if sub_l and sub_r:
        out.extend(handler_v(sub_l, sub_r, ctx, depth + 1, variant=variant))
    return out


def model_v(case, variant):
    n, m, ctx = E.build_ctx(case)
    ids_l, ids_r = ctx[2]
    pairs, intervals = E.greedy_scan(ids_l, ids_r, ctx[3][0], ctx[3][1])
    for (l0, r0, l1, r1) in intervals:
        ls = list(range(max(l0, 0), min(l1, n - 1) + 1))
        rs = list(range(max(r0, 0), min(r1, m - 1) + 1))
        if not ls or not rs:
            continue
        if variant == "V1":
            pairs.extend(E.nw_fill(ls, rs, ctx))
        else:
            pairs.extend(handler_v(ls, rs, ctx, variant=variant))
    return E.finish(case, pairs)


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

    for variant in ("V0", "V1", "V2", "V3", "V4"):
        r_ok = sum(model_v(c, variant) == w for _, c, w in rcases)
        f_ok = sum(model_v(c, variant) == w for _, c, w in fcases)
        fails = [nm for nm, c, w in fcases if model_v(c, variant) != w]
        print(f"{variant}: recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}"
              f"  fails={fails}")
    # detail for the five
    for nm, c, w in fcases:
        if nm in ("f0021", "f0040", "f0073", "f0092", "f0115"):
            print(f"\n{nm}: want={w}")
            for variant in ("V0", "V1", "V2", "V3", "V4"):
                got = model_v(c, variant)
                print(f"   {variant}: {'PASS' if got == w else 'fail'}")
                if got != w and variant == "V2":
                    print(f"      V2 got={got}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
