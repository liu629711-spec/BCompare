#!/usr/bin/env python3
"""f0092 discriminant probe: does 140e726b0's cross-key score fold case?

Each fixture's left/right pair makes the candidate scorer models predict
DIFFERENT pairings (computed offline first, see extracted/_scratch/f0092/).
One serial Oracle pass resolves which model tracks BC.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\Rea\product\verify
    python probes/f0092_score_axis.py
"""
from __future__ import annotations

import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod
from harness import oracle as orc

# tag, left lines, right lines, per-model predictions (pairs as (ltext, rtext))
CASES = [
    ("P1-f0092",   ["delta", "value value alpha", "x node beta", "beta"],
     ["DELTA", "Node"],
     {"cs": "('beta', 'Node')", "ci": "('x node beta', 'Node')",
      "half": "('x node beta', 'Node')", "score=common": "('x node beta', 'Node')"}),
    ("P2-foldx",   ["NODEx", "beta", "alpha"], ["node", "x"],
     {"cs": "('NODEx', 'x')", "ci": "('NODEx', 'node')",
      "half": "('NODEx', 'node')", "score=common": "('NODEx', 'node')+"}),
    ("P3-letters", ["abcdef", "zzzzzz"], ["abcxyz"],
     {"cs": "('abcdef', 'abcxyz')", "ci": "('abcdef', 'abcxyz')",
      "half": "('abcdef', 'abcxyz')", "score=common": "both pair"}),
    ("P4-wordcap", ["x node beta", "beta"], ["Node"],
     {"cs": "('beta', 'Node')", "ci": "('x node beta', 'Node')",
      "half": "('x node beta', 'Node')", "score=common": "('x node beta', 'Node')"}),
    ("P5-allcaps", ["NODE X BETA", "BETA"], ["Node"],
     {"cs": "('BETA', 'Node')", "ci": "('NODE X BETA', 'Node')",
      "half": "('NODE X BETA', 'Node')?", "score=common": "('NODE X BETA', 'Node')"}),
    ("P7-f0057shape", ["alpha node item value", "delta data"],
     ["yy beta", "ITEM VALUE YY VALUE"],
     {"cs": "L2<->R1, orphans", "ci": "L1<->R2 + L2<->R1 diagonal",
      "half": "L2<->R1, orphans", "score=common": "diagonal pairs"}),
]

def pairing(body: str):
    out = []
    for m in re.finditer(r'<linecomp status="(\w+)">(.*?)</linecomp>', body, re.S):
        lt = re.search(r'ltid="(-?\d+)"', m.group(2))
        rt = re.search(r'rtid="(-?\d+)"', m.group(2))
        out.append((m.group(1), lt.group(1) if lt else "-", rt.group(1) if rt else "-"))
    return out

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("f0092-score-axis-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    rows = []
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)
    for tag, left, right, pred in CASES:
        lp = (fx / f"{tag}-L.txt").resolve()
        rp = (fx / f"{tag}-R.txt").resolve()
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")
        out = (run_dir / "reports" / f"{tag}.oracle.xml").resolve()
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), str(out),
                      timeout=180.0, script_text=lines[0])
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        got = pairing(body)
        rows.append((tag, got))
        print(f"{tag:16} exit={run.exit_code} pairing={got}")
        print(f"{'':16} predictions: {pred}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
