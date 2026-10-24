#!/usr/bin/env python3
"""M6.0 table-channel probe: settle the *invocation form* and *report format*
of BC's Table Compare before writing any engine.

Help text (scripting_reference.html) is contradictory against our harness
practice, so every cell below is a measured observation:

  T1  data-report layout:side-by-side  with positional "%1" "%2"
  T2  data-report layout:xml           (does TABLE xml exist at all?)
  T3  data-report layout:summary
  T4  data-report layout:interleaved
  T5  text-report layout:xml           (is *.csv associated Text or Table?)
  T6  file-report layout:xml           (routing: file-report -> TABLE-REPORT?)
  T7  load "<L>" "<R>" + data-report layout:side-by-side output-to (session form)
  T8  file-report layout:side-by-side  (control for T6)

Fixture: 2 rows x 2 cols with one cell diff + one replaced row, so any
cell-level report is immediately readable.  Serial Oracle, one process at a
time, archive everything (exit, stdout tail, first 1200 chars of the report).

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m60_table_probe.py
"""
from __future__ import annotations
import json, pathlib, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

LEFT = "name,qty\napple,3\nbanana,5\n"
RIGHT = "name,qty\napple,4\ncherry,2\n"

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m60-table-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    lp = fx / "T-a.csv"; rp = fx / "T-b.csv"
    lp.write_text(LEFT, encoding="utf-8", newline="")
    rp.write_text(RIGHT, encoding="utf-8", newline="")
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    cells = [
        ("T1", ['data-report layout:side-by-side output-to:"%3" "%1" "%2"'], True),
        ("T2", ['data-report layout:xml output-to:"%3" "%1" "%2"'], True),
        ("T3", ['data-report layout:summary output-to:"%3" "%1" "%2"'], True),
        ("T4", ['data-report layout:interleaved output-to:"%3" "%1" "%2"'], True),
        ("T5", ['text-report layout:xml output-to:"%3" "%1" "%2"'], True),
        ("T6", ['file-report layout:xml output-to:"%3" "%1" "%2"'], True),
        ("T7", ['load "%1" "%2"', 'data-report layout:side-by-side output-to:"%3"'], False),
        ("T8", ['file-report layout:side-by-side output-to:"%3" "%1" "%2"'], True),
    ]
    results = []
    for tag, lines, positional in cells:
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        out = run_dir / "reports" / f"{tag}.out"
        args = (str(lp.resolve()), str(rp.resolve()), str(out.resolve())) if positional \
               else (str(lp.resolve()), str(rp.resolve()), str(out.resolve()))
        # T7: load consumes %1/%2 itself; output-to gets %3
        run = orc.run(inst.oracle_path, script, args[0], args[1], args[2],
                      timeout=120.0, script_text=lines[0])
        body = ""
        if out.exists():
            raw = out.read_bytes()
            body = raw.decode("utf-8-sig", errors="replace")
        rec = {"tag": tag, "lines": lines, "exit": run.exit_code,
               "elapsed_s": round(run.elapsed_s, 2),
               "report_bytes": len(body.encode("utf-8")),
               "report_head": body[:1200]}
        results.append(rec)
        print(f"{tag}: exit={run.exit_code} bytes={rec['report_bytes']:7} "
              f"({run.elapsed_s:5.2f}s) head={body[:64]!r}")

    (run_dir / "m60-table-probe.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
