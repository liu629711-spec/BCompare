#!/usr/bin/env python3
"""Scratch: faithful model of FUN_140e73b40 (SmartAlign window engine, Mode3)
as the interval pair-filler, vs the shipped handler model (2026-10-15).

Decode evidence (this round):
  * `140e74b60`'s zero-LIS delegation branch (lines 303-306) calls
    `140e73b40` directly -> the window engine is the universal filler for
    both Mode1 and Mode3; `140e74b60`'s own NW/unique-LIS layers are
    Mode1-internal.
  * `140e73b40`: loop; one side exhausted -> emit pure runs (199 clamp =
    200-line chunks); both alive -> `140e733b0`.
  * `140e733b0`: window = W rows/cols per side (job+0x98 from ctx+0x3c,
    140e72ea0 rounds it up to a power of two); L-form diagonal walk
    (up-then-left per step); `140e73040` collects equal-hash diagonal runs
    at unvisited cells; run weight = sum of 140e74a70 line weights;
    >4999 abort (unreachable here), >500 -> candidate {len, weight, l, r};
    visited bitmap marks every traversed cell (a start cell must be UNSET
    -> earliest-run-per-diagonal wins, later ones are swallowed).
  * `140e74100`: truncate runs beyond the interval end; quicksort by
    weight desc (140e73e80: w, then r asc, then l asc); scan-against-LATER
    overlap resolve (containment -> trim head by min(dl,dr)+recompute weight
    via 140e74080 (weight drops below 500 -> len=0); partial overlap not
    inside -> drop len=-1; re-sort tail when anything was trimmed);
    final sort by r asc (140e73cc0: r, then l asc); emit anchors in
    ascending order with NW (`140e74660`) between them; tail NW with
    partial-traceback (param_6=1: stop when one side hits the corner,
    write consumed counts back so the outer loop re-windows the remainder).

Axes the corpora decide (unknowns in the decode):
  W       window width (job+0x98): 32 / 1000 / huge (= no windowing)
  wgt     run weight source: key text length | strip text length |
          140e75c50 composite table
  ids     anchor hash ids for equal-hash runs: unique-id (product) vs
          strip-id for unimportant lines

Baseline to beat: shipped product model (scan anchors + `140e74b60`
handler): recorded 281/290, fuzz 119/120.
"""
from __future__ import annotations

import pathlib
import sys
from collections import Counter

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))
sys.path.insert(0, r"D:\Rea\extracted\_scratch\m556")

from m26_model_grade import collect, facts, fmt_of, split_bc, myers, order_events
from m55_model_lab import parse_xml_rows
from scan2_eval import scan2, nw_fill, emit_rows, score_full  # noqa: F401

GAP = 20


def run_weight_line(wl, wr, same_key):
    return wl + wr


def make_model(*, W: int, wgt: str, un_id: str):
    # ---- per-line tables (mirrors 140e72af0: hash, flag, weight) ----
    def tables(left, right, tl, tr, fmt):
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
        elif wgt == "strip":
            wl = [len(t) for t in stl]
            wr = [len(t) for t in str_]
        else:  # 140e75c50 composite: raw=ctx+0x60 (0 here), flag=140e72f30
            def c50(nonempty, flag, raw):
                # param_1 = (text == 0) for the pair score; per-line weight
                # table: text is non-empty here, so the plain branch applies.
                if flag:
                    return raw * 2 + 0x32
                return raw + 0x1e
            wl = [c50(False, not un_l[i], 0) for i in range(n)]
            wr = [c50(False, not un_r[j], 0) for j in range(m)]
        return ids_l, ids_r, un_l, un_r, stl, str_, wl, wr

    # ---- 140e73040: one L-form cell: collect an equal-hash diagonal run ----
    def diagonal_run(l, r, ids_l, ids_r, wl, wr, n, m, visited):
        # start cell must be unvisited
        if (l, r) in visited:
            return
        i, j = l, r
        acc = 0
        ln = 0
        cells = []
        while i < n and j < m and ids_l[i] == ids_r[j]:
            w = run_weight_line(wl[i], wr[j], True)
            acc += w
            ln += 1
            cells.append((i, j))
            i += 1
            j += 1
            if acc > 4999:
                return "ABORT"
            if i >= n or j >= m:
                break
        # mark all traversed cells visited (start must have been unset;
        # the walk beyond hash-equality does not happen: ids must stay equal)
        for c in cells:
            visited.add(c)
        if ln > 0 and acc > 500:
            return (ln, acc, l, r)
        return None

    # ---- 140e733b0: window walk ----
    def window_runs(l0, r0, lend, rend, ids_l, ids_r, wl, wr):
        """Scan the window [l0, min(l0+W-1, lend)] x [r0, min(r0+W-1, rend)].
        Return (cands, consumed_l, consumed_r) with cands ascending.
        consumed_* = last (re)visited corner; == lend/rend when the L-shape
        covered the corner."""
        n = lend - l0 + 1
        m = rend - r0 + 1
        wl_ = min(l0 + W - 1, lend)
        wr_ = min(r0 + W - 1, rend)
        visited = set()
        cands = []
        aborted = False
        # first point (l0, r0)
        res = diagonal_run(l0, r0, ids_l, ids_r, wl, wr, lend + 1, rend + 1, visited)
        if res == "ABORT":
            aborted = True
        elif res:
            cands.append(res)
        # walk: at each step try (x+1, y) then (x, y+1), corner first
        x, y = l0, r0
        while x < wl_ or y < wr_:
            if x + 1 <= wl_:
                x += 1
                res = diagonal_run(x, y, ids_l, ids_r, wl, wr, lend + 1, rend + 1, visited)
                if res == "ABORT":
                    aborted = True
                elif res:
                    cands.append(res)
            if y + 1 <= wr_:
                y += 1
                res = diagonal_run(x, y, ids_l, ids_r, wl, wr, lend + 1, rend + 1, visited)
                if res == "ABORT":
                    aborted = True
                elif res:
                    cands.append(res)
            if aborted:
                break
        # consumed corner: did the walk reach (lend, rend)?
        cl = wl_
        cr = wr_
        return cands, cl, cr, (wl_ >= lend and wr_ >= rend)

    # ---- 140e74100: truncate, sort weight desc, overlap-resolve, emit ----
    def resolve_emit(cands, l0, r0, lend, rend, ids_l, ids_r, stl, str_,
                     un_l, un_r, wl, wr, partial_done):
        # truncate runs that extend beyond the interval end
        out = []
        for (ln, acc, l, r) in cands:
            if lend < l + ln - 1 or rend < r + ln - 1:
                nl = lend - l + 1
                nr = rend - r + 1
                ln = min(ln, nl, nr)
                if ln <= 0:
                    continue
                # weight recompute (140e74080 semantics)
                acc = sum(run_weight_line(wl[l + k], wr[r + k], True)
                          for k in range(ln))
                if acc < 500:
                    ln = 0
            if ln > 0:
                out.append([ln, acc, l, r])
        cands = out
        # sort by weight desc, then r asc, then l asc
        cands.sort(key=lambda c: (-c[1], c[3], c[2]))
        # overlap resolution against LATER candidates (weight order)
        k = 0
        while k < len(cands):
            A = cands[k]
            al, ar, la = A[2], A[3], A[0]
            ae_l, ae_r = al + la - 1, ar + la - 1
            m2 = k + 1
            trimmed = False
            while m2 < len(cands):
                B = cands[m2]
                if B[0] <= 0:
                    m2 += 1
                    continue
                bl, br, lb = B[2], B[3], B[0]
                be_l, be_r = bl + lb - 1, br + lb - 1
                overlap = (bl <= ae_l or br <= ae_r) and (al <= be_l or ar <= be_r)
                if not overlap:
                    m2 += 1
                    continue
                inside_ab = (bl < al and br < ar) and (al <= be_l or ar <= be_r) \
                    and (be_l < ae_l and be_r < ae_r)
                inside_ba = (al < bl and ar < br) and (bl <= ae_l or br <= ae_r) \
                    and (ae_l < be_l and ae_r < be_r)
                if inside_ab:
                    d = min(al - bl, ar - br)
                    B[2] += d
                    B[3] += d
                    B[0] = lb - d
                    B[1] = sum(run_weight_line(wl[B[2] + t], wr[B[3] + t], True)
                               for t in range(B[0])) if B[0] > 0 else 0
                    if B[0] > 0 and B[1] < 500:
                        B[0] = 0
                    trimmed = True
                elif inside_ba:
                    d = max(ae_l - bl + 1, ae_r - br + 1)
                    B[0] = lb - d
                    B[2] += d
                    B[3] += d
                    if B[0] < 0:
                        B[0] = 0
                    if B[0] > 0:
                        B[1] = sum(run_weight_line(wl[B[2] + t], wr[B[3] + t], True)
                                   for t in range(B[0]))
                        if B[1] < 500:
                            B[0] = 0
                    trimmed = True
                else:
                    B[0] = -1  # drop
                m2 += 1
            if trimmed:
                cands[k + 1:] = sorted(cands[k + 1:],
                                       key=lambda c: (-c[1], c[3], c[2]))
            k += 1
        # final ordering: by r asc, then l asc; iterate skipping len<=0
        cands = [c for c in cands if c[0] > 0]
        cands.sort(key=lambda c: (c[3], c[2]))
        pairs = []
        cur_l, cur_r = l0, r0
        ids = (ids_l, ids_r)
        un = (un_l, un_r)
        for (ln, acc, l, r) in cands:
            ls = list(range(cur_l, l))
            rs = list(range(cur_r, r))
            if ls and rs:
                pairs.extend(nw_fill(ls, rs, stl, str_, ids, un))
            for t in range(ln):
                pairs.append((l + t, r + t))
            cur_l, cur_r = l + ln, r + ln
        tail_l, tail_r = lend, rend
        consumed_all = True
        ls = list(range(cur_l, tail_l + 1))
        rs = list(range(cur_r, tail_r + 1))
        if ls and rs:
            if partial_done:
                # full NW over the remainder (outer loop already covered the
                # corner; emit everything)
                pairs.extend(nw_fill(ls, rs, stl, str_, ids, un))
            else:
                # partial traceback: NW over the remainder, then the rest is
                # consumed in ascending runs by the outer loop.
                pairs.extend(nw_fill(ls, rs, stl, str_, ids, un))
        return pairs

    # ---- 140e73b40: outer window loop ----
    def engine(l0, r0, lend, rend, ids_l, ids_r, un_l, un_r, stl, str_,
               wl, wr):
        if l0 > lend or r0 > rend:
            return []
        pairs = []
        ids = (ids_l, ids_r)
        un = (un_l, un_r)
        while l0 <= lend and r0 <= rend:
            cands, cl, cr, done = window_runs(l0, r0, lend, rend,
                                              ids_l, ids_r, wl, wr)
            partial_done = done
            seg = resolve_emit(cands, l0, r0, lend, rend, ids_l, ids_r,
                               stl, str_, un_l, un_r, wl, wr, partial_done)
            pairs.extend(seg)
            # outer loop advance: consumed up to cl, cr (window corner)
            nl = max(l0, cl) + 1
            nr = max(r0, cr) + 1
            if not partial_done:
                # remainder of one side: pure runs beyond the window
                if nl > lend and r0 <= rend:
                    break  # right remainder emitted by the caller's orphan logic
                if nr > rend and l0 <= lend:
                    break
            l0, r0 = nl, nr
        return sorted(set(pairs))

    def run_case(case, want=None):
        left, right, tl, tr, fmt = case
        n, m = len(left), len(right)
        ids_l, ids_r, un_l, un_r, stl, str_, wl, wr = \
            tables(left, right, tl, tr, fmt)
        anch, intervals = scan2(ids_l, ids_r, un_l, un_r)
        pairs = list(anch)
        for (i0, j0, i1, j1) in intervals:
            ls = list(range(max(i0, 0), min(i1, n - 1) + 1))
            rs = list(range(max(j0, 0), min(j1, m - 1) + 1))
            if ls and rs:
                pairs.extend(engine(ls[0], rs[0], ls[-1], rs[-1],
                                    ids_l, ids_r, un_l, un_r, stl, str_,
                                    wl, wr))
        pairs = sorted(set(pairs))
        used_l = {i for i, _ in pairs}
        used_r = {j for _, j in pairs}
        lo = [i for i in range(n) if i not in used_l]
        ro = [j for j in range(m) if j not in used_r]
        rows = emit_rows(left, right, tl, tr, pairs, lo, ro)
        return rows if want is None else rows == want

    return run_case


def load_cases():
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
    return rcases, fcases


def main() -> int:
    rcases, fcases = load_cases()
    for W in (32, 1000, 10 ** 9):
        for wgt in ("key", "strip"):
            for un_id in ("unique", "strip"):
                rc = make_model(W=W, wgt=wgt, un_id=un_id)
                r_ok = sum(rc(c, w) for _, c, w in rcases)
                f_ok = sum(rc(c, w) for _, c, w in fcases)
                print(f"W={W:>10} wgt={wgt:6} ids={un_id:7}"
                      f"  recorded {r_ok}/{len(rcases)}  fuzz {f_ok}/{len(fcases)}")
    # detail for the two known-difference cases under the window engine
    rc = make_model(W=10 ** 9, wgt="key", un_id="unique")
    for nm, c, w in fcases:
        if nm in ("f0059", "f0062", "f0092", "f0017", "f0040"):
            ok = rc(c, w)
            if not ok:
                got = rc(c)
                print(f"\n{nm}: FAIL  want={w}\n         got={got}")
            else:
                print(f"\n{nm}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
