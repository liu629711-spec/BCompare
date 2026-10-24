#!/usr/bin/env python3
"""M2.6 pairing lab (OFFLINE): fit candidate alignment/pairing models to ALL
recorded BC text reports on disk.

No Oracle and no product binary are invoked.  Every observation already exists:
`verify/golden/*.xml`, `verify/disambig/*.xml`, `verify/cases/*.xml`, and
`product/verify/runs/**/reports/*.xml` are real BC reports, and each report
names its own fixtures (`<filename1>`/`<filename2>`), so the (left, right,
rows) triple is fully recoverable from disk.

What is compared: the *pairing structure* (which left line pairs with which
right line; which lines are one-sided), not the status vocabulary.  Verdicts
(same/similar/different) follow from the pair plus the importance engine and
are already covered by the 101 anchors; M2.6 is about the pairing.

Candidate model: monotone maximum-similarity matching (a weighted-LCS DP) over
each unmatched region, with unpaired lines free.  BC's own help calls the
feature "Use closeness matching"; the M2.6 divergence cases (all-kinds,
tail-1v2) are exactly where a similarity-driven pairing differs from the
product's positional/anchored strategies.

Usage (offline):
    python tools/_scratch/m26_pairing_lab.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

REA = pathlib.Path(r"D:\Rea")
SEARCH_ROOTS = [
    REA / "verify" / "golden",
    REA / "verify" / "disambig",
    REA / "verify" / "cases",
    REA / "product" / "verify" / "runs",
]

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(\d+)"')
RTID_RE = re.compile(r'rtid="(\d+)"')
FN_RE = re.compile(r"<filename([12])>(.*?)</filename\1>", re.S)

#: report paths whose rows are filtered/folded and therefore not a full pairing
SKIP_MARKERS = ("+iu", "-iu", "iu-", "ignore-unimportant",
                "display-matches", "display-mismatches", "display-context")


def rows_of(body: str):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2))
        rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out


def read_lines(p: pathlib.Path):
    try:
        return p.read_bytes().decode("utf-8-sig", errors="replace").splitlines()
    except OSError:
        return None


def collect() -> list[dict]:
    cases, seen = [], set()
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for xml in sorted(root.rglob("*.xml")):
            rel = str(xml.relative_to(REA)).replace("\\", "/")
            if any(m in rel.lower() for m in SKIP_MARKERS):
                continue
            try:
                body = xml.read_bytes().decode("utf-8-sig", errors="replace")
            except OSError:
                continue
            fns = dict(FN_RE.findall(body))
            if "1" not in fns or "2" not in fns:
                continue
            lp, rp = pathlib.Path(fns["1"]), pathlib.Path(fns["2"])
            if not lp.exists() or not rp.exists():
                continue
            key = (str(lp), str(rp), body)
            if key in seen:
                continue
            seen.add(key)
            rows = rows_of(body)
            if not rows:
                continue
            left, right = read_lines(lp), read_lines(rp)
            if left is None or right is None:
                continue
            cases.append({"src": rel, "left": left, "right": right,
                          "rows": rows})
    return cases


# ----------------------------------------------------------------------
# Similarity metrics
# ----------------------------------------------------------------------

def lcs_len(a: str, b: str) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b):
            cur[j + 1] = prev[j] + 1 if ca == cb else max(prev[j + 1], cur[j])
        prev = cur
    return prev[-1]


def common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def common_suffix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        n += 1
    return n


METRICS = {
    "lcs": lambda a, b: lcs_len(a, b),
    "lcs-ci": lambda a, b: lcs_len(a.lower(), b.lower()),
    "prefix+suffix": lambda a, b: common_prefix(a, b) + common_suffix(a, b),
    "multiset": lambda a, b: sum((__import__("collections").Counter(a) &
                                  __import__("collections").Counter(b)).values()),
}


# ----------------------------------------------------------------------
# Model: monotone max-similarity matching per two-sided block.
# ----------------------------------------------------------------------

def blocks_from_pairs(nl: int, nr: int, pairs):
    out, ai, bi = [], 0, 0
    for li, rj in pairs:
        if li > ai or rj > bi:
            out.append((ai, li, bi, rj))
        ai, bi = li + 1, rj + 1
    if ai < nl or bi < nr:
        out.append((ai, nl, bi, nr))
    return out


def pair_block_dp(left, right, ls, rs, sim, prefer_pair_on_tie=True):
    """Monotone max-similarity pairing inside one block.
    ls/rs are 0-based line indices; returns list of (li, rj) pairs."""
    n, m = len(ls), len(rs)
    # dp[i][j] = best score over first i left, first j right lines
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    ch = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            up, lf = dp[i - 1][j], dp[i][j - 1]
            diag = dp[i - 1][j - 1] + sim(left[ls[i - 1]], right[rs[j - 1]])
            best, how = up, "up"
            if lf > best:
                best, how = lf, "left"
            if diag > best or (prefer_pair_on_tie and diag == best and diag > dp[i - 1][j - 1]):
                best, how = diag, "diag"
            dp[i][j] = best
            ch[i][j] = how
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        how = ch[i][j]
        if how == "diag":
            pairs.append((ls[i - 1], rs[j - 1]))
            i, j = i - 1, j - 1
        elif how == "up":
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return pairs


def model_pairs(left, right, sim):
    """Pure closeness model: one global monotone matching."""
    ls = list(range(len(left)))
    rs = list(range(len(right)))
    return pair_block_dp(left, right, ls, rs, sim)


def bc_pairs(case):
    """The pairing BC's report shows: list of (li, rj) 0-based pairs."""
    out = []
    for _st, lt, rt in case["rows"]:
        if lt is not None and rt is not None:
            out.append((lt - 1, rt - 1))
    return out


def bc_orphans(case):
    lo = [lt - 1 for _s, lt, rt in case["rows"] if lt is not None and rt is None]
    ro = [rt - 1 for _s, lt, rt in case["rows"] if rt is not None and lt is None]
    return lo, ro


def main() -> int:
    cases = collect()
    print(f"collected {len(cases)} default-mode BC text observations\n")

    results = {}
    for mname, sim in METRICS.items():
        for pref in (True, False):
            tag = f"{mname}/pref={pref}"
            ok, bad = 0, []
            for c in cases:
                got_pairs = model_pairs(c["left"], c["right"], sim)
                want = bc_pairs(c)
                if sorted(got_pairs) == sorted(want):
                    ok += 1
                else:
                    bad.append((c, got_pairs, want))
            results[tag] = (ok, bad)

    print("=== model fit (pairing equality) ===")
    for tag, (ok, bad) in sorted(results.items(), key=lambda kv: -kv[1][0]):
        print(f"  {tag:<26} {ok}/{len(cases)}")
    print()

    best_tag = max(results, key=lambda t: results[t][0])
    ok, bad = results[best_tag]
    print(f"=== failures of {best_tag} ({len(bad)}) ===")
    for c, got, want in bad:
        print(f"-- {c['src']}")
        print(f"   L={c['left']}")
        print(f"   R={c['right']}")
        print(f"   BC   pairs(0-based)={want}")
        print(f"   model            ={got}")
        print(f"   BC rows={c['rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
