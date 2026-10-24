#!/usr/bin/env python3
"""Which axis does the anchor->window switch gate on?
Established (gateb-mode / -modefine / -modebisect 20261016T10*):
  sides 12x12 (pad 10) -> ANCHOR (similar row present, naive intervals)
  sides 13x13 (pad 11) -> WINDOW  (rightorphan head, positional middle,
                                   leftorphan tail)
This probe holds the golden 2x2 shape and varies sides asymmetrically:
  (12,13)/(13,12) total 25 vs max 13   -> max-axis: WINDOW, total(>24): WINDOW
  (12,100)/(100,12)                     -> min-axis gate => ANCHOR
  (2,13)/(13,2),(2,100)/(100,2)         -> min=2/13, max=13/2, total 15/102
  (11,14)/(14,11)                       -> max 14, total 25
Anchor signature: any `similar` row (a~A or B~b paired by case-swapped key).
Window signature: no similar rows; b,A head-orphans.

Usage (serial, Oracle exclusive):
  cd D:\Rea\product\verify && python probes\gateb_mode_axis_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

CASES = [(12,12),(13,13),(12,13),(13,12),(12,100),(100,12),
         (2,13),(13,2),(2,100),(100,2),(11,14),(14,11),(10,20),(20,10)]

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
               datetime.now(timezone.utc).strftime("gateb-modeaxis-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    results = []
    for pl, pr in CASES:
        left = [f"L{i}" for i in range(pl)] + ["a", "B"]
        right = ["b", "A"] + [f"R{i}" for i in range(pr)]
        tag = f"AX-{pl}x{pr}"
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
        rec = {"case": tag, "pl": pl + 2, "pr": pr + 2, "signature": mode,
               "sim": sim, "head": rows[:3], "total_s": run.elapsed_s}
        results.append(rec)
        print(f"{tag:10} sides {pl+2:4}x{pr+2:4} -> {mode:7} sim={sim} head={rows[:3]}")

    (run_dir / "modeaxis.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'modeaxis.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
