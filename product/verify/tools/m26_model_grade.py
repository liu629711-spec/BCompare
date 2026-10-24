#!/usr/bin/env python3
"""M2.6 model validation (OFFLINE) -- grade one alignment model against every
recorded BC text observation on disk.

No Oracle and no product binary run here.  Each BC report on disk names its own
fixtures, so (left lines, right lines, chosen pairing) is recoverable.

Model under test
----------------
A. keys: a line's alignment key is its IMPORTANT text (comments/whitespace
   removed; plain text is whitespace-stripped and lower-cased).  A line with NO
   important text (comment/blank/whitespace-only) is given a key that can never
   equal any other line, so it never anchors.
B. anchors: Myers over those keys (the product's `myers.rs`, forward-first).
C. gaps: between consecutive anchors, the remaining lines are paired by a
   monotone maximum-similarity matching whose score is the total longest-common-
   subsequence length over the closeness texts (verbatim lines for plain text —
   case-sensitive, M5.1b; important text for syntax formats); ties are broken
   by MORE pairs, then by the minimum total paired LEFT length (the m51c
   `tie-len-*` shapes), then by EARLIER pairs.  Unpaired lines become
   one-sided rows.
D. statuses: a pair is `same` when the raw lines are equal, `similar` when the
   important text is equal, else `different`; a one-sided line is
   `leftsimilar`/`rightsimilar` when it has no important content, else
   `leftorphan`/`rightorphan`.

Why this model: BC's help states the default alignment is "Standard" with an
optional "Use closeness matching ... based on their similarity"; the emit layer
(`FUN_140dc6c40`) turns a 1x1 unmatched cell into a paired row, so `different`
rows are chosen pairs; and the recorded corpus pins the anchor layer to
*important-text* equality (the swap cases would otherwise pick a higher-similarity
crossing pair).

Usage (offline):
    cd D:\\Rea\\product\\verify
    python tools/m26_model_grade.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

REA = pathlib.Path(r"D:\Rea")

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(\d+)"')
RTID_RE = re.compile(r'rtid="(\d+)"')
FN_RE = re.compile(r"<filename([12])>(.*?)</filename[12]>", re.S)
TEXT_RE = re.compile(r'<text([^>]*)>(.*?)</text>', re.S)

SKIP_MARKERS = ("+iu", "-iu", "iu-", "ignore-unimportant",
                "display-matches", "display-mismatches", "display-context")
NOT_ORACLE = (".product.", "product.xml", ".reacmp.")
PROBE_OK = ("m26-weighted-probe", "u8h-probe", "u2-probe", "u2b-probe",
            "u6-probe", "u7-probe", "u8f-probe")


# ======================================================================
# BC-compatible line splitting
# ======================================================================

def split_bc(raw: bytes):
    """Decode and split the way the report implies (LF / CRLF / CR)."""
    text = raw.decode("utf-8-sig", errors="replace")
    if "\ufffd" in text:                 # code-page case: not a pairing test
        return None
    if text == "":
        return []
    lines = re.split(r"\r\n|\n|\r", text)
    if lines and lines[-1] == "":
        lines.pop()
    return lines


# ======================================================================
# Line facts
# ======================================================================

def block_strip(line: str, block: list) -> str:
    out, i, n = [], 0, len(line)
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
    return "".join(out)


def facts(lines, fmt):
    """(important text, is_unimportant) per line."""
    block = [False]
    out = []
    for ln in lines:
        if fmt == "plain":
            seq = "".join(ln.split()).lower()
        elif fmt == "python":
            seq = "".join(ln.split("#", 1)[0].split())
        else:
            seq = "".join(block_strip(ln, block).split())
        out.append(seq)
    return out


def close_texts(lines, fmt):
    """The text the closeness pass scores similarity on (M5.1b).

    Plain text uses the verbatim line — case-sensitive, because the m51b
    `cs-check` shape shows BC zipping [bbbb, xx] vs [X, Y] into two zero-score
    pairs, which lower-cased text (`xx` scoring 1 against `X`) never produces.
    Syntax formats keep the important text: comments carry no weight there,
    which is what the recorded m26 comment pairings show.
    """
    if fmt == "plain":
        return list(lines)
    return facts(lines, fmt)


def fmt_of(path: str) -> str:
    low = path.lower()
    if low.endswith(".py"):
        return "python"
    if low.endswith((".c", ".cc", ".cpp", ".cs", ".h", ".hpp", ".m",
                     ".jav", ".java", ".js", ".sql")):
        return "cpp"
    return "plain"


# ======================================================================
# Myers (port of product/core/src/myers.rs)
# ======================================================================

def _snake(a, b, alo, ahi, blo, bhi, x, y):
    ex, ey = x, y
    if x < ahi and y < bhi and a[x] == b[y]:
        while ex < ahi and ey < bhi and a[ex] == b[ey]:
            ex += 1
            ey += 1
    while x > alo and y > blo and a[x - 1] == b[y - 1]:
        x -= 1
        y -= 1
    return x, ex, y, ey


def _middle(a, b, alo, ahi, blo, bhi):
    n, m = ahi - alo, bhi - blo
    delta = n - m
    odd = (delta & 1) != 0
    bound = (n + m + 1) // 2
    vf, ur = {1: 0}, {1: 0}
    for d in range(bound + 1):
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
                    return _snake(a, b, alo, ahi, blo, bhi, alo + x, blo + y)
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
                    return _snake(a, b, alo, ahi, blo, bhi,
                                  alo + (n - u), blo + (m - v))
            j += 2
    raise AssertionError("exhausted")


def _lcs_empty(a, b, alo, ahi, blo, bhi):
    s, l = ((a[alo:ahi], b[blo:bhi]) if ahi - alo <= bhi - blo
            else (b[blo:bhi], a[alo:ahi]))
    return not (set(s) & set(l))


def myers(a, b):
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
        ai, bi = ahi - suf, bhi - suf
        if alo == ai or blo == bi:
            if suf:
                emit(ahi - suf, bhi - suf, suf)
            return
        if ai - alo == 1 or bi - blo == 1:
            if ai - alo == 1:
                val = a[alo]
                for off, v in enumerate(b[blo:bi]):
                    if v == val:
                        out.append((alo, blo + off))
                        break
            else:
                val = b[blo]
                for off, v in enumerate(a[alo:ai]):
                    if v == val:
                        out.append((alo + off, blo))
                        break
            if suf:
                emit(ahi - suf, bhi - suf, suf)
            return
        if min(ai - alo, bi - blo) <= 32 and _lcs_empty(a, b, alo, ai, blo, bi):
            if suf:
                emit(ahi - suf, bhi - suf, suf)
            return
        a0, a1, b0, b1 = _middle(a, b, alo, ai, blo, bi)
        if a0 == a1 and ((a0 == alo and b0 == blo) or (a1 == ai and b1 == bi)):
            if _lcs_empty(a, b, alo, ai, blo, bi):
                if suf:
                    emit(ahi - suf, bhi - suf, suf)
                return
            raise AssertionError("no progress")
        rec(alo, a0, blo, b0)
        if a1 > a0:
            emit(a0, b0, a1 - a0)
        rec(a1, ai, b1, bi)
        if suf:
            emit(ahi - suf, bhi - suf, suf)

    if a and b:
        rec(0, len(a), 0, len(b))
    return out


# ======================================================================
# Similarity + gap pairing
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


def pair_gap(ls, rs, texts_l, texts_r):
    """Monotone matching maximising (total LCS, pair count); then minimum
    paired LEFT length; earliest on what remains (M5.1b, m51b/m51c probes).

    The third key is left-only: a monotone count-max matching always spends
    the first k right lines, so which right lines pair is never a choice.
    """
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    sc = [[lcs_len(texts_l[ls[i]], texts_r[rs[j]]) for j in range(m)]
          for i in range(n)]
    f = [[(0, 0, 0)] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = f[i + 1][j] if _better(f[i + 1][j], f[i][j + 1]) else f[i][j + 1]
            prev = f[i + 1][j + 1]
            cand = (prev[0] + sc[i][j], prev[1] + 1, prev[2] + len(texts_l[ls[i]]))
            if _better(cand, best):
                best = cand
            f[i][j] = best
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        prev = f[i + 1][j + 1]
        cand = (prev[0] + sc[i][j], prev[1] + 1, prev[2] + len(texts_l[ls[i]]))
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


def _better(a, b):
    """max (score, count), then min left length."""
    if a[0] != b[0]:
        return a[0] > b[0]
    if a[1] != b[1]:
        return a[1] > b[1]
    return a[2] <= b[2]


def model_leaves(left, right, texts_l, texts_r, ctexts_l, ctexts_r):
    """(pairs, left_orphans, right_orphans) for the model described in the docstring."""
    lk = [t if t else f"\x01L{i}" for i, t in enumerate(texts_l)]
    rk = [t if t else f"\x01R{j}" for j, t in enumerate(texts_r)]
    anchors = myers(lk, rk)
    pairs = list(anchors)
    bounds = [(-1, -1)] + list(anchors) + [(len(left), len(right))]
    for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
        ls = list(range(pl + 1, nl))
        rs = list(range(pr + 1, nr))
        if ls and rs:
            pairs.extend(pair_gap(ls, rs, ctexts_l, ctexts_r))
    pairs = sorted(pairs)
    used_l = {i for i, _ in pairs}
    used_r = {j for _, j in pairs}
    lo = [i for i in range(len(left)) if i not in used_l]
    ro = [j for j in range(len(right)) if j not in used_r]
    return pairs, lo, ro


def model_rows(left, right, texts_l, texts_r, ctexts_l, ctexts_r):
    """Emit the report rows (status, ltid, rtid) the model predicts, 1-based."""
    pairs, lo, ro = model_leaves(left, right, texts_l, texts_r, ctexts_l, ctexts_r)
    events = order_events(pairs, lo, ro)
    rows = []
    for kind, i, j in events:
        if kind == "pair":
            if left[i] == right[j]:
                st = "same"
            elif texts_l[i] == texts_r[j]:
                st = "similar"
            else:
                st = "different"
            rows.append((st, i + 1, j + 1))
        elif kind == "left":
            st = "leftsimilar" if not texts_l[i] else "leftorphan"
            rows.append((st, i + 1, None))
        else:
            st = "rightsimilar" if not texts_r[j] else "rightorphan"
            rows.append((st, None, j + 1))
    return rows


def order_events(pairs, lo, ro):
    """Report order = the anchor stream with each gap's orphans emitted between
    the pairings that bound them.

    BC's emitter appends one-sided runs as the subdivision discovers them and
    treats matched runs as the gaps between them, so an orphan always sits at
    its own document position: `al-insert` (a,c vs a,b,c) reports
    `same, rightorphan(b), same`, and the m26 `tail-1v2` case reports
    `rightorphan(x)` BEFORE the trailing replacement.  Sorting orphans by
    coordinate alone gets this wrong (an orphan's coordinate can be larger than
    the following pair's left coordinate), so the gap structure is used.
    """
    events = []
    prev = (-1, -1)
    for nl, nr in list(pairs) + [(10 ** 18, 10 ** 18)]:
        events.extend(("left", i, None) for i in lo if prev[0] < i < nl)
        events.extend(("right", None, j) for j in ro if prev[1] < j < nr)
        if nl != 10 ** 18:
            events.append(("pair", nl, nr))
        prev = (nl, nr)
    return events


def _unused_placeholder():
    rows = []
    for kind, i, j in events:
        if kind == "pair":
            if left[i] == right[j]:
                st = "same"
            elif texts_l[i] == texts_r[j]:
                st = "similar"
            else:
                st = "different"
            rows.append((st, i + 1, j + 1))
        elif kind == "left":
            st = "leftsimilar" if not texts_l[i] else "leftorphan"
            rows.append((st, i + 1, None))
        else:
            st = "rightsimilar" if not texts_r[j] else "rightorphan"
            rows.append((st, None, j + 1))
    return rows


# ======================================================================
# Corpus
# ======================================================================

def is_oracle_report(rel: str) -> bool:
    low = rel.lower()
    if any(m in low for m in NOT_ORACLE):
        return False
    if ".oracle." in low:
        return True
    if "/runs/" in low or "\\runs\\" in low:
        return any(p in low for p in PROBE_OK)
    return True


def rows_of(body):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2))
        rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out


def collect():
    roots = [REA / "verify" / "golden", REA / "verify" / "disambig",
             REA / "verify" / "cases", REA / "product" / "verify" / "runs"]
    cases, seen = [], set()
    for root in roots:
        if not root.exists():
            continue
        for xml in sorted(root.rglob("*.xml")):
            rel = str(xml.relative_to(REA)).replace("\\", "/")
            low = rel.lower()
            if any(m in low for m in SKIP_MARKERS) or not is_oracle_report(rel):
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
            left, right = split_bc(lp.read_bytes()), split_bc(rp.read_bytes())
            if left is None or right is None:
                continue                 # code-page case: decode-layer test
            rows = rows_of(body)
            if not rows:
                continue
            if sorted(lt for _s, lt, _r in rows if lt) != list(range(1, len(left) + 1)):
                continue
            if sorted(rt for _s, _l, rt in rows if rt) != list(range(1, len(right) + 1)):
                continue
            # sanity: the report's own text fields must agree with the fixtures
            if not report_texts_match(body, left, right):
                continue
            key = (str(lp), str(rp), tuple(rows))
            if key in seen:
                continue
            seen.add(key)
            cases.append({"src": rel, "left_path": str(lp), "right_path": str(rp),
                          "left": left, "right": right, "bc_rows": rows})
    return cases


def report_texts_match(body, left, right) -> bool:
    """Cheap guard: every reported text field must be a prefix of the fixture
    line it names (reports may elide long lines)."""
    for m in TEXT_RE.finditer(body):
        attrs, text = m.group(1), m.group(2)
        lt = re.search(r'ltid="(\d+)"', attrs)
        rt = re.search(r'rtid="(\d+)"', attrs)
        for side, tid in (("l", lt), ("r", rt)):
            if not tid:
                continue
            idx = int(tid.group(1)) - 1
            lines = left if side == "l" else right
            if idx >= len(lines):
                return False
            got = unescape_xml(text)
            want = lines[idx]
            if got and not want.startswith(got[:max(1, len(got) - 1)]):
                return False
    return True


def unescape_xml(s: str) -> str:
    for a, b in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                 ("&apos;", "'"), ("&#0;", "\x00"), ("&amp;", "&")):
        s = s.replace(a, b)
    return s


def main() -> int:
    cases = collect()
    print(f"grading the model against {len(cases)} recorded BC observations\n")

    ok, bad = 0, []
    for c in cases:
        fmt = fmt_of(c["left_path"])
        tl = facts(c["left"], fmt)
        tr = facts(c["right"], fmt)
        ctl = close_texts(c["left"], fmt)
        ctr = close_texts(c["right"], fmt)
        got = model_rows(c["left"], c["right"], tl, tr, ctl, ctr)
        if got == c["bc_rows"]:
            ok += 1
        else:
            bad.append((c, got))

    print(f"=== agreement: {ok}/{len(cases)} ===")
    for c, got in bad:
        print(f"\n-- {c['src']}")
        print(f"   L={c['left']}")
        print(f"   R={c['right']}")
        print(f"   BC   ={c['bc_rows']}")
        print(f"   model={got}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REA / "product" / "verify" / "runs" / f"m26-model-grade-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "m26-model-grade.json").write_text(json.dumps(
        {"total": len(cases), "agree": ok,
         "failures": [{"src": c["src"], "left": c["left"], "right": c["right"],
                       "bc": c["bc_rows"], "model": got} for c, got in bad]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {out / 'm26-model-grade.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
