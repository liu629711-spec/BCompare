#!/usr/bin/env python3
"""U5f probe -- the text-report XML root shape under three load states.

U5c observed that `load <folders>` followed by `text-report layout:xml` exits 0
and writes a 256-byte report whose root holds `<ltpath>`/`<rtpath>` directly,
with no comparison element and no rows.  That is a *different root shape* from a
real text comparison, whose XML (per the golden anchors) carries a
`<textcomp>`-style body.

This probe pins the contract the M4 interpreter must reproduce:

  1. text-report with NO load at all        -> what root/elements?
  2. text-report with the two file args (%1 %2)  -> the normal comparison shape
  3. text-report after `load <files>`       -> same as (2)?
  4. text-report after `load <folders>`     -> the 256-byte shape from u5c
  5. The summary layout in case (1) -- does it differ from xml?

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5f_text_report_root.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5f-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    (fx / "Ldir").mkdir(parents=True, exist_ok=True)
    (fx / "Rdir").mkdir(parents=True, exist_ok=True)
    (fx / "Ldir" / "a.txt").write_bytes(b"alpha\n")
    (fx / "Rdir" / "a.txt").write_bytes(b"alpha\n")
    lf, rf = fx / "L.txt", fx / "R.txt"
    lf.write_bytes(b"alpha\nbeta\n")
    rf.write_bytes(b"alpha\nGAMMA\n")
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records: list[dict] = []

    def case(tag: str, lines: list[str]) -> dict:
        out = run_dir / "reports" / f"{tag}.out"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(lf), str(rf), out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        elements = re.findall(r"<(\w+)[ >/]", body)
        rec = {"tag": tag, "script": lines, "exit": run.exit_code,
               "report_bytes": run.report_bytes,
               "elements": sorted(set(elements)), "report_body": body}
        records.append(rec)
        print(f"  {tag:<26} exit={run.exit_code:<4} bytes={run.report_bytes:<5} "
              f"elements={sorted(set(elements))}")
        return rec

    case("no-load-xml", ['text-report layout:xml output-to:"%3"'])

    r = case("args-xml", ['text-report layout:xml output-to:"%3" "%1" "%2"'])
    print("---- args-xml body ----")
    print(r["report_body"][:900])
    print("---- end ----")

    case("load-files-xml", [f'load "{lf}" "{rf}"',
                            'text-report layout:xml output-to:"%3"'])

    r = case("load-folders-xml", [f'load "{fx / "Ldir"}" "{fx / "Rdir"}"',
                                  'text-report layout:xml output-to:"%3"'])
    print("---- load-folders-xml body ----")
    print(r["report_body"])
    print("---- end ----")

    case("no-load-summary", ['text-report layout:summary output-to:"%3"'])

    (run_dir / "u5f-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5f-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
