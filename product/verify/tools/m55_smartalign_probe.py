#!/usr/bin/env python3
"""M5.5-6 single-variable probe (OFFLINE): the anchoring layer only.

§13/§13.3 decoded BC's real anchor tier for `.txt` (Mode3 TBcSmartAlign):

  * `140e738a0` (shared by Mode1/Mode3) is a forward greedy scan with a
    pending-interval discipline:
      - both sides important (FUN_140e72f30 == 0) and hash ids equal
        (FUN_140e72e80) -> with NO pending, emit a 1:1 anchor pair; with a
        pending interval open, only remember the interval start (no anchor);
      - both sides unimportant -> if hosts differ, break; if equal, flush
        any pending interval to the mode's vtable[1] and emit the pair;
      - importance differs -> advance ONLY the unimportant side, recording
        the pending start on the other side;
      - mismatch with no pending -> set pending (start of the interval).
    After the loop, the remaining region (or the pending one) goes to
    vtable[1].
  * Mode3 vtable[1] = `140e73b40` -> `140e733b0` window DP: per side the
    window is min(remaining, job+0x98) (ctx cache size, runtime value not
    located); `140e73040` walks equal-hash diagonals (`140e74a70` per-line
    weights), recording a run as an anchor only when its weight > 500
    (>= 5000 raises); `140e74100` emits kept anchors and fills every gap
    with the NW-DP `140e74660` (gap cost -20/line, pair score
    `140e726b0` char-frequency intersection).

This probe changes EXACTLY ONE structural variable at a time against the
shipped model, so the delta isolates each change (the whole point of
M5.5-6). Two independent axes are modelled:

    anchors            filler (per interval, incl. the residual gaps)
    inc     myers over ci-folded important keys     LCS (score,count,min-len)
    incNW   myers over ci-folded important keys     NW-DP freq_score, gap -20
    incNWf  myers over ci-folded important keys     nw_gap_faithful
    sa0     decoded greedy scan (as above)          LCS (score,count,min-len)
    saN     decoded greedy scan (as above)          NW-DP freq_score, gap -20
    saNf    decoded greedy scan (as above)          nw_gap_faithful

`nw_gap_faithful` is the literal `FUN_140e74660` port: the DP fills in
REVERSED coordinates with tie order diag > skip-left > skip-right, then
traces back from the (n, m) corner -- the tie preference is anchored at
the END of the interval. This is measurable and dominant: it alone takes
fuzz 84/120 -> 91/120 (incNWf), and layered on the decoded anchors gives
94/120 (saNf); the forward port (`freqscore_pair_gap`) measurably HURTS.

Measured results (runs/m55-smartalign-probe-20261015T095342Z):
    inc     recorded 244/290  fuzz 84/120
    incNWf  recorded 245/290  fuzz 91/120
    saNf    recorded 241/290  fuzz 94/120
    sa0     recorded 229/290  fuzz 87/120
    incNW   recorded 227/290  fuzz 82/120
    saN     recorded 214/290  fuzz 83/120
The window-DP diagonal-run stage was modelled and measured inert on this
corpus scale (0 of 1269 runs reached weight 500) -- a measured claim, not
an assumption (RUN_STATS in the JSON).

OFFLINE only: recorded XML + fuzz fixtures on disk. No Oracle, no product
code change.
    cd D:\\Rea\\product\\verify && python tools/m55_smartalign_probe.py
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))

from m26_model_grade import (  # noqa: E402
    collect, facts, fmt_of, myers, order_events, split_bc,
)
from m55_model_lab import (  # noqa: E402
    freq_score, freqscore_pair_gap, incumbent_rows, lcs_pair_gap,
    parse_xml_rows,
)

WINDOW_RUN_MIN = 500      # `140e73040`: runs recorded only when weight > 500
WINDOW_RUN_MAX = 4999     # `140e73040`: runs >= 5000 raise inside BC
GAP_PENALTY = 20          # `140e74660`: -0x14 per skipped line

RUN_STATS = {"runs_total": 0, "runs_kept": 0, "runs_over_max": 0,
             "scan_anchors": 0, "myers_anchors": 0}


def nw_gap_faithful(ls, rs, left, right, texts_l, texts_r, *,
                    score_fn=None, gap=GAP_PENALTY):
    """`FUN_140e74660` AS DECODED: the DP fills in reversed coordinates
    (score at column local_4c uses left line hi - local_4c + 1) with the
    tie order diag > skip-left > skip-right, then traces back from the
    (n, m) corner. This differs from a naive forward port in WHICH
    diagonal wins a tie: the reversed fill anchors the preference at the
    END of the sequences (case-swap-align pins this: BC pairs B/b, the
    forward port pairs a/A).

    `score_fn` defaults to the decoded `freq_score`; pass `lcs_len` to
    isolate the DP geometry with the incumbent's score held fixed."""
    if score_fn is None:
        score_fn = freq_score
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    sc = [[score_fn(texts_l[ls[n - c]], texts_r[rs[m - r]])
           for c in range(1, n + 1)] for r in range(1, m + 1)]
    f = [[0] * (n + 1) for _ in range(m + 1)]
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for c in range(1, n + 1):
        f[0][c] = f[0][c - 1] - gap
        d[0][c] = 1
    for r in range(1, m + 1):
        f[r][0] = f[r - 1][0] - gap
        d[r][0] = 2
        for c in range(1, n + 1):
            best, b = f[r - 1][c - 1] + sc[r - 1][c - 1], 3
            if best < f[r][c - 1] - gap:
                best, b = f[r][c - 1] - gap, 1
            if best < f[r - 1][c] - gap:
                best, b = f[r - 1][c] - gap, 2
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


def nw_gap_forward(ls, rs, left, right, texts_l, texts_r, *,
                   score_fn=None, gap=GAP_PENALTY):
    """Forward-coordinate NW (gap -20, diag-first ties, traced from (n,m)).

    The control for the geometry axis: identical objective to the faithful
    port, only the fill coordinate system and tie preference differ."""
    if score_fn is None:
        score_fn = freq_score
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    sc = [[score_fn(texts_l[ls[i]], texts_r[rs[j]]) for j in range(m)]
          for i in range(n)]
    f = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        f[i][0] = -gap * i
    for j in range(m + 1):
        f[0][j] = -gap * j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            f[i][j] = max(f[i - 1][j - 1] + sc[i - 1][j - 1],
                          f[i - 1][j] - gap,
                          f[i][j - 1] - gap)
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        if f[i][j] == f[i - 1][j - 1] + sc[i - 1][j - 1]:
            pairs.append((ls[i - 1], rs[j - 1]))
            i -= 1
            j -= 1
        elif f[i][j] == f[i - 1][j] - gap:
            i -= 1
        else:
            j -= 1
    return pairs


# ----------------------------------------------------------------------
# Greedy scan: faithful model of `140e738a0` (+ `140e72f30`/`140e72e80`)
# ----------------------------------------------------------------------

def smart_scan(keys_l: list[str], keys_r: list[str]):
    """Return (anchor_pairs, intervals); intervals are inclusive ranges
    (l0, r0, l1, r1) handed to the mode's vtable[1] aligner.

    "important" is modelled as a non-empty important key (the importance
    verdict produced text); empty keys (blank lines / comment-only lines
    in syntax formats) are the unimportant side. Hash ids are modelled by
    exact key equality; the real ids are collision-prone 32-bit values,
    which the corpora cannot distinguish.
    """
    n, m = len(keys_l), len(keys_r)
    anchors: list[tuple[int, int]] = []
    intervals: list[tuple[int, int, int, int]] = []
    i = j = 0
    p5 = p6 = -1                       # pending interval start (left/right)
    while i < n and j < m:
        l_un = not keys_l[i]
        r_un = not keys_r[j]
        if not l_un and not r_un:
            if p5 < 0 and p6 < 0:
                if keys_l[i] == keys_r[j]:
                    anchors.append((i, j))
                else:
                    p5, p6 = i, j
            else:
                if p5 < 0:
                    p5 = i
                if p6 < 0:
                    p6 = j
            i += 1
            j += 1
        elif l_un and r_un:
            if keys_l[i] != keys_r[j]:
                break
            if p5 >= 0 or p6 >= 0:
                if p5 < 0:
                    p5 = i
                if p6 < 0:
                    p6 = j
                intervals.append((p5, p6, i - 1, j - 1))
                p5 = p6 = -1
            anchors.append((i, j))
            i += 1
            j += 1
        elif not l_un and r_un:        # left important, right unimportant
            if p5 < 0:
                p5 = i
            i += 1
        else:                          # left unimportant, right important
            if p6 < 0:
                p6 = j
            j += 1
    if p5 >= 0:
        i = p5
    if p6 >= 0:
        j = p6
    intervals.append((i, j, n - 1, m - 1))
    return anchors, intervals


# ----------------------------------------------------------------------
# Window DP stage model (`140e73040`/`140e74100` diagonal runs)
# ----------------------------------------------------------------------

def window_keep_runs(ls, rs, keys_l, keys_r, weights_l):
    """Diagonal equal-key runs inside one interval, kept only when the
    accumulated LEFT weight exceeds WINDOW_RUN_MIN (the decoded >500
    threshold); weight >= 5000 is BC's raise path and is counted as
    unrecorded. These runs become anchors; the gaps between them get the
    NW-DP filler. At corpus scale nothing should qualify -- RUN_STATS
    records that fact instead of assuming it."""
    kept: list[tuple[int, int, int]] = []
    ridx = {v: k for k, v in enumerate(rs)}
    for i, li in enumerate(ls):
        if not keys_l[li]:
            continue
        for rj in rs:
            if keys_l[li] != keys_r[rj]:
                continue
            RUN_STATS["runs_total"] += 1
            ln = 0
            weight = 0
            while (i + ln < len(ls) and ridx.get(rj) is not None
                   and ridx[rj] + ln < len(rs)):
                ii = ls[i + ln]
                jj = rs[ridx[rj] + ln]
                if not keys_l[ii] or keys_l[ii] != keys_r[jj]:
                    break
                weight += weights_l[ii]
                ln += 1
            if weight > WINDOW_RUN_MAX:
                RUN_STATS["runs_over_max"] += 1
            elif weight > WINDOW_RUN_MIN:
                RUN_STATS["runs_kept"] += 1
                kept.append((li, rj, ln))
            break                      # one start per left line
    return kept


# ----------------------------------------------------------------------
# Row assembly: identical downstream of the pair list
# ----------------------------------------------------------------------

def rows_from_pairs(left, right, texts_l, texts_r, pairs):
    pairs = sorted(set(pairs))
    used_l = {i for i, _ in pairs}
    used_r = {j for _, j in pairs}
    lo = [i for i in range(len(left)) if i not in used_l]
    ro = [j for j in range(len(right)) if j not in used_r]
    rows = []
    for kind, i, j in order_events(pairs, lo, ro):
        if kind == "pair":
            if left[i] == right[j]:
                st = "same"
            elif texts_l[i] and texts_l[i] == texts_r[j]:
                st = "similar"
            else:
                st = "different"
            rows.append([st, i + 1, j + 1])
        elif kind == "left":
            st = "leftsimilar" if not texts_l[i] else "leftorphan"
            rows.append([st, i + 1, None])
        else:
            st = "rightsimilar" if not texts_r[j] else "rightorphan"
            rows.append([st, None, j + 1])
    return rows


def myers_fill(left, right, texts_l, texts_r, filler):
    """Incumbent anchor layer (myers over ci keys), variable filler."""
    lk = [t if t else f"\x01L{i}" for i, t in enumerate(texts_l)]
    rk = [t if t else f"\x01R{j}" for j, t in enumerate(texts_r)]
    anchors = myers(lk, rk)
    pairs = list(anchors)
    bounds = [(-1, -1)] + list(anchors) + [(len(left), len(right))]
    for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
        ls = list(range(pl + 1, nl))
        rs = list(range(pr + 1, nr))
        if ls and rs:
            pairs.extend(filler(ls, rs, left, right, texts_l, texts_r))
    return pairs


def scan_fill(left, right, texts_l, texts_r, filler):
    """Decoded greedy scan anchors + variable filler on its intervals
    (with the window-DP run stage in front of the NW filler)."""
    anchors, intervals = smart_scan(texts_l, texts_r)
    pairs = list(anchors)
    weights_l = [len(t) for t in texts_l]
    for (l0, r0, l1, r1) in intervals:
        ls = list(range(max(l0, 0), min(l1, len(left) - 1) + 1))
        rs = list(range(max(r0, 0), min(r1, len(right) - 1) + 1))
        if not ls or not rs:
            continue
        kept = window_keep_runs(ls, rs, texts_l, texts_r, weights_l)
        for li, rj, ln in kept:
            for k in range(ln):
                pairs.append((li + k, rj + k))
        anchors_set = {(li + k, rj + k) for li, rj, ln in kept
                       for k in range(ln)}
        # NW/LCS filler over the interval minus the kept runs
        free_l = [x for x in ls if not any((x, y) in anchors_set for y in rs)]
        free_r = [x for x in rs if not any((y, x) in anchors_set for y in ls)]
        if free_l and free_r:
            pairs.extend(filler(free_l, free_r, left, right, texts_l, texts_r))
    return pairs


def main() -> int:
    recorded = collect()
    rec_cases = []
    for c in recorded:
        fmt = fmt_of(c["left_path"])
        rec_cases.append({
            "src": c["src"], "left": c["left"], "right": c["right"],
            "texts_l": facts(c["left"], fmt), "texts_r": facts(c["right"], fmt),
            "want": [[s, i, j] for s, i, j in c["bc_rows"]],
        })

    fz_dir = REA / "product/verify/runs/m54-fuzz-20261014T170917Z/fixtures"
    fz_cases = []
    for lp in sorted(fz_dir.glob("*-L.*")):
        rp = pathlib.Path(str(lp).replace("-L.", "-R."))
        tag = lp.stem.split("-")[0]
        o_body = (fz_dir.parent / "reports" / f"{tag}.oracle.xml").read_bytes() \
            .decode("utf-8-sig", errors="replace")
        left = split_bc(lp.read_bytes())
        right = split_bc(rp.read_bytes())
        fmt = fmt_of(str(lp))
        fz_cases.append({
            "src": tag, "left": left, "right": right,
            "texts_l": facts(left, fmt), "texts_r": facts(right, fmt),
            "want": parse_xml_rows(o_body),
        })

    def lcs_fill(ls, rs, left, right, tl, tr):
        return lcs_pair_gap(ls, rs, left, right, tl, tr)

    def nw_fill(ls, rs, left, right, tl, tr):
        return freqscore_pair_gap(ls, rs, left, right, tl, tr)

    def nw_fill_faithful(ls, rs, left, right, tl, tr):
        return nw_gap_faithful(ls, rs, left, right, tl, tr)

    def nw_faithful_lcs(ls, rs, left, right, tl, tr):
        from m26_model_grade import lcs_len
        return nw_gap_faithful(ls, rs, left, right, tl, tr, score_fn=lcs_len)

    def nw_forward_lcs(ls, rs, left, right, tl, tr):
        from m26_model_grade import lcs_len
        return nw_gap_forward(ls, rs, left, right, tl, tr, score_fn=lcs_len)

    variants = {
        "inc": lambda c: incumbent_rows(c["left"], c["right"],
                                        c["texts_l"], c["texts_r"]),
        "incNW": lambda c: rows_from_pairs(
            c["left"], c["right"], c["texts_l"], c["texts_r"],
            myers_fill(c["left"], c["right"], c["texts_l"], c["texts_r"],
                       nw_fill)),
        "incNWf": lambda c: rows_from_pairs(
            c["left"], c["right"], c["texts_l"], c["texts_r"],
            myers_fill(c["left"], c["right"], c["texts_l"], c["texts_r"],
                       nw_fill_faithful)),
        # --- geometry axis with the incumbent score held fixed (LCS) ---
        "incFWD_L": lambda c: rows_from_pairs(
            c["left"], c["right"], c["texts_l"], c["texts_r"],
            myers_fill(c["left"], c["right"], c["texts_l"], c["texts_r"],
                       nw_forward_lcs)),
        "incFAI_L": lambda c: rows_from_pairs(
            c["left"], c["right"], c["texts_l"], c["texts_r"],
            myers_fill(c["left"], c["right"], c["texts_l"], c["texts_r"],
                       nw_faithful_lcs)),
        "sa0": lambda c: rows_from_pairs(
            c["left"], c["right"], c["texts_l"], c["texts_r"],
            scan_fill(c["left"], c["right"], c["texts_l"], c["texts_r"],
                      lcs_fill)),
        "saN": lambda c: rows_from_pairs(
            c["left"], c["right"], c["texts_l"], c["texts_r"],
            scan_fill(c["left"], c["right"], c["texts_l"], c["texts_r"],
                      nw_fill)),
        "saNf": lambda c: rows_from_pairs(
            c["left"], c["right"], c["texts_l"], c["texts_r"],
            scan_fill(c["left"], c["right"], c["texts_l"], c["texts_r"],
                      nw_fill_faithful)),
    }
    results = {}
    failures = {}
    for name, fn in variants.items():
        r = {"rec": 0, "rec_ok": 0, "fz": 0, "fz_ok": 0}
        fails = []
        for c in rec_cases:
            got = fn(c)
            r["rec"] += 1
            if got == c["want"]:
                r["rec_ok"] += 1
            elif len(fails) < 12:
                fails.append(("rec", c["src"], c["want"], got))
        for c in fz_cases:
            got = fn(c)
            r["fz"] += 1
            if got == c["want"]:
                r["fz_ok"] += 1
            elif len(fails) < 12:
                fails.append(("fuzz", c["src"], c["want"], got))
        results[name] = r
        failures[name] = fails

    print(f"recorded {len(rec_cases)}  fuzz {len(fz_cases)}")
    for name in variants:
        r = results[name]
        print(f"{name:6}  recorded {r['rec_ok']}/{r['rec']}  "
              f"fuzz {r['fz_ok']}/{r['fz']}")
    print(f"window runs: {RUN_STATS}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REA / "product/verify/runs" / f"m55-smartalign-probe-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "m55-smartalign-probe.json").write_text(json.dumps(
        {"results": results, "failures": failures, "run_stats": RUN_STATS},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"raw: {out / 'm55-smartalign-probe.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
