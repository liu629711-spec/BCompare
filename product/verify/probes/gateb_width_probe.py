#!/usr/bin/env python3
"""Gate B width probe: pin the window W of 140e73b40 behaviorally.

Every case is ONE interval (greedy scan breaks at (0,0): L0='S1' vs R0='B1'),
with a shared 100-line block whose distance-from-diagonal is `off`:

    L = S1..S100, A1..A10000
    R = B1..Boff, S1..S100, Boff+1..B10000

max(n,m)=10100 > 5000 forces the window path; left duplicates = 0. The NW
filler would always pair the block; the window engine can only see it while
the offset stays inside the window. The first offset BC leaves UNPAIRED pins
W. Product (full NW) is expected to pair every case -- any oracle divergence
is a behavioral (not just performance) gap for §21.6.

Usage (serial):  cd D:\Rea\product\verify && python probes/gateb_width_probe.py
"""
from __future__ import annotations
import json, pathlib, re, subprocess, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
OFFSETS = [1000, 3000, 4000, 4096, 4097, 5000, 6000, 9000]
N = 10000
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
               datetime.now(timezone.utc).strftime("gateb-width-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")
    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    results = []
    for off in OFFSETS:
        left = [f"S{i}" for i in range(K)] + [f"A{i}" for i in range(N)]
        right = ([f"B{i}" for i in range(off)] + [f"S{i}" for i in range(K)]
                 + [f"B{i}" for i in range(off, N)])
        tag = f"W-off{off}"
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")

        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=300.0, script_text=lines[0])
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        o_rows = rows_of(o_body)
        # is the shared block paired in the oracle?
        o_sp = [(l, r) for s, l, r in o_rows if l and r and 1 <= l <= K and off + 1 <= r <= off + K]

        p_out = run_dir / "reports" / f"{tag}.product.xml"
        subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)], capture_output=True, timeout=600)
        p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace") if p_out.exists() else ""
        p_rows = rows_of(p_body)
        p_sp = [(l, r) for s, l, r in p_rows if l and r and 1 <= l <= K and off + 1 <= r <= off + K]

        rec = {"offset": off, "oracle_s": run.elapsed_s,
               "oracle_shared_pairs": len(o_sp), "product_shared_pairs": len(p_sp),
               "rows_same": o_rows == p_rows}
        results.append(rec)
        print(f"off={off:6} oracle {run.elapsed_s:6.2f}s shared_pairs={len(o_sp):4} "
              f"| product shared={len(p_sp):4} | rows {'SAME' if o_rows == p_rows else 'DIFF'}")

    (run_dir / "gateb-width.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'gateb-width.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
