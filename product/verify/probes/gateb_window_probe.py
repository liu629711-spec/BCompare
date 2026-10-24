#!/usr/bin/env python3
"""Gate B probe: 140e74b60 delegates an interval to the window engine
(140e73b40) when left-duplicates >= 1001 OR max(n,m) > 5000; otherwise the
NW filler (140e74660) allocates the full matrix. Each case comes in a
just-inside / just-outside pair with the SAME logical content, so the XML
row structure and the wall-clock scaling localize the gate and its behavior.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\Rea\product\verify
    python probes/gateb_window_probe.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod
from harness import oracle as orc

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"


def disjoint(n: int) -> tuple[list[str], list[str]]:
    return ([f"L{i}" for i in range(n)], [f"R{i}" for i in range(n)])


def rotated_dup(k: int) -> tuple[list[str], list[str]]:
    """2k lines per side; every key appears exactly twice (unique pairs
    empty). Left order 0,1,..k-1,0,1,..k-1; right = rotate left by one.
    Left duplicates = k: k >= 1001 forces the window even under the size gate."""
    left = [f"v{i}" for i in range(k)] + [f"v{i}" for i in range(k)]
    right = left[1:] + left[:1]
    return left, right


CASES = [
    # size gate: NW side vs window side on identical shape
    ("S1-disjoint-4999", disjoint(4999), "NW: max<=5000, dups=0"),
    ("S2-disjoint-5001", disjoint(5001), "window: max>5000"),
    ("S3-disjoint-12000", disjoint(12000), "window: 2.4x size; timing scaling"),
    # duplicate gate under the size gate: k=1000 NW vs k=1001 window
    ("S4-dup-2000", rotated_dup(1000), "NW: dups=1000<1001"),
    ("S5-dup-2002", rotated_dup(1001), "window: dups=1001>=1001"),
    # rotated duplicate multiset at 5000/5002 (both gates combined)
    ("S6-dup-5000", rotated_dup(2500), "NW side"),
    ("S7-dup-5002", rotated_dup(2501), "window side"),
]

ROW_RE = re.compile(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(-?\d+)"')
RTID_RE = re.compile(r'rtid="(-?\d+)"')


def rows_of(body: str):
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2))
        rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), int(lt.group(1)) if lt else None,
                    int(rt.group(1)) if rt else None))
    return out


def diff_note(a: list, b: list) -> str:
    if a == b:
        return "identical"
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return f"first diff at row {i}: oracle-side-A={x} vs B={y} (len {len(a)} vs {len(b)})"
    return f"prefix-equal, lengths {len(a)} vs {len(b)}"


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("gateb-window-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
    script = orc.write_script(run_dir / "reports" / "pair.bcs", lines)

    results = []
    for tag, (left, right), note in CASES:
        lp = fx / f"{tag}-L.txt"
        rp = fx / f"{tag}-R.txt"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")

        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(o_out.resolve()), timeout=300.0, script_text=lines[0])
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        o_rows = rows_of(o_body)

        p_out = run_dir / "reports" / f"{tag}.product.xml"
        import subprocess
        proc = subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)],
                              capture_output=True, timeout=300)
        p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace") if p_out.exists() else ""
        p_rows = rows_of(p_body)

        rec = {"tag": tag, "note": note, "n": len(left),
               "oracle_exit": run.exit_code, "oracle_s": run.elapsed_s,
               "oracle_bytes": run.report_bytes,
               "product_exit": proc.returncode,
               "oracle_rows": len(o_rows), "product_rows": len(p_rows),
               "same_as_product": o_rows == p_rows,
               "diff": diff_note(o_rows, p_rows) if o_rows != p_rows else ""}
        results.append(rec)
        print(f"{tag:20} oracle {run.elapsed_s:8.3f}s exit={run.exit_code} "
              f"rows={len(o_rows):6} | product exit={proc.returncode} rows={len(p_rows):6} "
              f"{'SAME' if o_rows == p_rows else 'DIFF'}")
        if o_rows != p_rows:
            print(f"    {rec['diff']}")
        # structural fingerprint of the oracle rows
        if o_rows:
            paired = sum(1 for s, l, r in o_rows if l is not None and r is not None)
            diag = sum(1 for s, l, r in o_rows if l is not None and r is not None and l == r)
            off = sum(1 for s, l, r in o_rows if l is not None and r is not None and l == r + 1)
            print(f"    fingerprint: paired={paired} ltid==rtid:{diag} ltid==rtid+1:{off}")

    (run_dir / "gateb-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    print(f"\nraw: {run_dir / 'gateb-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
