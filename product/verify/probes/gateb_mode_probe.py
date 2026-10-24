#!/usr/bin/env python3
"""Mode discriminator sweep: does BC's CLI switch from the anchor hybrid
(140e74b60: LIS over unique-unique pairs) to the banded window engine
(140e73b40) as the file grows?

Discriminator = the 2x2 golden shape `a,B` vs `b,A` (disambig/case-swap-align):
  * anchor hybrid -> pair B~b (keys cross), orphans a and A:
    [leftorphan a] [similar B,b] [rightorphan A]
  * window engine -> no run (weight 31 < 500 gate), NW over the box pairs
    positionally at -9/-9 > orphans: [different a,b] [different B,A]
Both predictions are stable when the shape is padded with uniquely-keyed lines,
so sweeping the pad size localizes the strategy switch (if any).

Usage (serial, Oracle exclusive):
  cd D:\Rea\product\verify && python probes\gateb_mode_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

PADS = [0, 500, 1000, 1500, 1900, 1985, 1990, 1995, 2000, 2100, 2500, 3000, 4500]

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
               datetime.now(timezone.utc).strftime("gateb-mode-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    results = []
    for pad in PADS:
        left = [f"L{i}" for i in range(pad)] + ["a", "B"]
        right = ["b", "A"] + [f"R{i}" for i in range(pad)]
        tag = f"MD-pad{pad}"
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=300.0, script_text=lines[0])
        body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        rows = rows_of(body)
        # the golden pair: L id pad+2 ("B") with R id 1 ("b") as `similar`
        sim = [r for r in rows if r[0] == "similar" and r[1] == pad + 2 and r[2] == 1]
        # else: window signature = L pad+1 ("a") paired positionally with R1
        pos = [r for r in rows if r[0] == "different" and r[1] == pad + 1 and r[2] == 1]
        mode = "ANCHOR" if sim else ("WINDOW" if pos else "OTHER")
        rec = {"pad": pad, "sides": pad + 2, "oracle_s": run.elapsed_s,
               "signature": mode,
               "window_head": rows[:4]}
        results.append(rec)
        print(f"pad={pad:5} sides={pad+2:5} {run.elapsed_s:5.2f}s -> {mode}"
              f"   first rows: {rows[:3]}")

    (run_dir / "mode.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'mode.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
