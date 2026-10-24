#!/usr/bin/env python3
"""Scratch: corrected model of FUN_140e738a0 + evaluation (2026-10-15).

The first Python model (`m55_smartalign_probe.smart_scan`) had two branch
polarities wrong versus the decompiled code:

  * asymmetric (one side important, other unimportant): the code advances the
    IMPORTANT side and pins the pending start at the important line, not the
    unimportant one;
  * with a pending interval open, even a both-important equal-id pair does NOT
    emit — it only extends the interval (the `(iVar5 < 0) && (iVar6 < 0)`
    guard). The interval is flushed only by a both-unimportant EQUAL pair (or
    by the tail call).

Also: both-unimportant with UNEQUAL ids breaks the loop (tail flush follows),
and both-unimportant EQUAL pairs emit even with no pending open.

This script re-models the scan faithfully and grades it on the recorded
(290) + fuzz (120) corpora against the shipped anchor layer, with the now
validated filler (decoded `140e726b0` score + decoded NW + strip text).
"""
from __future__ import annotations

import pathlib
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))

from m26_model_grade import collect, facts, fmt_of, split_bc, myers, order_events
from m55_model_lab import parse_xml_rows

GAP = 20


def intersect(a, b):
    from collections import Counter
    fa = Counter(a)
    n = 0
    for ch, nb in Counter(b).items():
        n += min(fa.get(ch, 0), nb)
    return n


def score_full(stl, str_, same_key, wl, wr):
    """FUN_140e726b0, all branches (decoded)."""
    if same_key:
        if not stl or not str_:
            return -10
        s = (wl + wr) * 2
        if len(stl) != len(str_):
            s -= 1
        return s
    if not stl or not str_:
        v = -4 * (len(stl) + len(str_)) - 1
        if v > -12:
            v = -11
        if v < -39:
            v = -40
        return v
    common = intersect(stl, str_)
    raw = common * 3 - len(stl) - len(str_)
    if raw < 1:
        return max(raw * 4 - 1, -40)
    return (raw * 25) // min(len(stl), len(str_))


def nw_fill(ls, rs, stl, str_, ids, un):
    """FUN_140e74660 decoded: reversed-coordinate NW, gap 20, diag-first."""
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    f = [[0] * (n + 1) for _ in range(m + 1)]
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for c in range(1, n + 1):
        f[0][c] = f[0][c - 1] - GAP
        d[0][c] = 1
    for r in range(1, m + 1):
        f[r][0] = f[r - 1][0] - GAP
        d[r][0] = 2
        for c in range(1, n + 1):
            a, b = n - c, m - r
            la, rb = ls[a], rs[b]
            same_key = (not un[0][la]) and ids[0][la] == ids[1][rb]
            best = f[r - 1][c - 1] + score_full(stl[la], str_[rb], same_key,
                                                len(ids[0][la]), len(ids[1][rb]))
            bd = 3
            if best < f[r][c - 1] - GAP:
                best, bd = f[r][c - 1] - GAP, 1
            if best < f[r - 1][c] - GAP:
                best, bd = f[r - 1][c] - GAP, 2
            f[r][c], d[r][c] = best, bd
    pairs = []
    r, c = m, n
    while r != 0 or c != 0:
        bd = d[r][c]
        if bd == 3:
            pairs.append((ls[n - c], rs[m - r]))
            r -= 1
            c -= 1
        elif bd == 2:
            r -= 1
        else:
            c -= 1
    return pairs


def scan2(ids_l, ids_r, un_l, un_r, *, mixed="advance-important"):
    """Faithful FUN_140e738a0. Returns (pairs, intervals).

    `mixed` selects the asymmetric branch reading:
      'advance-important'   left important + right unimportant -> advance LEFT
      'advance-unimportant' left important + right unimportant -> advance RIGHT
    Both are defensible readings of the LAB_140e739cc double-check; the
    corpora (f0040) decide.
    """
    n, m = len(ids_l), len(ids_r)
    i = j = 0
    pi = pj = -1
    pairs, intervals = [], []
    advance_left_on_mixed = (mixed == "advance-important")
    while i < n and j < m:
        if not un_l[i]:
            if not un_r[j]:
                # both important
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
            else:
                # left important, right unimportant
                if advance_left_on_mixed:
                    if pi < 0:
                        pi = i
                    i += 1
                else:
                    if pj < 0:
                        pj = j
                    j += 1
        else:
            if un_r[j]:
                # both unimportant
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
            else:
                # left unimportant, right important
                if advance_left_on_mixed:
                    if pj < 0:
                        pj = j
                    j += 1
                else:
                    if pi < 0:
                        pi = i
                    i += 1
    if pi >= 0:
        i = pi
    if pj >= 0:
        j = pj
    intervals.append((i, j, n - 1, m - 1))
    return pairs, intervals


def emit_rows(left, right, tl, tr, pairs, lo, ro):
    rows = []
    for kind, i, j in order_events(sorted(set(pairs)), lo, ro):
        if kind == "pair":
            st = ("same" if left[i] == right[j]
                  else "similar" if tl[i] == tr[j] else "different")
            rows.append([st, i + 1, j + 1])
        elif kind == "left":
            rows.append(["leftsimilar" if not tl[i] else "leftorphan", i + 1, None])
        else:
            rows.append(["rightsimilar" if not tr[j] else "rightorphan", None, j + 1])
    return rows


def run_case(case, *, anchors, un_id):
    left, right, tl, tr, fmt = case
    n, m = len(left), len(right)
    stl = [t.strip() for t in left]
    str_ = [t.strip() for t in right]
    un_l = [not t for t in tl]
    un_r = [not t for t in tr]
    if un_id == "strip":
        ids_l = [t if t else left[i].strip() for i, t in enumerate(tl)]
        ids_r = [t if t else right[j].strip() for j, t in enumerate(tr)]
    elif un_id == "raw":
        ids_l = [t if t else left[i] for i, t in enumerate(tl)]
        ids_r = [t if t else right[j] for j, t in enumerate(tr)]
    else:  # unique: unimportant lines never match (product's current rule)
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
                pairs.extend(nw_fill(ls, rs, stl, str_, ids, un))
    else:
        anch, intervals = scan2(ids_l, ids_r, un_l, un_r)
        pairs = list(anch)
        for (l0, r0, l1, r1) in intervals:
            ls = list(range(max(l0, 0), min(l1, n - 1) + 1))
            rs = list(range(max(r0, 0), min(r1, m - 1) + 1))
            if ls and rs:
                pairs.extend(nw_fill(ls, rs, stl, str_, ids, un))
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
        ("A myers+strip-ids (current product)", dict(anchors="myers", un_id="strip")),
        ("B myers+unique-ids", dict(anchors="myers", un_id="unique")),
        ("C scan2+strip-ids", dict(anchors="scan", un_id="strip")),
        ("D scan2+raw-ids", dict(anchors="scan", un_id="raw")),
        ("E scan2+unique-ids", dict(anchors="scan", un_id="unique")),
    ]
    for name, cfg in configs:
        r_ok = sum(run_case(c, **cfg) == w for _, c, w in rcases)
        f_ok = sum(run_case(c, **cfg) == w for _, c, w in fcases)
        print(f"{name:38} recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}")

    # detail for f0017 under scan
    for nm, c, w in fcases:
        if nm == "f0017":
            print("\nf0017 want:", w)
            for name, cfg in configs:
                print(f"  {name:36} {'PASS' if run_case(c, **cfg) == w else 'fail'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
