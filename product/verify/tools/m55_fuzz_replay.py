#!/usr/bin/env python3
"""Product fuzz replay (OFFLINE): product binary vs the STORED oracle XML.

The m54 probe's fixtures and BC oracle reports are already on disk
(`runs/m54-fuzz-20261014T170917Z/`), so the product side can be replayed
without running the Oracle at all: run `reacmp.exe` over each fixture pair,
parse its report, and compare the (status, ltid, rtid) rows with the stored
oracle XML. This is the cheap regression/gain metric for alignment changes.

    cd D:\\Rea\\product\\verify
    python tools/m55_fuzz_replay.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
FUZZ = REA / "product/verify/runs/m54-fuzz-20261014T170917Z"

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(\d+)"')
RTID_RE = re.compile(r'rtid="(\d+)"')


def rows_of(body: str):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2))
        rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not PRODUCT.exists():
        raise SystemExit(f"product binary missing: {PRODUCT}")
    fixtures = FUZZ / "fixtures"
    reports = FUZZ / "reports"
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="m55-replay-"))

    cases, ok, fails = [], 0, []
    for lp in sorted(fixtures.glob("*-L.*")):
        rp = pathlib.Path(str(lp).replace("-L.", "-R."))
        tag = lp.stem.split("-")[0]
        oracle = reports / f"{tag}.oracle.xml"
        if not oracle.exists():
            continue
        cases.append(tag)
        out = tmp / f"{tag}.product.xml"
        proc = subprocess.run([str(PRODUCT), str(lp), str(rp), str(out)],
                              capture_output=True, timeout=120)
        if proc.returncode != 0 or not out.exists():
            fails.append((tag, "run-failed", [], []))
            continue
        want = rows_of(oracle.read_bytes().decode("utf-8-sig", errors="replace"))
        got = rows_of(out.read_bytes().decode("utf-8-sig", errors="replace"))
        if got == want:
            ok += 1
        else:
            fails.append((tag, "mismatch", want, got))

    print(f"product fuzz replay: {ok}/{len(cases)}")
    for tag, why, want, got in fails[:14]:
        print(f"  {tag}: {why}")
        if why == "mismatch":
            print(f"     want: {want}")
            print(f"     got : {got}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = REA / "product/verify/runs" / f"m55-fuzz-replay-{stamp}"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "m55-fuzz-replay.json").write_text(json.dumps(
        {"ok": ok, "total": len(cases),
         "fails": [{"tag": t, "why": w, "want": wa, "got": g}
                   for t, w, wa, g in fails]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"raw: {outdir / 'm55-fuzz-replay.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
