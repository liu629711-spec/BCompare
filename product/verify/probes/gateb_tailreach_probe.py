#!/usr/bin/env python3
"""Tail-reach pinning probe: confirm the measured rule "no-run tail NW box
reaches cursor + 1999 on BOTH axes (width 2000), while the run-collection box
stays cursor + 1992 (job+0x98 = 1993)".

Three fixtures place the divergence at NEW cursor positions / clamps so the
constant cannot be an artifact of the original 137:

  TB-1  K20-off1990: K=20 short shared block (weight 20*32=640 > 500 -> run)
        but placed at off 1990 with A/B 6000-line bodies. iter2 cursor =
        (20, 2010): tail reach should clip left at 20+1999=2019 vs old model
        2012. Predicted: TB-1 matches WT=2000, mismatches W=1993.
  TB-2  K100-off1990-short: same as archived W-off1990 but N=3000 so the box
        right end is CLAMPED by the table end (2090+1999=4089 > 2999 ->
        clamped 2999). Tests the clamp interaction; predict WT=2000==oracle.
  TB-3  DBL-off1990-1990: two blocks: S0..S99 at off 1990 and T0..T99 at
        1990+2000. iter3 cursor after iter2 clip -> a THIRD iteration whose
        tail reach at a new origin decides whether the rule is
        "cursor-relative" (WT=2000) vs "absolute 2000" (would pair past).

Usage (serial):  cd D:\Rea\product\verify && python probes/gateb_tailreach_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(-?\d+)"')
RTID_RE = re.compile(r'rtid="(-?\d+)"')

def rows_of(body):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2)); rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("gateb-tailreach-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    def body(n):
        return [f"A{i}" for i in range(n)], [f"B{i}" for i in range(n)]

    cases = {}
    # TB-1: K=20 block at off 1990, N=6000
    A, B = body(6000)
    cases["TB1-k20-off1990"] = (
        [f"S{i}" for i in range(20)] + A,
        [f"B{i}" for i in range(1990)] + [f"S{i}" for i in range(20)] + B[1990:])
    # TB-2: K=100 block at off 1990, N=3000 (box clamp by table end)
    A, B = body(3000)
    cases["TB2-k100-off1990-n3000"] = (
        [f"S{i}" for i in range(100)] + A,
        [f"B{i}" for i in range(1990)] + [f"S{i}" for i in range(100)] + B[1990:])
    # TB-3: two blocks: S at 1990, T at 3990 (gap exactly 2000), N=8000
    A, B = body(8000)
    cases["TB3-dbl-1990-3990"] = (
        [f"S{i}" for i in range(100)] + A[:1900] + [f"T{i}" for i in range(100)] + A[1900:],
        [f"B{i}" for i in range(1990)] + [f"S{i}" for i in range(100)]
        + [f"B{i+1990}" for i in range(1900)] + [f"T{i}" for i in range(100)]
        + [f"B{i+3990}" for i in range(1990, 8000)])

    results = []
    for tag, (left, right) in cases.items():
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=600.0, script_text=lines[0])
        o_rows = rows_of(o_out.read_bytes().decode("utf-8-sig", errors="replace")) if run.report_exists else []
        rec = {"tag": tag, "rows": len(o_rows), "elapsed": run.elapsed_s, "exit": run.exit_code}
        results.append(rec)
        print(f"{tag}: rows={len(o_rows)} exit={run.exit_code} ({run.elapsed_s:.1f}s)")
    (run_dir / "tailreach.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
