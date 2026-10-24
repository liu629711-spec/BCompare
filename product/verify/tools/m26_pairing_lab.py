#!/usr/bin/env python3
"""M2.6 pairing lab (OFFLINE) -- fit a two-layer alignment model to real BC output.

No Oracle and no product binary run here.  Every observation already exists on
disk as a real BC text report; each report names its own fixtures, so the
(left lines, right lines, chosen pairing) triple is recoverable from disk.

Hypothesis under test (from BC's own evidence)
----------------------------------------------
* `help/sessiontextalignment.html`: the default alignment is "Standard", and
  "Use closeness matching ... attempt[s] to align the remaining mismatched
  lines based on their similarity".
* The emit layer (`FUN_140dc6c40` case 2) treats a 1x1 no-match rectangle as a
  PAIR, so a reported `different`/`similar` row may be a pair chosen by
  similarity, not an exact match.

Model:
  layer 1  anchors = exact matches over *important content* keys
           (a line with no important content -- comment/blank -- either shares
           one sentinel key (product's current behaviour) or is excluded).
  layer 2  each gap between anchors is paired by a monotone maximum-similarity
           matching: maximise (total similarity, pair count), ties -> earliest
           pairs.  Leftovers become one-sided rows.

Layer 2 subsumes the product's positional/anchored strategies: with all-zero
similarity it degenerates to the identity zip (three `different` rows), which is
what the `al-replace-block` anchor records.

Usage (offline):
    python tools/m26_pairing_lab.py
"""
from __future__ import annotations

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
FN_RE = re.compile(r"<filename([12])>(.*?)</filename[12]>", re.S)

SKIP_MARKERS = ("+iu", "-iu", "iu-", "ignore-unimportant",
                "display-matches", "display-mismatches", "display-context")

#: files that are NOT BC output: never ground truth
NOT_ORACLE = (".product.", "product.xml", ".reacmp.")


def is_oracle_report(rel: str) -> bool:
    low = rel.lower()
    if any(m in low for m in NOT_ORACLE):
        return False
    if ".oracle." in low:
        return True
    return "/runs/" not in low and "\\runs\\" not in low

SENTINEL = "\x00UNIMPORTANT"


# ======================================================================
# Line facts (approximation of product/core/src/importance.rs)
# ======================================================================

def facts_plain(line: str):
    """Plain text: case-insensitive, whitespace-insensitive (product semantics:
    the align key is the whitespace-stripped LOWER-CASED line)."""
    seq = "".join(line.split()).lower()
    return (seq if seq else None), seq


def facts_cpp(line: str, block: list):
    """Strip // and /* */ (cross-line), then whitespace."""
    out = []
    i, n = 0, len(line)
    while i < n:
        if block[0]:
            k = line.find("*/", i)
            if k < 0:
                break
            block[0] = False
            i = k + 2
            continue
        if line.startswith("/*", i):
            k = line.find("*/", i + 2)
            if k < 0:
                block[0] = True
                break
            i = k + 2
            continue
        if line.startswith("//", i):
            break
        out.append(line[i])
        i += 1
    seq = "".join("".join(out).split())
    return (seq if seq else None), seq


def facts_python(line: str):
    body = line.split("#", 1)[0]
    seq = "".join(body.split())
    return (seq if seq else None), seq


def make_facts(lines, fmt):
    block = [False]
    keys, norm = [], []
    for ln in lines:
        if fmt == "plain":
            k, t = facts_plain(ln)
        elif fmt == "python":
            k, t = facts_python(ln)
        else:
            k, t = facts_cpp(ln, block)
        keys.append(k)
        norm.append(t)
    return keys, norm


# ======================================================================
# Myers port (mirrors product/core/src/myers.rs)
# ======================================================================

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


def _middle_snake(a, b, alo, ahi, blo, bhi):
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


def _lcs_empty(a, b, alo, ahi, blo, bhi):
    s, l = ((a[alo:ahi], b[blo:bhi]) if ahi - alo <= bhi - blo
            else (b[blo:bhi], a[alo:ahi]))
    return not (set(s) & set(l))


def myers_matches(a, b):
    out = []

    def emit(astart, bstart, ln):
        for i in range(ln):
            out.append((astart + i, bstart + i))

    def rec(alo, ahi, blo, bhi):
        pre = 0
        while alo + pre < ahi and blo + pre < bhi and a[alo + pre] == b[blo + pre]:
            pre += 1
        if pre:
            emit(alo, blo, pre)
            alo += pre
            blo += pre
        if alo == ahi or blo == bhi:
            return
        suf = 0
        while ahi - suf > alo and bhi - suf > blo and a[ahi - 1 - suf] == b[bhi - 1 - suf]:
            suf += 1
        ahi_in, bhi_in = ahi - suf, bhi - suf
        if alo == ahi_in or blo == bhi_in:
            if suf:
                emit(ahi - suf, bhi - suf, suf)
            return
        if ahi_in - alo == 1 or bhi_in - blo == 1:
            if ahi_in - alo == 1:
                val = a[alo]
                for off, v in enumerate(b[blo:bhi_in]):
                    if v == val:
                        out.append((alo, blo + off))
                        break
            else:
                val = b[blo]
                for off, v in enumerate(a[alo:ahi_in]):
                    if v == val:
                        out.append((alo + off, blo))
                        break
            if suf:
                emit(ahi - suf, bhi - suf, suf)
            return
        if min(ahi_in - alo, bhi_in - blo) <= 32 and _lcs_empty(
                a, b, alo, ahi_in, blo, bhi_in):
            if suf:
                emit(ahi - suf, bhi - suf, suf)
            return
        astart, aend, bstart, bend = _middle_snake(a, b, alo, ahi_in, blo, bhi_in)
        if astart == aend and ((astart == alo and bstart == blo)
                               or (aend == ahi_in and bend == bhi_in)):
            if _lcs_empty(a, b, alo, ahi_in, blo, bhi_in):
                if suf:
                    emit(ahi - suf, bhi - suf, suf)
                return
            raise AssertionError("no progress")
        rec(alo, astart, blo, bstart)
        if aend > astart:
            emit(astart, bstart, aend - astart)
        rec(aend, ahi_in, bend, bhi_in)
        if suf:
            emit(ahi - suf, bhi - suf, suf)

    if a and b:
        rec(0, len(a), 0, len(b))
    return out


# ======================================================================
# Similarity metrics
# ======================================================================

def lcs_len(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b):
            cur[j + 1] = prev[j] + 1 if ca == cb else max(prev[j + 1], cur[j])
        prev = cur
    return prev[-1]


def pref_suf(a: str, b: str) -> int:
    p = 0
    for x, y in zip(a, b):
        if x != y:
            break
        p += 1
    s = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        s += 1
    return p + s


def tok_lcs(a: str, b: str) -> int:
    ta, tb = a.split(), b.split()
    if not ta or not tb:
        return 0
    prev = [0] * (len(tb) + 1)
    for x in ta:
        cur = [0] * (len(tb) + 1)
        for j, y in enumerate(tb):
            cur[j + 1] = prev[j] + 1 if x == y else max(prev[j + 1], cur[j])
        prev = cur
    return prev[-1]


def mk_sim(kind):
    if kind == "ws-cs":
        return lcs_len
    if kind == "ws-ci":
        return lambda a, b: lcs_len(a.lower(), b.lower())
    if kind == "raw-cs":
        return lambda a, b: lcs_len(a, b)
    if kind == "pref":
        return pref_suf
    if kind == "tok-ci":
        return lambda a, b: tok_lcs(a.lower(), b.lower())
    raise ValueError(kind)


# ======================================================================
# Gap pairing: monotone matching maximising (score, pairs), earliest ties
# ======================================================================

def pair_gap(ls, rs, sim, raw_l, raw_r):
    """Monotone pairing of one gap.

    Objective, lexicographic: maximise (total similarity, pair count).  Ties
    resolve to the EARLIEST pairs.  Zero-similarity cells are still allowed to
    pair when doing so raises the count, so an all-different gap degenerates to
    the identity zip -- which is what BC shows for a replaced block
    (`al-replace-block`: h1 x y z h2 vs h1 p q r h2 gives three `different`
    rows, not two `same` rows and one orphan block).
    """
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    sc = [[sim(raw_l[ls[i]], raw_r[rs[j]]) for j in range(m)] for i in range(n)]
    f = [[(0, 0)] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = f[i + 1][j] if f[i + 1][j] >= f[i][j + 1] else f[i][j + 1]
            prev = f[i + 1][j + 1]
            cand = (prev[0] + sc[i][j], prev[1] + 1)
            if cand > best:
                best = cand
            f[i][j] = best
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        prev = f[i + 1][j + 1]
        cand = (prev[0] + sc[i][j], prev[1] + 1)
        if cand == f[i][j]:
            pairs.append((ls[i], rs[j]))
            i += 1
            j += 1
            continue
        if f[i][j + 1] == f[i][j]:
            j += 1
        elif f[i + 1][j] == f[i][j]:
            i += 1
        else:
            break
    return pairs


# ======================================================================
# Two-layer model
# ======================================================================

def model_pairs(left, right, fmt, anchor_mode, sim, raw_l, raw_r):
    lkeys, lnorm = make_facts(left, fmt)
    rkeys, rnorm = make_facts(right, fmt)

    def key_seq(keys, tag):
        out, fresh = [], 0
        for k in keys:
            if k is None:
                if anchor_mode == "sentinel":
                    out.append(SENTINEL)
                else:
                    # excluded: a key that can never equal anything else
                    out.append(f"\x01{tag}{fresh}")
                    fresh += 1
            else:
                out.append(k)
        return out

    lk, rk = key_seq(lkeys, "L"), key_seq(rkeys, "R")
    anchors = myers_matches(lk, rk)

    pairs = list(anchors)
    bounds = [(-1, -1)] + anchors + [(len(left), len(right))]
    for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
        ls = list(range(pl + 1, nl))
        rs = list(range(pr + 1, nr))
        if ls and rs:
            pairs.extend(pair_gap(ls, rs, sim, raw_l, raw_r))
    return sorted(pairs)


# ======================================================================
# Corpus + evaluation
# ======================================================================

def rows_of(body):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2))
        rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out


def read_lines(p):
    try:
        return p.read_bytes().decode("utf-8-sig", errors="replace").splitlines()
    except OSError:
        return None


def fmt_of(path: str) -> str:
    """Format from the FILE path, never from the report path (a report about
    `x.c` lives in a directory whose own name says nothing about the grammar)."""
    low = path.lower()
    if low.endswith(".py"):
        return "python"
    if low.endswith((".c", ".cc", ".cpp", ".cs", ".h", ".hpp", ".m", ".java",
                     ".js", ".sql")):
        return "cpp"
    return "plain"


def collect():
    cases, seen = [], set()
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for xml in sorted(root.rglob("*.xml")):
            rel = str(xml.relative_to(REA)).replace("\\", "/")
            low = rel.lower()
            if any(m in low for m in SKIP_MARKERS):
                continue
            if not is_oracle_report(rel):
                continue
            if "/runs/" in low and "m26-weighted-probe" not in low:
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
            left, right = read_lines(lp), read_lines(rp)
            if left is None or right is None:
                continue
            rows = rows_of(body)
            if not rows:
                continue
            lseen = sorted(lt for _s, lt, _r in rows if lt)
            rseen = sorted(rt for _s, _l, rt in rows if rt)
            if lseen != list(range(1, len(left) + 1)):
                continue                    # not full coverage: skip
            if rseen != list(range(1, len(right) + 1)):
                continue
            key = (str(lp), str(rp), tuple(rows))
            if key in seen:
                continue
            seen.add(key)
            cases.append({"src": rel, "left": left, "right": right,
                          "left_path": str(lp),
                          "pairs": [(lt - 1, rt - 1) for _s, lt, rt in rows
                                    if lt and rt]})
    return cases


def main() -> int:
    cases = collect()
    print(f"collected {len(cases)} full-coverage BC text observations\n")

    results = {}
    for anchor_mode in ("sentinel", "excluded"):
        for kind in ("ws-cs", "ws-ci", "raw-cs", "pref"):
            ok, bad = 0, []
            for c in cases:
                fmt = fmt_of(c["left_path"])
                got = model_pairs(c["left"], c["right"], fmt, anchor_mode,
                                  mk_sim(kind), c["left"], c["right"])
                if sorted(got) == sorted(c["pairs"]):
                    ok += 1
                else:
                    bad.append((c, got))
            results[(anchor_mode, kind)] = (ok, bad)

    print("=== pairing fit ===")
    for (am, kd), (ok, _b) in sorted(results.items(), key=lambda kv: -kv[1][0]):
        print(f"  anchors={am:<9} sim={kd:<7} {ok}/{len(cases)}")
    print()

    best = max(results, key=lambda k: results[k][0])
    ok, bad = results[best]
    print(f"=== {len(bad)} failures of anchors={best[0]} sim={best[1]} ===")
    for c, got in bad:
        print(f"-- {c['src']}")
        print(f"   L={c['left']}")
        print(f"   R={c['right']}")
        print(f"   BC   pairs={c['pairs']}")
        print(f"   model      ={got}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
