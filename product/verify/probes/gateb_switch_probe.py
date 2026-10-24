#!/usr/bin/env python3
"""Strategy-switch ladder: locate the size threshold where BC's CLI switches
from the anchor hybrid (140e74b60: pairs a far unique block) to the banded
window engine (140e73b40: unpaired past reach 1992).

Shape (same discriminator as D1): left = A0..A(n-1) + S0..S99,
right = S0..S99 + B0..B(n-1). Distractor distance == n. anchor mode pairs the
S-block (unique keys, order-consistent) regardless of n; banded mode pairs it
only while n <= 1992. Also re-verifies the tiny golden case (a,B vs b,A)
through this CLI harness.

Usage (serial, Oracle exclusive):
  cd D:\Rea\product\verify && python probes\gateb_switch_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

K = 100
NS = [1000, 2000, 2500, 3000, 3500, 4000, 4500, 6000]

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
               datetime.now(timezone.utc).strftime("gateb-switch-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    results = []

    # case 0: the tiny golden (disambig/case-swap-align) through this harness
    lp = fx / "tiny-L.txt"; rp = fx / "tiny-R.txt"
    lp.write_text("a\nB\n", encoding="utf-8", newline="")
    rp.write_text("b\nA\n", encoding="utf-8", newline="")
    o_out = run_dir / "reports" / "tiny.oracle.xml"
    run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                  str(o_out.resolve()), timeout=120.0, script_text=lines[0])
    body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
    tiny = [(s, l, r) for s, l, r in rows_of(body)]
    print(f"tiny (a,B vs b,A): {tiny}")
    results.append({"case": "tiny", "rows": tiny})

    for nn in NS:
        left = [f"A{i}" for i in range(nn)] + [f"S{i}" for i in range(K)]
        right = [f"S{i}" for i in range(K)] + [f"B{i}" for i in range(nn)]
        tag = f"SW-n{nn}"
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=300.0, script_text=lines[0])
        body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        rows = rows_of(body)
        # S-block pairs: left ids nn+1..nn+K (1-based), right ids 1..K
        sp = sum(1 for s, l, r in rows
                 if l and r and nn + 1 <= l <= nn + K and 1 <= r <= K)
        rec = {"case": tag, "n": nn, "min_side": nn + K, "oracle_s": run.elapsed_s,
               "block_pairs": sp,
               "mode": "ANCHOR (paired)" if sp == K else
                       "WINDOW (unpaired)" if sp == 0 else f"PARTIAL {sp}"}
        results.append(rec)
        print(f"n={nn:5} min_side={nn+K:5} {run.elapsed_s:6.2f}s block_pairs={sp:4} -> {rec['mode']}")

    (run_dir / "switch.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'switch.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
