#!/usr/bin/env python3
"""M5.5 model lab (OFFLINE) -- test the decompiled token-hash pairing model.

`FUN_140de2f30` (BcAlign.pas) shows BC's closeness measure: skip whitespace,
maximal alphanumeric runs are tokens, each punctuation char is a singleton
token, tokens are case-(?)folded and hashed, and the matcher aligns the TOKEN
HASH sequences. This lab grades line-pairing models built on that discovery
against every recorded BC answer on disk:

  * the 234 recorded XML observations (`m26_model_grade.collect`),
  * the 120 fuzz cases (`runs/m54-fuzz-20261014T170917Z`, oracle XML saved).

Variants (axes):
  anchor   raw-exact (m51b f0019) vs ci-folded important text (m2.6 status quo)
  score    unweighted token-hash LCS vs token-length-weighted LCS
  hash     additive fold-hash (order-free) over [a-zA-Z0-9] runs

Everything else stays as measured in M5.1: (score, pair count) lexicographic,
then minimum paired-left length, then earliest; statuses from the importance
verdict. Usage:
    cd D:\\Rea\\product\\verify
    python tools/m55_model_lab.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
sys.path.insert(0, str(REA / "product" / "verify" / "tools"))

from m26_model_grade import (  # noqa: E402
    _better, collect, facts, fmt_of, myers, order_events, split_bc,
)


def tokens(line: str) -> list[int]:
    """Token hashes: whitespace skipped, alnum runs folded+hashed, punct singletons.

    Returns (hashes, lengths) -- the matcher weights matched tokens by their
    character span on the left side.
    """
    hashes: list[int] = []
    lens: list[int] = []
    cur = ""
    for ch in line:
        if ch.isspace():
            if cur:
                hashes.append(_hash(cur))
                lens.append(len(cur))
                cur = ""
        elif ch.isalnum():
            cur += ch
        else:
            if cur:
                hashes.append(_hash(cur))
                lens.append(len(cur))
                cur = ""
            hashes.append(ord(ch))
            lens.append(1)
    if cur:
        hashes.append(_hash(cur))
        lens.append(len(cur))
    return hashes, lens


def _hash(run: str) -> int:
    import zlib
    raw = b"".join(ord(ch).to_bytes(2, "little") for ch in run)
    return zlib.crc32(raw) & 0xFFFFFFFF


def lcs_weighted(a: list[int], b: list[int], wa: list[int], wb: list[int],
                 weighted: bool) -> tuple[int, int]:
    """(matched token count, matched char weight) of the best token alignment."""
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 0, 0
    f = [[(0, 0)] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = max(f[i + 1][j], f[i][j + 1])
            if a[i] == b[j]:
                w = wa[i] if weighted else 1
                cand = (f[i + 1][j + 1][0] + 1, f[i + 1][j + 1][1] + w)
                if cand > best:
                    best = cand
            f[i][j] = best
    return f[0][0]


def pair_gap(ls, rs, tok_l, tok_r, tok_wl, tok_wr, weighted):
    """Monotone line matching maximizing (token score, pair count), then
    min-left-len, then earliest -- the M5.1 objective with token scores."""
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    sc = [[lcs_weighted(tok_l[i], tok_r[j], tok_wl[i], tok_wr[j], weighted)
           for j in rs] for i in ls]
    f = [[(0, 0, 0)] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = f[i + 1][j] if _better(f[i + 1][j], f[i][j + 1]) else f[i][j + 1]
            prev = f[i + 1][j + 1]
            cand = (prev[0] + sc[i][j][0], prev[1] + 1, prev[2] + len(left_lines[ls[i]]))
            if _better(cand, best):
                best = cand
            f[i][j] = best
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        prev = f[i + 1][j + 1]
        cand = (prev[0] + sc[i][j][0], prev[1] + 1, prev[2] + len(left_lines[ls[i]]))
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


def model_rows(left, right, texts_l, texts_r, *, anchor: str, weighted: bool):
    """Full (status, ltid, rtid) rows under the token-hash model."""
    global left_lines
    left_lines = left
    parsed_l = [tokens(t) for t in left]
    parsed_r = [tokens(t) for t in right]
    tok_l = [h for h, _ in parsed_l]
    tok_r = [h for h, _ in parsed_r]
    tok_wl = [w for _, w in parsed_l]
    tok_wr = [w for _, w in parsed_r]

    if anchor == "raw":
        lk = [t if t else f"\x01L{i}" for i, t in enumerate(left)]
        rk = [t if t else f"\x01R{j}" for j, t in enumerate(right)]
    else:  # ci: folded important text (the m2.6 status quo)
        lk = [t if t else f"\x01L{i}" for i, t in enumerate(texts_l)]
        rk = [t if t else f"\x01R{j}" for j, t in enumerate(texts_r)]
    anchors = myers(lk, rk)

    pairs = list(anchors)
    bounds = [(-1, -1)] + list(anchors) + [(len(left), len(right))]
    for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
        ls = list(range(pl + 1, nl))
        rs = list(range(pr + 1, nr))
        if ls and rs:
            pairs.extend(pair_gap(ls, rs, tok_l, tok_r, tok_wl, tok_wr, weighted))
    pairs = sorted(pairs)
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


left_lines: list[str] = []


def parse_xml_rows(body: str) -> list[list]:
    rows = []
    for m in re.finditer(r'<linecomp status="(\w+)">(.*?)</linecomp>', body, re.S):
        lt = re.search(r'ltid="(-?\d+)"', m.group(2))
        rt = re.search(r'rtid="(-?\d+)"', m.group(2))
        rows.append([m.group(1), int(lt.group(1)) if lt else None,
                     int(rt.group(1)) if rt else None])
    return rows


def incumbent_rows(left, right, texts_l, texts_r):
    """The shipped M5.1 model: ci anchors + (LCS score, count, min-left-len)."""
    lk = [t if t else f"\x01L{i}" for i, t in enumerate(texts_l)]
    rk = [t if t else f"\x01R{j}" for j, t in enumerate(texts_r)]
    anchors = myers(lk, rk)
    pairs = list(anchors)
    bounds = [(-1, -1)] + list(anchors) + [(len(left), len(right))]
    global left_lines
    left_lines = left
    for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
        ls = list(range(pl + 1, nl))
        rs = list(range(pr + 1, nr))
        if ls and rs:
            pairs.extend(lcs_pair_gap(ls, rs, left, right, texts_l, texts_r))
    pairs = sorted(pairs)
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


def freq_common(a: str, b: str) -> int:
    """Order-free common-character count: sum(min(freq_a[c], freq_b[c])).

    This is `FUN_140e725f0` (decoded 2026-10-15): a 256-bucket histogram
    difference, NOT the longest common subsequence. See docs/11 §9.
    """
    from collections import Counter
    fa = Counter(a)
    common = 0
    for ch, nb in Counter(b).items():
        common += min(fa.get(ch, 0), nb)
    return common


def freq_score(a: str, b: str) -> int:
    """BC's decoded line-pair score (`FUN_140e726b0`, char-mode branch).

    common = freq_common(a, b); raw = common*3 - len(a) - len(b);
    raw<=0 -> clamp(raw*4-1, floor=-0x28); else (raw*25)//min(len(a),len(b)).
    Returns an int score (higher = closer); used only to RANK candidate
    pairs within a gap, so the exact floor only matters for tie behavior.
    """
    if not a or not b:
        total = len(a) + len(b)
        return max(total * -4 - 1, -0x28)
    common = freq_common(a, b)
    raw = common * 3 - len(a) - len(b)
    if raw <= 0:
        return max(raw * 4 - 1, -0x28)
    return (raw * 25) // min(len(a), len(b))


GAP_PENALTY = 0x14  # 20, decoded from FUN_140e74660's constant gap cost


def freqscore_pair_gap(ls, rs, left, right, texts_l, texts_r):
    """Real Needleman-Wunsch (as decoded in `FUN_140e74660`): fixed gap
    penalty 20 per skipped line, cell cost `freq_score` for a diagonal
    match/substitution. This is NOT the (score,count,-len) monotone-LCS
    framework the other variants use -- a pair only wins over two gaps
    when its freq_score beats -2*GAP_PENALTY, matching BC's real tradeoff.
    """
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    close_l = texts_l
    close_r = texts_r
    sc = [[freq_score(close_l[ls[i]], close_r[rs[j]]) for j in range(m)]
          for i in range(n)]
    NEG = -(1 << 30)
    f = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        f[i][0] = -GAP_PENALTY * i
    for j in range(m + 1):
        f[0][j] = -GAP_PENALTY * j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = f[i - 1][j - 1] + sc[i - 1][j - 1]
            up = f[i - 1][j] - GAP_PENALTY
            left_ = f[i][j - 1] - GAP_PENALTY
            f[i][j] = max(diag, up, left_)
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        diag = f[i - 1][j - 1] + sc[i - 1][j - 1]
        if f[i][j] == diag:
            pairs.append((ls[i - 1], rs[j - 1]))
            i -= 1
            j -= 1
        elif f[i][j] == f[i - 1][j] - GAP_PENALTY:
            i -= 1
        else:
            j -= 1
    return pairs


def freqscore_rows(left, right, texts_l, texts_r, *, anchor: str):
    """Full (status, ltid, rtid) rows under the decoded freq-intersection model."""
    if anchor == "raw":
        lk = [t if t else f"\x01L{i}" for i, t in enumerate(left)]
        rk = [t if t else f"\x01R{j}" for j, t in enumerate(right)]
    else:  # ci: folded important text (the m2.6 status quo)
        lk = [t if t else f"\x01L{i}" for i, t in enumerate(texts_l)]
        rk = [t if t else f"\x01R{j}" for j, t in enumerate(texts_r)]
    anchors = myers(lk, rk)
    pairs = list(anchors)
    bounds = [(-1, -1)] + list(anchors) + [(len(left), len(right))]
    for (pl, pr), (nl, nr) in zip(bounds, bounds[1:]):
        ls = list(range(pl + 1, nl))
        rs = list(range(pr + 1, nr))
        if ls and rs:
            pairs.extend(freqscore_pair_gap(ls, rs, left, right, texts_l, texts_r))
    pairs = sorted(pairs)
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


def lcs_pair_gap(ls, rs, left, right, texts_l, texts_r):
    n, m = len(ls), len(rs)
    if n == 0 or m == 0:
        return []
    close_l = texts_l
    close_r = texts_r
    sc = [[lcs_len(close_l[ls[i]], close_r[rs[j]]) for j in range(m)]
          for i in range(n)]
    f = [[(0, 0, 0)] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = f[i + 1][j] if _better(f[i + 1][j], f[i][j + 1]) else f[i][j + 1]
            prev = f[i + 1][j + 1]
            cand = (prev[0] + sc[i][j], prev[1] + 1, prev[2] + len(left[ls[i]]))
            if _better(cand, best):
                best = cand
            f[i][j] = best
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        prev = f[i + 1][j + 1]
        cand = (prev[0] + sc[i][j], prev[1] + 1, prev[2] + len(left[ls[i]]))
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


def main() -> int:
    variants = [
        ("incumbent", None),
        ("tok/raw/noweight", {"kind": "tok", "anchor": "raw", "weighted": False}),
        ("tok/raw/weighted", {"kind": "tok", "anchor": "raw", "weighted": True}),
        ("tok/ci/noweight", {"kind": "tok", "anchor": "ci", "weighted": False}),
        ("tok/ci/weighted", {"kind": "tok", "anchor": "ci", "weighted": True}),
        ("freq/raw", {"kind": "freq", "anchor": "raw"}),
        ("freq/ci", {"kind": "freq", "anchor": "ci"}),
    ]
    results: dict[str, dict] = {}
    failures: dict[str, list] = {}

    def grade(tag, model, cases, corpus):
        for c in cases:
            want = c["want"]
            got = model(c)
            r = results[tag]
            r[corpus] += 1
            if got == want:
                r[corpus + "_ok"] += 1
            elif len(failures[tag]) < 10:
                failures[tag].append((corpus, c["src"], want, got))

    recorded = collect()
    print(f"recorded observations: {len(recorded)}")
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

    def run_model(kind, c):
        if kind is None:
            return incumbent_rows(c["left"], c["right"], c["texts_l"], c["texts_r"])
        if kind["kind"] == "freq":
            return freqscore_rows(c["left"], c["right"], c["texts_l"], c["texts_r"],
                                  anchor=kind["anchor"])
        return model_rows(c["left"], c["right"], c["texts_l"], c["texts_r"],
                          anchor=kind["anchor"], weighted=kind["weighted"])

    for name, kind in variants:
        results[name] = {"rec": 0, "rec_ok": 0, "fz": 0, "fz_ok": 0}
        failures[name] = []
        for c in rec_cases:
            got = run_model(kind, c)
            results[name]["rec"] += 1
            if got == c["want"]:
                results[name]["rec_ok"] += 1
            elif len(failures[name]) < 10:
                failures[name].append(("rec", c["src"], c["want"], got))
        for c in fz_cases:
            got = run_model(kind, c)
            results[name]["fz"] += 1
            if got == c["want"]:
                results[name]["fz_ok"] += 1
            elif len(failures[name]) < 10:
                failures[name].append(("fuzz", c["src"], c["want"], got))

    for name, _ in variants:
        r = results[name]
        print(f"{name:20}  recorded {r['rec_ok']}/{r['rec']}  fuzz {r['fz_ok']}/{r['fz']}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REA / "product/verify/runs" / f"m55-model-lab-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "m55-model-lab.json").write_text(json.dumps(
        {"results": {str(k): v for k, v in results.items()},
         "failures": {str(k): f for k, f in failures.items()}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"raw: {out / 'm55-model-lab.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
