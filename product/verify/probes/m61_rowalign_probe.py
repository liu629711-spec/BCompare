#!/usr/bin/env python3
"""M6.1 row-alignment discriminators for the table channel.

Central hypothesis (from T1 in m60-table-probe): BC's table row alignment is
the *text line alignment applied to raw CSV lines*, then cell-wise diff within
aligned pairs decides `=`/`<>`/orphan marks.  Each fixture below discriminates
a facet:

  T10 pure middle insert (orphan mark?)         T11 pure middle delete
  T12 head-identical + tail row swap            T13 positional vs content
  T14 exact duplicate rows shifted              T15 similar-ish rows (closeness)
  T17 semicolon file (format routing)           T18 column count change
  T19 header vs data-row alignment              T20 quoted comma cell diff
  T21 quoted cell with EMBEDDED NEWLINE (row vs line model!)

Serial, Job-Object contained; both side-by-side and interleaved per fixture
(the interleaved numbering shows whether a quoted multi-line cell counts as
ONE row).  Archived verbatim -- this batch is the design input for the engine.

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m61_rowalign_probe.py
"""
from __future__ import annotations
import json, pathlib, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

FIXTURES = {
    # tag: (left, right)
    "T10-ins":   ("a,1\nb,2\nd,3\n",       "a,1\nb,2\nc,2.5\nd,3\n"),
    "T11-del":   ("a,1\nb,2\nc,3\nd,4\n",  "a,1\nb,2\nd,4\n"),
    "T12-swap":  ("x,1\ny,2\n",            "y,2\nx,1\n"),
    "T13-cont":  ("k1,a\nk2,b\nk3,c\nk4,d\n", "k1,a\nk2,b\nk4,d\nk3,c\n"),
    "T14-dup":   ("k,v\nr,1\nr,1\nr,1\nz,9\n", "k,v\nr,1\nr,1\nz,9\n"),
    "T15-close": ("id,1000\n",             "id,1001\n"),
    "T17-semi":  ("a;b;c\n",               "a;d;c\n"),
    "T18-cols":  ("a,1\n",                 "a,1,x\n"),
    "T19-hdr":   ("h1,h2\nq,1\nr,2\n",     "h1,h2\nr,2\nq,1\n"),
    "T20-quot":  ('k,"a,b",2\n',           'k,"a,c",2\n'),
    "T21-nl":    ('k,"x\ny",2\nz,3,4\n',   'k,"x\ny",2\nz,3,5\n'),
}

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m61-rowalign-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, (left, right) in FIXTURES.items():
        lp = fx / f"{tag}-L.csv"; rp = fx / f"{tag}-R.csv"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "left": left, "right": right, "reports": {}}
        for lay in ("side-by-side", "interleaved"):
            lines = [f'data-report layout:{lay} output-to:"%3" "%1" "%2"']
            script = orc.write_script(run_dir / "reports" / f"{tag}.{lay}.bcs", lines)
            out = run_dir / "reports" / f"{tag}.{lay}.out"
            run = orc.run(inst.oracle_path, script, str(lp.resolve()),
                          str(rp.resolve()), str(out.resolve()),
                          timeout=120.0, script_text=lines[0])
            body = out.read_text(encoding="utf-8-sig", errors="replace") if out.exists() else ""
            rec["reports"][lay] = {"exit": run.exit_code, "body": body}
        results.append(rec)
        sbs = rec["reports"]["side-by-side"]
        print(f"{tag:10} exit={sbs['exit']}")
        for ln in sbs["body"].splitlines()[4:]:   # skip header block
            print(f"    {ln}")
        print()

    (run_dir / "m61-rowalign.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
