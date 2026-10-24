#!/usr/bin/env python3
"""Fine-grained mode-switch sweep between pad=0 (ANCHOR, proven by
gateb-mode-20261016T095915Z) and pad=500 (WINDOW, same run).

Same discriminator as gateb_mode_probe.py: 2x2 golden `a,B` vs `b,A` padded
with unique L{i}/R{i} lines. Anchor signature: B~b emerges as `similar`.
Window signature: b,A right-orphans at the head, a,B left-orphans at the tail,
every other row a positional `different` (L{i} ~ R{i+2}).

Usage (serial, Oracle exclusive):
  cd D:\Rea\product\verify && python probes\gateb_mode_fine_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

PADS = [2, 5, 10, 25, 50, 100, 150, 200, 250, 300, 350, 400, 450, 480, 490, 499]

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
               datetime.now(timezone.utc).strftime("gateb-modefine-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    results = []
    for pad in PADS:
        left = [f"L{i}" for i in range(pad)] + ["a", "B"]
        right = ["b", "A"] + [f"R{i}" for i in range(pad)]
        tag = f"MF-pad{pad}"
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=300.0, script_text=lines[0])
        body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        rows = rows_of(body)
        sim = [r for r in rows if r[0] == "similar" and r[1] == pad + 2 and r[2] == 1]
        win = ([r for r in rows if r[0] == "rightorphan" and r[2] in (1, 2)]
               and [r for r in rows if r[0] == "leftorphan" and r[1] in (pad + 1, pad + 2)]
               and not sim)
        mode = "ANCHOR" if sim else ("WINDOW" if win else "OTHER")
        rec = {"pad": pad, "sides": pad + 2, "oracle_s": run.elapsed_s,
               "signature": mode, "head": rows[:4], "tail": rows[-4:]}
        results.append(rec)
        print(f"pad={pad:5} sides={pad+2:5} {run.elapsed_s:5.2f}s -> {mode}"
              f"   head={rows[:3]}")

    (run_dir / "modefine.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'modefine.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
