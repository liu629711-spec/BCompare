#!/usr/bin/env python3
"""Scratch: FUN_140e74b60 interval handler (unique-match + patience LIS)
as the scan's interval aligner, tested against the corpora (2026-10-15).

The scan-only + NW model (E config) reaches fuzz 117/120 but loses 9
recorded cases -- all shapes where a "unique line correspondence" tier
decides (case-swap-align, similar-preference, al-swap-blocks, ...). The
decoded `140e74b60` has exactly that tier, so model it faithfully:

  1. trim the common equal-key prefix and suffix (emit as anchors);
  2. left dict key -> left index, repeated keys poisoned to -1 with a
     duplicate counter; right pass collects unique-unique pairs;
  3. patience LIS over the pair sequence (in right order, keyed by left
     index) with the DECODED overwrite semantics (a smaller left index
     replaces the tail slot) -> anchors -> recurse into the gaps;
  4. if the LIS is empty: fall back to the NW filler (the +0xac / size
     gates select the window DP or the plain NW in BC; both end at
     `140e74660` for the sizes here).

`keep` selects the LIS tie rule so the corpus decides between overwrite
(decoded) and keep-earliest.
"""
from __future__ import annotations

import pathlib
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")

from m26_model_grade import collect, facts, fmt_of, split_bc, myers, order_events
from m55_model_lab import parse_xml_rows
from scan2_eval import scan2, nw_fill, emit_rows, score_full  # noqa: F401


def unique_pairs(ls, rs, ids_l, ids_r):
    """Unique-unique key pairs; duplicates on either side are excluded."""
    from collections import Counter
    cl = Counter(ids_l[i] for i in ls)
    cr = Counter(ids_r[j] for j in rs)
    left_pos = {}
    for i in ls:
        if cl[ids_l[i]] == 1:
            left_pos[ids_l[i]] = i
    pairs = []
    for j in rs:
        k = ids_r[j]
        if cr[k] == 1 and k in left_pos:
            pairs.append((left_pos.pop(k), j))
    return pairs


def patience_pairs(pairs, *, keep: str):
    """LIS over the unique-pair list.

    keep='overwrite-right': iterate in RIGHT order with left-index values,
    bisect_left slot replacement (my earlier reading of the decode).
    keep='overwrite-left':  iterate in LEFT order with right-index values,
    bisect_left slot replacement (the decode with side 0 = right doc).
    keep='first': greedy earliest-compatible (control).

    case-swap-align (a,B / b,A) discriminates: overwrite-right keeps a/A,
    overwrite-left and first keep B/b; the oracle records B/b.
    """
    if keep == "overwrite-left":
        seq = sorted(pairs, key=lambda p: p[0])
        keys = [r for (_l, r) in seq]
    else:
        seq = sorted(pairs, key=lambda p: p[1])
        keys = [l for (l, _r) in seq]
    tails = []          # increasing keys
    slots = []          # element (left, right) at each slot
    back = {}           # element identity -> predecessor element identity
    ident = {}          # element key -> identity of the element in that slot
    for (l, r) in seq:
        x = r if keep == "overwrite-left" else l
        ident[(l, r)] = (l, r)
        k = 0
        while k < len(tails) and tails[k] < x:
            k += 1
        if k == len(tails):
            tails.append(x)
            slots.append((l, r))
            prev = slots[k - 1][1] if k > 0 else None
            back[(l, r)] = prev if prev is not None else None
        elif keep in ("overwrite-left", "overwrite-right"):
            prev = slots[k - 1][1] if k > 0 else None
            tails[k] = x
            slots[k] = (l, r)
            back[(l, r)] = prev
        # keep == 'first': drop
    if not slots:
        return []
    # Reconstruct by the back chain of the last slot's element. Elements are
    # identified by their RIGHT index in right-order mode and by their LEFT
    # index in left-order mode; index the chain accordingly.
    if keep == "overwrite-left":
        by_right = {(l, r): r for (l, r) in slots}
        top = slots[-1]
        chain = [top]
        cur = top
        while back.get((cur[0], cur[1])) is not None:
            prev_r = back[(cur[0], cur[1])]
            nxt = next((e for e in back if e[1] == prev_r and e in slots), None)
            if nxt is None:
                break
            chain.append(nxt)
            cur = nxt
            if len(chain) > len(slots) + 2:
                break
        return list(reversed(chain))
    top = slots[-1]
    chain = [top]
    cur = top
    while back.get((cur[0], cur[1])) is not None:
        prev_r = back[(cur[0], cur[1])]
        nxt = next((e for e in back if e[1] == prev_r), None)
        if nxt is None:
            break
        chain.append(nxt)
        cur = nxt
        if len(chain) > len(slots) + 2:
            break
    return list(reversed(chain))


def handler(ls, rs, ids, un, stl, str_, *, keep: str, depth=0):
    """Model of FUN_140e74b60 over one interval [ls] x [rs]."""
    pairs = []
    if not ls or not rs or depth > 64:
        return pairs
    # 1. common prefix / suffix trim
    pre = 0
    while (pre < len(ls) and pre < len(rs)
           and ids[0][ls[pre]] == ids[1][rs[pre]]):
        pairs.append((ls[pre], rs[pre]))
        pre += 1
    ls = ls[pre:]
    rs = rs[pre:]
    if not ls or not rs:
        return pairs
    suf = 0
    while (suf < len(ls) - 1 and suf < len(rs) - 1
           and ids[0][ls[-1 - suf]] == ids[1][rs[-1 - suf]]):
        suf += 1
    tail = [(ls[len(ls) - 1 - k], rs[len(rs) - 1 - k]) for k in range(suf)]
    ls = ls[:len(ls) - suf]
    rs = rs[:len(rs) - suf]
    # 2. unique-unique pairs
    up = unique_pairs(ls, rs, ids[0], ids[1])
    if up:
        anchors = patience_pairs(up, keep=keep)
        # 3. recurse into the gaps between anchors
        pairs.extend(_recurse(ls, rs, anchors, ids, un, stl, str_,
                              keep=keep, depth=depth))
    else:
        pairs.extend(nw_fill(ls, rs, stl, str_, ids, un))
    pairs.extend(tail)
    return pairs


def _recurse(ls, rs, anchors, ids, un, stl, str_, *, keep, depth):
    out = []
    li = ri = 0
    for (al, ar) in anchors:
        sub_l = [x for x in ls[li:] if x < al]
        sub_r = [x for x in rs[ri:] if x < ar]
        if sub_l and sub_r:
            out.extend(handler(sub_l, sub_r, ids, un, stl, str_,
                               keep=keep, depth=depth + 1))
        out.append((al, ar))
        while li < len(ls) and ls[li] <= al:
            li += 1
        while ri < len(rs) and rs[ri] <= ar:
            ri += 1
    sub_l = ls[li:]
    sub_r = rs[ri:]
    if sub_l and sub_r:
        out.extend(handler(sub_l, sub_r, ids, un, stl, str_,
                           keep=keep, depth=depth + 1))
    return out


def run_case(case, *, anchors="scan", keep="overwrite", un_id="unique"):
    left, right, tl, tr, fmt = case
    n, m = len(left), len(right)
    stl = [t.strip() for t in left]
    str_ = [t.strip() for t in right]
    un_l = [not t for t in tl]
    un_r = [not t for t in tr]
    if un_id == "strip":
        ids_l = [t if t else left[i].strip() for i, t in enumerate(tl)]
        ids_r = [t if t else right[j].strip() for j, t in enumerate(tr)]
    else:
        ids_l = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
        ids_r = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
    ids = (ids_l, ids_r)
    un = (un_l, un_r)
    if anchors == "myers":
        ktl = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
        ktr = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
        pairs = list(myers(ktl, ktr))
        bounds = [(-1, -1)] + list(pairs) + [(n, m)]
        for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
            ls = list(range(pl + 1, nl))
            rs = list(range(pr + 1, nr))
            if ls and rs:
                pairs.extend(handler(ls, rs, ids, un, stl, str_, keep=keep))
    else:
        anch, intervals = scan2(ids_l, ids_r, un_l, un_r)
        pairs = list(anch)
        for (l0, r0, l1, r1) in intervals:
            ls = list(range(max(l0, 0), min(l1, n - 1) + 1))
            rs = list(range(max(r0, 0), min(r1, m - 1) + 1))
            if ls and rs:
                pairs.extend(handler(ls, rs, ids, un, stl, str_, keep=keep))
    pairs = sorted(set(pairs))
    used_l = {i for i, _ in pairs}
    used_r = {j for _, j in pairs}
    lo = [i for i in range(n) if i not in used_l]
    ro = [j for j in range(m) if j not in used_r]
    return emit_rows(left, right, tl, tr, pairs, lo, ro)


def main() -> int:
    rec = collect()
    rcases = []
    for c in rec:
        fmt = fmt_of(c["left_path"])
        rcases.append((pathlib.PurePath(c["src"]).name,
                       (c["left"], c["right"], facts(c["left"], fmt),
                        facts(c["right"], fmt), fmt),
                       [[s, i, j] for s, i, j in c["bc_rows"]]))
    fz_dir = REA / "product/verify/runs/m54-fuzz-20261014T170917Z/fixtures"
    fcases = []
    for lp in sorted(fz_dir.glob("*-L.*")):
        rp = pathlib.Path(str(lp).replace("-L.", "-R."))
        tag = lp.stem.split("-")[0]
        o = (fz_dir.parent / "reports" / f"{tag}.oracle.xml").read_bytes() \
            .decode("utf-8-sig", errors="replace")
        left, right = split_bc(lp.read_bytes()), split_bc(rp.read_bytes())
        fmt = fmt_of(str(lp))
        fcases.append((tag, (left, right, facts(left, fmt), facts(right, fmt), fmt),
                       parse_xml_rows(o)))

    configs = [
        ("A myers+NW (current)", dict(anchors="myers", keep="none", un_id="unique")),
        ("H3  scan+LIS(overwrite-right)+NW", dict(anchors="scan", keep="overwrite-right")),
        ("H3L scan+LIS(overwrite-left)+NW", dict(anchors="scan", keep="overwrite-left")),
        ("H3b scan+LIS(first)+NW", dict(anchors="scan", keep="first")),
    ]
    for name, cfg in configs:
        try:
            r_ok = sum(run_case(c, **cfg) == w for _, c, w in rcases)
            f_ok = sum(run_case(c, **cfg) == w for _, c, w in fcases)
            print(f"{name:34} recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}")
        except Exception as e:  # noqa: BLE001
            print(f"{name:34} ERROR {e}")
    for nm, c, w in fcases:
        if nm in ("f0017", "f0040", "f0041", "f0092"):
            print(f"\n{nm}:")
            for name, cfg in configs:
                try:
                    print(f"   {name:32} {'PASS' if run_case(c, **cfg) == w else 'fail'}")
                except Exception as e:  # noqa: BLE001
                    print(f"   {name:32} ERROR {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
