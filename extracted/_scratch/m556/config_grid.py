#!/usr/bin/env python3
"""Scratch: grid-search the FULL FUN_140e726b0 scorer model (2026-10-15).

The probe's freq_score only models the "hash differs, texts non-empty,
+0x58 clear" branch. The decoded function has three branches:

  * hash ids EQUAL  -> -10 when either fetched text is empty, else
    (wL + wR) * 2 (with -1 when the two text lengths differ);
  * hash differs, one text empty -> v = -4*(lL + lR) - 1, raised to -11
    when v > -12, floored at -40;
  * hash differs, both non-empty -> raw = 3*common - lL - lR; raw < 1 ->
    max(raw*4 - 1, -40); else (raw * 25) // min(lL, lR).

Unknowns exercised as grid axes:
  text   scored/fetched text: close (product mapping: plain verbatim,
         syntax important-stripped) | important (all formats) | strip
         (whitespace-stripped verbatim, comments included)
  weight the hash-equal branch's w: key text length | verbatim length
  eq     hash-equal branch on/off

Anchor layer fixed to myers (product) + faithful NW geometry (decoded
140e74660); emitter = m26_model_grade convention. Compares against the
base model (myers + LCS triple DP) on 290 recorded + 120 fuzz.
"""
from __future__ import annotations

import pathlib
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))

from m26_model_grade import (collect, facts, close_texts, fmt_of, split_bc,
                             myers, order_events, pair_gap)
from m55_model_lab import parse_xml_rows

GAP = 20


def intersect(a, b):
    from collections import Counter
    fa = Counter(a)
    n = 0
    for ch, nb in Counter(b).items():
        n += min(fa.get(ch, 0), nb)
    return n


def make_scorer(text_mode, weight_mode, eq_on):
    def texts_of(line, fmt):
        if text_mode == "close":
            return line if fmt == "plain" else facts([line], fmt)[0]
        if text_mode == "important":
            return facts([line], fmt)[0]
        return line.strip()

    def score(tl, tr, kl, kr, wl, wr):
        if eq_on and kl == kr and kl:
            if not tl or not tr:
                return -10
            s = (wl + wr) * 2
            if len(tl) != len(tr):
                s -= 1
            return s
        if not tl or not tr:
            v = -4 * (len(tl) + len(tr)) - 1
            if v > -12:
                v = -11
            if v < -39:
                v = -40
            return v
        common = intersect(tl, tr)
        raw = common * 3 - len(tl) - len(tr)
        if raw < 1:
            return max(raw * 4 - 1, -40)
        return (raw * 25) // min(len(tl), len(tr))

    def nw_fill(ls, rs, left, right, ctl, ctr, fmt, keys, weights):
        n, m = len(ls), len(rs)
        if n == 0 or m == 0:
            return []
        sc = [[score(ctl[ls[n - c]], ctr[rs[m - r]],
                     keys[0][ls[n - c]], keys[1][rs[m - r]],
                     weights[0][ls[n - c]], weights[1][rs[m - r]])
               for c in range(1, n + 1)] for r in range(1, m + 1)]
        f = [[0] * (n + 1) for _ in range(m + 1)]
        d = [[0] * (n + 1) for _ in range(m + 1)]
        for c in range(1, n + 1):
            f[0][c] = f[0][c - 1] - GAP
            d[0][c] = 1
        for r in range(1, m + 1):
            f[r][0] = f[r - 1][0] - GAP
            d[r][0] = 2
            for c in range(1, n + 1):
                best, b = f[r - 1][c - 1] + sc[r - 1][c - 1], 3
                if best < f[r][c - 1] - GAP:
                    best, b = f[r][c - 1] - GAP, 1
                if best < f[r - 1][c] - GAP:
                    best, b = f[r - 1][c] - GAP, 2
                f[r][c], d[r][c] = best, b
        pairs = []
        r, c = m, n
        while r != 0 or c != 0:
            b = d[r][c]
            if b == 3:
                pairs.append((ls[n - c], rs[m - r]))
                r -= 1
                c -= 1
            elif b == 2:
                r -= 1
            else:
                c -= 1
        return pairs

    return texts_of, nw_fill


def emit_rows(left, right, tl, tr, pairs, lo, ro):
    rows = []
    for kind, i, j in order_events(sorted(set(pairs)), lo, ro):
        if kind == "pair":
            if left[i] == right[j]:
                st = "same"
            elif tl[i] == tr[j]:
                st = "similar"
            else:
                st = "different"
            rows.append([st, i + 1, j + 1])
        elif kind == "left":
            rows.append(["leftsimilar" if not tl[i] else "leftorphan", i + 1, None])
        else:
            rows.append(["rightsimilar" if not tr[j] else "rightorphan", None, j + 1])
    return rows


def run_case(case, scorer, want):
    left, right, tl, tr, ctl, ctr, fmt = case
    texts_of, nw_fill = scorer
    # scoring texts per config (may differ from close_texts)
    stl = [texts_of(t, fmt) for t in left]
    str_ = [texts_of(t, fmt) for t in right]
    ktl = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
    ktr = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
    keys = (ktl, ktr)
    weights = (tl, tr)  # key-length weights (axis value chosen by caller)
    anchors = myers(ktl, ktr)
    pairs = list(anchors)
    bounds = [(-1, -1)] + list(anchors) + [(len(left), len(right))]
    for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
        ls = list(range(pl + 1, nl))
        rs = list(range(pr + 1, nr))
        if ls and rs:
            pairs.extend(nw_fill(ls, rs, left, right, stl, str_, fmt,
                                 keys, weights))
    pairs = sorted(set(pairs))
    used_l = {i for i, _ in pairs}
    used_r = {j for _, j in pairs}
    lo = [i for i in range(len(left)) if i not in used_l]
    ro = [j for j in range(len(right)) if j not in used_r]
    return emit_rows(left, right, tl, tr, pairs, lo, ro) == want


def main() -> int:
    rec = collect()
    rcases = []
    for c in rec:
        fmt = fmt_of(c["left_path"])
        rcases.append((pathlib.PurePath(c["src"]).name,
                       (c["left"], c["right"], facts(c["left"], fmt),
                        facts(c["right"], fmt), close_texts(c["left"], fmt),
                        close_texts(c["right"], fmt), fmt),
                       [[s, i, j] for s, i, j in c["bc_rows"]]))

    fz_dir = REA / "product/verify/runs/m54-fuzz-20261014T170917Z/fixtures"
    fcases = []
    for lp in sorted(fz_dir.glob("*-L.*")):
        rp = pathlib.Path(str(lp).replace("-L.", "-R."))
        tag = lp.stem.split("-")[0]
        o_body = (fz_dir.parent / "reports" / f"{tag}.oracle.xml") \
            .read_bytes().decode("utf-8-sig", errors="replace")
        left = split_bc(lp.read_bytes())
        right = split_bc(rp.read_bytes())
        fmt = fmt_of(str(lp))
        fcases.append((tag,
                       (left, right, facts(left, fmt), facts(right, fmt),
                        close_texts(left, fmt), close_texts(right, fmt), fmt),
                       parse_xml_rows(o_body)))

    # base for reference
    def base_ok(case, want):
        left, right, tl, tr, ctl, ctr, _fmt = case
        ktl = [t if t else f"\x01L{i}" for i, t in enumerate(tl)]
        ktr = [t if t else f"\x01R{j}" for j, t in enumerate(tr)]
        anchors = myers(ktl, ktr)
        pairs = list(anchors)
        bounds = [(-1, -1)] + list(anchors) + [(len(left), len(right))]
        for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
            ls = list(range(pl + 1, nl))
            rs = list(range(pr + 1, nr))
            if ls and rs:
                pairs.extend(pair_gap(ls, rs, ctl, ctr))
        pairs = sorted(set(pairs))
        used_l = {i for i, _ in pairs}
        used_r = {j for _, j in pairs}
        lo = [i for i in range(len(left)) if i not in used_l]
        ro = [j for j in range(len(right)) if j not in used_r]
        return emit_rows(left, right, tl, tr, pairs, lo, ro) == want

    base_r = sum(base_ok(c, w) for _, c, w in rcases)
    base_f = sum(base_ok(c, w) for _, c, w in fcases)
    print(f"BASE  recorded {base_r}/{len(rcases)}  fuzz {base_f}/{len(fcases)}")

    watch = {"f0028", "f0040", "f0092", "f0057", "f0083", "f0017"}
    for text_mode in ("close", "important", "strip"):
        for weight_mode in ("key",):
            for eq_on in (True, False):
                scorer = make_scorer(text_mode, weight_mode, eq_on)
                r_ok = sum(run_case(c, scorer, w) for _, c, w in rcases)
                f_ok = sum(run_case(c, scorer, w) for _, c, w in fcases)
                flips = {}
                for nm, c, w in fcases:
                    if nm.split(".")[0] in watch:
                        flips[nm.split(".")[0]] = run_case(c, scorer, w)
                print(f"text={text_mode:9} w={weight_mode:4} eq={int(eq_on)}"
                      f"  recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}"
                      f"  watch {flips}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
