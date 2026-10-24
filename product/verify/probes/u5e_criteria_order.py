#!/usr/bin/env python3
"""U5e probe -- the last M4 semantics before interfaces are frozen.

  1. Does `criteria` issued AFTER `load` take effect?  (u5d showed `filter`
     after `load` does; criteria must be measured separately because the
     comparison may have been computed at load time.)
  2. `load <left>` with a single path -- documented as optional right.
  3. `option` command forms: stop-on-error, confirm:yes-to-all,
     confirm:no-to-all -- accepted, or syntax error?
  4. `expand "nope"` -- a path that is not there.
  5. `criteria timestamp:2sec` and `timestamp:2sec;IgnoreDST` -- syntax only.
  6. `filter` folder-mask raw XML, so the matcher's folder rule is recorded
     rather than inferred from a row count.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5e_criteria_order.py
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
               datetime.now(timezone.utc).strftime("u5e-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    for side in ("L", "R"):
        (fx / side / "sub").mkdir(parents=True, exist_ok=True)
        (fx / side / "other").mkdir(parents=True, exist_ok=True)
        # Same size, same timestamp, different bytes: only a content criterion
        # can see the difference.  os.utime pins both sides equal.
        (fx / side / "tiny.bin").write_bytes(b"AAA\n" if side == "L" else b"BBB\n")
        (fx / side / "sub" / "s.txt").write_bytes(b"s\n")
        (fx / side / "other" / "o.log").write_bytes(b"o\n")
    import os
    FIXED = 1_767_225_600
    for p in fx.rglob("*"):
        os.utime(p, (FIXED, FIXED))
    L, R = fx / "L", fx / "R"
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records: list[dict] = []

    def case(tag: str, lines: list[str], keep_body: bool = False) -> dict:
        out = run_dir / "reports" / f"{tag}.out"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(L), str(R), out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        statuses = re.findall(r'<filecomp status="([a-z]+)"', body)
        filters = re.findall(r"<filters>([^<]*)</filters>", body)
        rec = {"tag": tag, "script": lines, "exit": run.exit_code,
               "report_bytes": run.report_bytes, "statuses": statuses,
               "filters": filters,
               "report_body": body if keep_body else body[:500]}
        records.append(rec)
        print(f"  {tag:<28} exit={run.exit_code:<4} statuses={statuses} "
              f"filters={filters}")
        return rec

    report = ['folder-report layout:xml output-to:"%3"']

    # 1. criteria AFTER load vs BEFORE load -- same verdict?
    case("crit-before-load", ["criteria CRC", f'load "{L}" "{R}"', "expand all"] + report)
    case("crit-after-load", [f'load "{L}" "{R}"', "expand all", "criteria CRC"] + report)
    case("crit-after-report", [f'load "{L}" "{R}"', "expand all"] + report +
         ["criteria CRC", f'folder-report layout:xml output-to:"{run_dir}/reports/crit-after-report2.out"'])
    # Control: default criteria (size+timestamp) cannot see the content change.
    case("crit-default", [f'load "{L}" "{R}"', "expand all"] + report)

    # 2. Single-path load.
    case("load-left-only", [f'load "{L}"', "expand all"] + report)

    # 3. option forms.
    for tag, opt in [("option-stop-on-error", "stop-on-error"),
                     ("option-confirm-yes", "confirm:yes-to-all"),
                     ("option-confirm-no", "confirm:no-to-all"),
                     ("option-bogus", "frobnicate")]:
        case(tag, [f"option {opt}", f'load "{L}" "{R}"', "expand all"] + report)

    # 4. expand a path that is not there.
    case("expand-missing", [f'load "{L}" "{R}"', 'expand "nope"'] + report)

    # 5. timestamp tolerance syntax.
    case("crit-tol-sec", ["criteria timestamp:2sec", f'load "{L}" "{R}"',
                          "expand all"] + report)
    case("crit-tol-dst", ["criteria timestamp:2sec;IgnoreDST", f'load "{L}" "{R}"',
                          "expand all"] + report)

    # 6. Folder-mask raw XML.
    case("filter-folder-raw", ['filter "sub\\\\"', f'load "{L}" "{R}"', "expand all"]
         + report, keep_body=True)

    (run_dir / "u5e-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5e-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
