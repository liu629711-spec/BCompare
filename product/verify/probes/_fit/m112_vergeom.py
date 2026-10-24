#!/usr/bin/env python3
"""M112 geometry solver (OFFLINE): derive the version-report table layout from
the measured cells.

The registry channel (m111_colsolve.py) established the method: model each
column's start as a function of the content widths, then check the model
against EVERY archived cell rather than fitting one.

Model (registry's, carried over -- the two channels share the frame engine):
    lt = floor_name + max(name content incl. the box prefix)
    ld = lt + tw + 1
    mcol = ld + dwL + 1
    mlen = 0 (header only) / 1 ('=') / 2 (any of <> +- -+)
    rn = mcol + mlen + 1
    rt = rn + max(floor_name, name content right)
    rd = rt + tw + 1
    rule = rd + dwR

where floor_name = the display width of the 名称/值 LABEL itself (ZH 名称=4
display cols, 值=2; EN Name=4, Value=5) -- the registry finding was that the
floor is the LABEL width, not a constant.

This script recomputes it from the archived cells and prints the fit.
"""
from __future__ import annotations

import pathlib
import re
import sys

RUN = pathlib.Path(r"D:\Rea\product\verify\runs\m112-versurface-20261019T135402Z\reports")
RUNB = pathlib.Path(r"D:\Rea\product\verify\runs\m112b-verfields-20261019T153141Z\reports")


def disp(s: str) -> int:
    return sum(2 if ord(c) > 0x2e80 else 1 for c in s)


def load(tag: str, run=RUN):
    p = run / f"{tag}.out"
    if not p.exists():
        return None
    t = p.read_bytes().decode("utf-8-sig", errors="replace").splitlines()
    hi = next((i for i, l in enumerate(t) if l.count("名称") >= 2), None)
    if hi is None:
        return None
    return {
        "tag": tag,
        "header": t[hi],
        "rule": t[hi + 1],
        "rows": t[hi + 2:],
    }


def analyse(c):
    hdr = c["header"]
    # column starts in DISPLAY columns
    cols, w = [], 0
    for ch in hdr:
        cols.append((w, ch))
        w += disp(ch)
    name_pos = [x for x, ch in cols if ch == "名"]
    val_pos = [x for x, ch in cols if ch == "值"]
    # widest name / value content per side, from the body rows
    # a body row is: <left name><pad><left value><pad><marker><pad><right name><pad><right value>
    ln_max = rn_max = lv_max = rv_max = 0
    marker_seen = set()
    for r in c["rows"]:
        if set(r.strip()) <= {"-"}:
            continue
        # the marker is the first of  = <> +- -+  that is NOT inside a value
        for m in (" <> ", " = ", " +- ", " -+ "):
            if m in r:
                marker_seen.add(m.strip())
    return {
        "tag": c["tag"],
        "name_pos": name_pos,
        "val_pos": val_pos,
        "rule": len(c["rule"]),
        "markers": sorted(marker_seen),
        "header_len": len(hdr),
    }


def main() -> int:
    tags = ["V8-sbs-plain-both", "V7-sbs-plain-vs-pe", "V23-sbs-reg-pair",
            "V1-sbs-equal", "V6-sbs-ms", "W1-one-field"]
    for tag in tags:
        c = load(tag) or load(tag, RUNB)
        if c is None:
            print(f"{tag}: MISSING")
            continue
        a = analyse(c)
        print(f"{tag:<22} rule={a['rule']:>4} name@{a['name_pos']} val@{a['val_pos']} markers={a['markers']}")
        print(f"    header: {c['header']!r}")
        for r in c["rows"][:3]:
            print(f"    row   : {r!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
