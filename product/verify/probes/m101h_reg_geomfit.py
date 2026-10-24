#!/usr/bin/env python3
"""M101h: offline geometry extraction from the m101e/f/g archives.

Builds the column model WITHOUT new Oracle calls: for every sbs table row,
derives (left-field-width, marker start, right-field start, box prefix
structure) from exact character indices -- and cross-checks against the
column positions computed from the HEADER line (which encodes the field
widths). Prints a table the model can be fit against, by ints only.

Key idea: the header '名称 ... 类型 ... 数据 ... <gap> 名称 ...' gives the
right-side column start index. Every row's right field must align to it.
Marker tokens (=, <>, +-, -+) sit immediately before the right field.
"""
from __future__ import annotations
import json, glob, pathlib, re

RUNS = pathlib.Path(r"D:\Rea\product\verify\runs")

def header_metrics(line: str) -> dict:
    """From a header line compute column widths.
    zh header: 名称 {w1+2}? -- instead: find occurrences of the labels.
    The layout is: NAME_COL(name_w) SEP TYPE_COL SEP DATA_COL GAP...
    Simpler: positions of '名称'(left/right), '类型' x2, '数据' x2."""
    hits = {}
    for tok in ("名称", "类型", "数据"):
        idxs = []
        start = 0
        while True:
            j = line.find(tok, start)
            if j == -1:
                break
            idxs.append(j)
            start = j + len(tok)
        hits[tok] = idxs
    return hits


def analyze(run_pat: str):
    for f in sorted(glob.glob(str(RUNS / run_pat / "m101*-summary*.json"))):
        data = json.load(open(f, encoding="utf-8"))
        for c in data:
            if not c["tag"].endswith("-sid") and "sbs" not in c["tag"]:
                continue
            lines = c["lines"]
            hdr = next((ln for ln in lines if ln.startswith("名称")), None)
            if hdr is None:
                continue
            h = header_metrics(hdr)
            right_name = h["名称"][1] if len(h["名称"]) > 1 else None
            if right_name is None:
                continue
            print(f"### {pathlib.Path(f).parent.name[:28]} {c['tag']}")
            print(f"    header: name@{h['名称'][0]} type@{h['类型'][0]} "
                  f"data@{h['数据'][0]} | Rname@{right_name} "
                  f"Rtype@{h['类型'][1]} Rdata@{h['数据'][1]}")
            in_body = False
            for i, ln in enumerate(lines):
                if ln.startswith(("已产生", "左边文件", "右边文件", "模式",
                                  "注册", "左边错误", "右边错误")):
                    continue
                if set(ln) == {"-"}:
                    print(f"    [{i:2}] RULE len={len(ln)}")
                    in_body = not in_body
                    continue
                if ln.startswith("名称"):
                    continue
                # slice by model: [left name .. right name ..]
                # classify prefix box chars at col 0..: '+' | runs
                prefix = ""
                j = 0
                while j < len(ln) and ln[j] in "+|":
                    prefix += ln[j]
                    j += 1
                # marker search before right_name
                seg_mid = ln[:right_name]
                m = None
                for tok in ("<>", "+-", "-+", " = "):
                    k = seg_mid.rfind(tok)
                    if k != -1:
                        m = (tok, k)
                        break
                print(f"    [{i:2}] prefix={prefix!r} marker={m} "
                      f"len={len(ln)} rightfield={ln[right_name:]!r} "
                      f"leftpart={ln[:j]!r}/{ln[j:right_name]!r}")


if __name__ == "__main__":
    for pat in ("m101e-*", "m101f-*", "m101g-*"):
        analyze(pat)
