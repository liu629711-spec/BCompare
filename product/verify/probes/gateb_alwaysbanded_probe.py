#!/usr/bin/env python3
"""Discriminate the CLI align architecture: always-banded vs gated-banded.

Background (docs/11 §24.2): the strategy descriptor `0x140e71510` has interval
slot = `140e73b40` (pure window engine, no anchors/no gate B), while
`0x140e718c0` has slot = `140e75a70` -> `140e74b60` (anchors + gate-B + NW).
The archived width probes prove the CLI bands (off>=1993 unpaired), which under
`140e74b60` would require the gate `dups>=1001 OR min>5000` to fire -- but the
off=1989 fixture has min side 10100 (>5000) and off=1000 as well, so all
existing fixtures are consistent with BOTH readings.

D1 is the discriminator: shared block 100 lines, left block starts at row 4501,
right block at row 1. min(n,m) = 4500 < 5000, left duplicate keys = 0.
  - gated-banded (`140e74b60`, gate closed): the handler sees unique-unique
    anchor pairs -> block PAIRED (NW/anchors span the whole interval).
  - always-banded (`140e73b40` directly): the block's left copy (L>=4501) and
    right copy (R<=100) never share one window box (reach 1993) -> UNPAIRED.

Usage (serial, Oracle exclusive):
  cd D:\Rea\product\verify && python probes\gateb_alwaysbanded_probe.py
"""
from __future__ import annotations
import json, pathlib, re, subprocess, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
N = 4500
K = 100

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
               datetime.now(timezone.utc).strftime("gateb-alwaysbanded-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    left = [f"A{i}" for i in range(N)] + [f"S{i}" for i in range(K)]
    right = [f"S{i}" for i in range(K)] + [f"B{i}" for i in range(N - K)]
    lp = fx / "D1-L.txt"; rp = fx / "D1-R.txt"
    lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
    rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")

    o_out = run_dir / "reports" / "D1.oracle.xml"
    run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                  str(o_out.resolve()), timeout=300.0, script_text=lines[0])
    o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
    o_rows = rows_of(o_body)
    paired = sum(1 for s, l, r in o_rows
                 if l and r and N + 1 <= l <= N + K and 1 <= r <= K)

    rec = {"min_side": min(len(left), len(right)), "oracle_s": run.elapsed_s,
           "oracle_block_pairs": paired,
           "verdict": "ALWAYS-BANDED (block unpaired)" if paired == 0
                      else "GATED-BANDED (gate closed, handler paired it)"}
    print(f"D1: oracle block pairs = {paired} -> {rec['verdict']}")
    (run_dir / "verdict.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(f"raw: {run_dir / 'verdict.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
