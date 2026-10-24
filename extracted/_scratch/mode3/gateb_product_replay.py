#!/usr/bin/env python3
"""Replay the PRODUCT binary over every archived gateb fixture and compare its
rows against the stored oracle XML. Offline; no Oracle calls.

Usage: python gateb_product_replay.py [--limit N] [--only TAG ...]
"""
from __future__ import annotations
import argparse, json, pathlib, re, subprocess, tempfile
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
RUNS = REA / "product" / "verify" / "runs"

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(-?\d+)"')
RTID_RE = re.compile(r'rtid="(-?\d+)"')

def rows_of_bytes(b: bytes):
    body = b.decode("utf-8-sig", errors="replace")
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2)); rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="gateb-prod-replay-"))
    cases = []
    for d in sorted(RUNS.glob("gateb-*")):
        fx = d / "fixtures"
        if not fx.exists():
            continue
        for ox in sorted((d / "reports").glob("*.oracle.xml")):
            tag = ox.name[: -len(".oracle.xml")]
            lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
            if lp.exists() and rp.exists():
                cases.append((d.name, tag, lp, rp, ox))
    if args.only:
        cases = [c for c in cases if c[1] in args.only]
    if args.limit:
        cases = cases[: args.limit]

    ok, fails = 0, []
    for run, tag, lp, rp, ox in cases:
        out = tmp / f"{tag}.product.xml"
        try:
            proc = subprocess.run([str(PRODUCT), str(lp), str(rp), str(out)],
                                  capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            fails.append({"run": run, "tag": tag, "why": "timeout"})
            continue
        if proc.returncode != 0 or not out.exists():
            fails.append({"run": run, "tag": tag, "why": f"exit {proc.returncode}"})
            continue
        want = rows_of_bytes(ox.read_bytes())
        got = rows_of_bytes(out.read_bytes())
        if got == want:
            ok += 1
        else:
            fi = next((k for k in range(max(len(want), len(got)))
                       if (want[k] if k < len(want) else None) != (got[k] if k < len(got) else None)), None)
            fails.append({"run": run, "tag": tag, "why": "mismatch",
                          "len_got": len(got), "len_want": len(want), "idx": fi,
                          "ctx_want": [list(x) for x in want[max(0,(fi or 0)-2):(fi or 0)+4]],
                          "ctx_got": [list(x) for x in got[max(0,(fi or 0)-2):(fi or 0)+4]]})

    print(f"product gateb replay: {ok}/{len(cases)}")
    for f in fails:
        print(f"  {f['tag']:16} {f['why']:9} got={f.get('len_got')} want={f.get('len_want')} idx={f.get('idx')}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = RUNS / f"gateb-product-replay-{stamp}"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "replay.json").write_text(json.dumps(
        {"ok": ok, "total": len(cases), "fails": fails}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"raw: {outdir / 'replay.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
