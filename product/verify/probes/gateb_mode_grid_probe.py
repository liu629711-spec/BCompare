#!/usr/bin/env python3
"""Boundary grid for the anchor->window gate. Working rule (22 axis points):
ANCHOR iff R <= 12 or L <= 4 (L/R = side line counts incl. golden 2 rows).
Test the predicted boundary cells:
  R=13 sweep over L:     (4,13) A? (5,13) W? (3,13) A?
  L=22 at R=13:         (22,13) W?   (R=12 was A)
  R=23 at L=4:          (4,23) A?
  interior re-check:    (10,13) W?  (6,13) W?  (4,12) A?  (5,12) A?
Usage (serial, Oracle exclusive):
  cd D:\Rea\product\verify && python probes\gateb_mode_grid_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

CASES = [(4,13),(5,13),(3,13),(22,13),(4,23),(10,13),(6,13),(4,12),(5,12)]

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
               datetime.now(timezone.utc).strftime("gateb-modegrid-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    results = []
    for pl, pr in CASES:
        left = [f"L{i}" for i in range(pl)] + ["a", "B"]
        right = ["b", "A"] + [f"R{i}" for i in range(pr)]
        tag = f"GR-{pl}x{pr}"
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=300.0, script_text=lines[0])
        body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        rows = rows_of(body)
        sim = [r for r in rows if r[0] == "similar"]
        mode = "ANCHOR" if sim else "WINDOW"
        rec = {"case": tag, "L": pl + 2, "R": pr + 2, "signature": mode,
               "sim": sim, "head": rows[:3]}
        results.append(rec)
        print(f"{tag:10} sides {pl+2:4}x{pr+2:4} -> {mode:7} sim={sim}")

    (run_dir / "modegrid.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'modegrid.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
