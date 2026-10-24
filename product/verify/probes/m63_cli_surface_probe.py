#!/usr/bin/env python3
"""M6.3 CLI-surface probe: pin the exact exit codes / report shapes of the
data-report command family so the product's accept/refuse surface matches
observation, not inference.  Raw subprocess (not harness.run) because these
cases deliberately have 0/3 file arguments.

  X1  `table-report layout:...`          -- is table-report an accepted alias?
  X2  `data-report` with no layout arg   -- which exit? (105 arg vs 106 cmd)
  X3  `data-report layout:bogus`         -- unknown layout code
  X4  `data-report layout:summary title:X` -- does title render into the header?
  X5  `data-report layout:side-by-side` with ZERO comparison files
  X6  three comparison files
  X7  missing file path
  X8  output-options:csv (does the table channel accept it?)

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m63_cli_surface_probe.py
"""
from __future__ import annotations
import json, pathlib, subprocess, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

CASES = [
    # tag, script lines, extra file args (full argv after @script)
    ("X1-alias",   ['table-report layout:side-by-side output-to:"%3" "%1" "%2"'], 2),
    ("X2-nolayout", ['data-report output-to:"%3" "%1" "%2"'], 2),
    ("X3-bogus",   ['data-report layout:bogus output-to:"%3" "%1" "%2"'], 2),
    ("X4-title",   ['data-report layout:summary title:"MyTitle" output-to:"%3" "%1" "%2"'], 2),
    ("X5-nofiles", ['data-report layout:side-by-side output-to:"%3"'], 0),
    ("X6-three",   ['data-report layout:summary output-to:"%3" "%1" "%2" "%1"'], 3),
    ("X7-missing", ['data-report layout:summary output-to:"%3" "Z:\\nope.csv" "Z:\\nope2.csv"'], 0),
    ("X8-opts",    ['data-report layout:side-by-side output-options:csv output-to:"%3" "%1" "%2"'], 2),
]

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m63-clisurface-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    lp = fx / "X-L.csv"; rp = fx / "X-R.csv"
    lp.write_text("k,1\n", encoding="utf-8", newline="")
    rp.write_text("k,2\n", encoding="utf-8", newline="")
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, lines, nfiles in CASES:
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        out = run_dir / "reports" / f"{tag}.out"
        if out.exists():
            out.unlink()
        files = [str(lp.resolve()), str(rp.resolve()), str(lp.resolve())][:nfiles]
        argv = [str(inst.oracle_path), "/silent", f"@{script}"] + files + [str(out.resolve())]
        proc = subprocess.run(argv, cwd=str(pathlib.Path(inst.oracle_path).parent),
                              capture_output=True, timeout=120)
        body = out.read_text(encoding="utf-8-sig", errors="replace") if out.exists() else ""
        rec = {"tag": tag, "lines": lines, "exit": proc.returncode,
               "stdout": proc.stdout.decode("utf-8", errors="replace")[:300],
               "stderr": proc.stderr.decode("utf-8", errors="replace")[:300],
               "report_bytes": len(body.encode("utf-8")),
               "report_head": body[:500]}
        results.append(rec)
        print(f"{tag:11} exit={proc.returncode:4} bytes={rec['report_bytes']:6} "
              f"head={body[:70]!r}")
        # residue check every call
        r = subprocess.run(["tasklist"], capture_output=True, text=True)
        if "BComp" in r.stdout or "BCompare" in r.stdout:
            print("  RESIDUE DETECTED -- killing")
            subprocess.run(["taskkill", "/F", "/IM", "BComp.com"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "BCompare.exe"], capture_output=True)

    (run_dir / "m63-clisurface.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
