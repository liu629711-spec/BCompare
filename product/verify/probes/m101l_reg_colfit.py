#!/usr/bin/env python3
"""M101l offline column fit: extract (name_w, type_w, data_w) from every
archived registry sbs report and fit the exact field-width formulas.

Model to fit:
  row = LFIELD + '  ' + MARKER2 + ' ' + RFIELD (rstrip)
  LFIELD = name_col + ' ' + type_col + ' ' + data_col  (all space-padded)
  question: how do name_col/type_col/data_col widths derive from the rows?
  header row: 名称/类型/数据 labels padded the same way?
  rule row: '=' runs -- width = ? of full row?
Print per-report: max lens of extracted fields vs observed paddings.
"""
from __future__ import annotations
import json, glob, re, pathlib

RUNS = pathlib.Path(r"D:\Rea\product\verify\runs")
SKIP = ("注册", "已产生", "模式", "左边文件", "右边文件", "左边错误", "右边错误",
        "Registry", "Produced", "Mode:", "Left file", "Right file",
        "Left error", "Right error", "名称", "Name ")


def parse_row(ln: str):
    """Try marker-based split for table rows."""
    for m in ("  = ", "  <> ", "  +-", "  -+ "):
        i = ln.find(m)
        if i != -1:
            left = ln[:i]
            marker = m.strip()
            right = ln[i + len(m):] if m != "  +-" else ""
            if m == "  +-" or m == "  -+":
                # +- row: right part after +- is empty usually; -+ row: right after
                if m == "  -+":
                    left = ln[:i]
                    right = ln[i + 4:]
                    return None if False else (left, "-+", right)
                return (left, "+-", None)
            return (left, marker, right)
    return None


def split_fields(seg: str):
    """left field: name | type | data -- type token is REG_* / 0xNN / bare."""
    # name = leading up to first double-space? no: fields separated by single
    # space with padding spaces trailing. Identify: name runs to first space
    # run >= 1 then type token matching [A-Z0-9_]+ or 0x[0-9A-F]+ then rest.
    m = re.match(r"^(.*?\S)\s\s+(?=\S)", seg)
    # more robust: find the type token by pattern
    tm = re.search(r"\b(REG_[A-Z_]+|0x[0-9A-F]{2}|\bREG_SZ)\b", seg)
    return None


def main():
    rows_seen = 0
    for f in sorted(glob.glob(str(RUNS / "m101*-summary*.json"))):
        data = json.load(open(f, encoding="utf-8"))
        for c in data:
            lines = c.get("lines", [])
            tbl = [ln for ln in lines
                   if ln and not any(ln.startswith(s) for s in SKIP)
                   and set(ln) != {"-"} and not ln.startswith("Name")
                   and "Type" not in ln[:12]]
            rule = [ln for ln in lines if set(ln) == {"-"}]
            if not tbl:
                continue
            print("###", pathlib.Path(f).parent.name[:30], c["tag"])
            for ln in tbl:
                r = parse_row(ln)
                if r is None:
                    print("   RAW  ", repr(ln), "len", len(ln))
                    continue
            for ln in tbl:
                print("   ", repr(ln), "len", len(ln))
            if rule:
                print("   RULE len", len(rule[0]))
            rows_seen += len(tbl)
    print("rows:", rows_seen)


if __name__ == "__main__":
    main()
