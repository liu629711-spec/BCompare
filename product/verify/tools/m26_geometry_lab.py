#!/usr/bin/env python3
"""M2.6 geometry lab (OFFLINE): reproduce BC's pairing by replaying its
recursion over the middle snake, with 1x1 cells emitted as pairs.

Reading of the observed code (extracted/pseudocode):
  FUN_140dc5d80   trims a common prefix/suffix once, then calls the core
  FUN_140dc60b0   the core:
                    - left range empty      -> every right line is one-sided
                    - right range empty     -> every left line is one-sided
                    - middle-snake overlap  -> recurse(left of snake) and
                                               recurse(right of snake); the
                                               snake is matched (it never emits
                                               a record -- matched lines are the
                                               complement in the report)
                    - a 1x1 rectangle       -> FUN_140dc6c40(...,kind 2), i.e. a
                                               PAIR (this is what turns an
                                               unmatched cell into a
                                               `different`/`similar` row)
  So the reported *pairing* is exactly the recursion's cell decomposition:
  every 1x1 cell becomes a pair, every one-sided leftover becomes an orphan.

Consequence being tested: the shapes BC shows for all-different rectangles
(3x3 -> three pairs; 2x3 -> two pairs + trailing orphan; 4x4 -> leading orphan +
three pairs + trailing orphan; 1x2 -> leading orphan + one pair) are NOT a
positional zip -- they are whatever this recursion produces.

Usage (offline):
    python tools/m26_geometry_lab.py
"""
from __future__ import annotations

import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.setrecursionlimit(100000)

# ----------------------------------------------------------------------
# Middle snake, ported from product/core/src/myers.rs (validated there against
# a brute-force LCS reference).  Returns (a_start, a_end, b_start, b_end) in
# absolute coordinates for the sub-rectangle [a_lo,a_hi) x [b_lo,b_hi).
# ----------------------------------------------------------------------

def _snake_around(a, b, alo, ahi, blo, bhi, x, y):
    ex, ey = x, y
    if x < ahi and y < bhi and a[x] == b[y]:
        while ex < ahi and ey < bhi and a[ex] == b[ey]:
            ex += 1
            ey += 1
    while x > alo and y > blo and a[x - 1] == b[y - 1]:
        x -= 1
        y -= 1
    return x, ex, y, ey


def middle_snake(a, b, alo, ahi, blo, bhi):
    n, m = ahi - alo, bhi - blo
    delta = n - m
    odd = (delta & 1) != 0
    d_bound = (n + m + 1) // 2
    vf, ur = {1: 0}, {1: 0}
    for d in range(d_bound + 1):
        k = -d
        while k <= d:
            if k == -d or (k != d and vf.get(k - 1, 0) < vf.get(k + 1, 0)):
                x = vf.get(k + 1, 0)
            else:
                x = vf.get(k - 1, 0) + 1
            y = x - k
            while x < n and y < m and a[alo + x] == b[blo + y]:
                x += 1
                y += 1
            vf[k] = x
            if odd and (delta - (d - 1)) <= k <= (delta + (d - 1)):
                j = delta - k
                if n - ur.get(j, 0) <= x:
                    return _snake_around(a, b, alo, ahi, blo, bhi,
                                         alo + x, blo + y)
            k += 2
        j = -d
        while j <= d:
            if j == -d or (j != d and ur.get(j - 1, 0) < ur.get(j + 1, 0)):
                u = ur.get(j + 1, 0)
            else:
                u = ur.get(j - 1, 0) + 1
            v = u - j
            while u < n and v < m and a[ahi - 1 - u] == b[bhi - 1 - v]:
                u += 1
                v += 1
            ur[j] = u
            if not odd:
                k = delta - j
                if -d <= k <= d and n - u <= vf.get(k, 0):
                    return _snake_around(a, b, alo, ahi, blo, bhi,
                                         alo + (n - u), blo + (m - v))
            j += 2
    raise AssertionError("search exhausted")


# ----------------------------------------------------------------------
# BC-style recursion: emit cells, not blocks.
# ----------------------------------------------------------------------

def replay(a, b, alo, ahi, blo, bhi, out, depth=0, guard=0):
    """Append ('same'|'pair'|'left'|'right', li|None, rj|None) events in order."""
    if alo == ahi:
        for j in range(blo, bhi):
            out.append(("right", None, j))
        return True
    if blo == bhi:
        for i in range(alo, ahi):
            out.append(("left", i, None))
        return True
    if ahi - alo == 1 and bhi - blo == 1:
        out.append(("pair", alo, blo))
        return True
    if guard > 200:                 # runaway guard for the lab
        raise RuntimeError("recursion guard tripped")
    astart, aend, bstart, bend = middle_snake(a, b, alo, ahi, blo, bhi)
    empty_at_corner = (astart == aend) and ((astart == alo and bstart == blo)
                                            or (aend == ahi and bend == bhi))
    if empty_at_corner:
        # The observed core has no such case: its search only returns a snake
        # once the frontiers overlap, and the overlap split always shrinks the
        # rectangle.  Report it rather than inventing behaviour.
        return False
    if not replay(a, b, alo, astart, blo, bstart, out, depth + 1, guard + 1):
        return False
    for i in range(aend - astart):
        out.append(("same", astart + i, bstart + i))
    if not replay(a, b, aend, ahi, bend, bhi, out, depth + 1, guard + 1):
        return False
    return True


def shape_of(left, right):
    """Deterministic id keys (no importance): pure geometry test."""
    a = list(range(len(left)))
    b = list(range(len(right)))
    out = []
    ok = replay(a, b, 0, len(a), 0, len(b), out)
    return ok, out


CASES = [
    ("3x3 all-different (al-replace-block middle)", ["x", "y", "z"], ["p", "q", "r"]),
    ("2x3 all-different (unequal-replace middle)", ["x", "y"], ["p", "q", "r"]),
    ("4x4 all-different (all-kinds-txt)", ["a", "b4", "c4", "d4"],
     ["w4", "x4", "y4", "z4"]),
    ("1x2 all-different (tail-1v2)", ["?next"], ["x", "next"]),
    ("3x3 .c shape (comment-lead)", ["ca", "p", "r"], ["x", "y", "cs"]),
    ("4x4 .c shape (all-kinds)", ["ca", "p", "cq", "r"], ["x", "cb", "y", "cs"]),
    ("2x3 .c shape (comment-middle)", ["p", "ca", "r"], ["x", "y", "cs"]),
    ("3x3 .txt shape (comment-tail)", ["p", "r", "ca"], ["x", "y", "cs"]),
]


def main() -> int:
    for name, left, right in CASES:
        ok, out = shape_of(left, right)
        cells = [(k, li, rj) for k, li, rj in out]
        status = "OK " if ok else "STOP"
        print(f"== {status} {name}")
        print(f"   left={left}")
        print(f"   right={right}")
        print(f"   cells={cells}")
        pairs = [(li, rj) for k, li, rj in cells if k == "pair"]
        print(f"   pairs={pairs}  (same cells: "
              f"{[(li, rj) for k, li, rj in cells if k == 'same']})")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
