#!/usr/bin/env python3
"""U5d probe -- `expand` shaping and `filter` mask rules (M4 inputs).

Questions left before the M4 interfaces can be frozen:

  1. `load` + `folder-report` with NO `expand`: what exactly does the report
     contain?  (tree.rs cites `tools/_audit/dir-load-expand-report.xml` but that
     audit file is not in the product tree, so this is re-measured.)
  2. `expand <path>` for one subfolder only -- partial expansion shape.
  3. `filter` mask rules that decide the matcher implementation:
       - case sensitivity on Windows ("*.TXT" vs a.txt)
       - `?` wildcard
       - semicolon lists and mixed include/exclude ordering
       - folder masks with a trailing backslash
       - does a filter apply to subfolder *contents* transitively?
  4. Whether `criteria`/`filter`/`expand` may come after `load` (order freedom).

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5d_expand_and_filter.py
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
               datetime.now(timezone.utc).strftime("u5d-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    for side in ("L", "R"):
        for sub in ("sub", "sub/deep", "other"):
            (fx / side / sub).mkdir(parents=True, exist_ok=True)
        (fx / side / "a.txt").write_bytes(b"alpha\n" + side.encode() + b"\n")
        (fx / side / "b.log").write_bytes(b"log\n" + side.encode() + b"\n")
        (fx / side / "c.TXT").write_bytes(b"upper\n" + side.encode() + b"\n")
        (fx / side / "d1.bin").write_bytes(b"x\n")
        (fx / side / "sub" / "e.txt").write_bytes(b"e\n" + side.encode() + b"\n")
        (fx / side / "sub" / "deep" / "f.txt").write_bytes(b"f\n" + side.encode() + b"\n")
        (fx / side / "other" / "g.log").write_bytes(b"g\n" + side.encode() + b"\n")
    L, R = fx / "L", fx / "R"
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records: list[dict] = []

    def case(tag: str, lines: list[str]) -> dict:
        out = run_dir / "reports" / f"{tag}.xml"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(L), str(R), out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        # Harvest a compact structural summary: row kind + name + status.
        rows = []
        for m in re.finditer(
                r'<(foldercomp|filecomp)( status="([a-z]+)")?>(.*?)</\1>',
                body, re.S):
            kind = m.group(1)
            status = m.group(3) or ""
            inner = m.group(4)
            names = re.findall(r"<name>([^<]*)</name>", inner)
            empty_size = "<size/>" in inner
            rows.append({"kind": kind, "status": status, "names": names,
                         "empty_size": empty_size})
        rec = {"tag": tag, "script": lines, "exit": run.exit_code,
               "report_bytes": run.report_bytes, "rows": rows,
               "report_body": body}
        records.append(rec)
        shown = ", ".join(
            f"{r['kind'][:4]}:{'/'.join(r['names'][:2])}"
            f"{'#' + r['status'] if r['status'] else ''}"
            f"{'∅' if r['empty_size'] else ''}" for r in rows)
        print(f"  {tag:<26} exit={run.exit_code:<4} rows={len(rows):<3} {shown[:150]}")
        return rec

    # 1. No expand at all.
    case("no-expand", [f'load "{L}" "{R}"',
                       'folder-report layout:xml output-to:"%3"'])
    # 2. expand all (control).
    case("expand-all", [f'load "{L}" "{R}"', "expand all",
                        'folder-report layout:xml output-to:"%3"'])
    # 3. One subfolder only.
    case("expand-sub", [f'load "{L}" "{R}"', 'expand "sub"',
                        'folder-report layout:xml output-to:"%3"'])
    # 4. Filter case sensitivity.
    r = case("filter-upper-txt", ['filter "*.TXT"', f'load "{L}" "{R}"', "expand all",
                                  'folder-report layout:xml output-to:"%3"'])
    # 5. Question-mark wildcard.
    case("filter-question", ['filter "d?.bin"', f'load "{L}" "{R}"', "expand all",
                             'folder-report layout:xml output-to:"%3"'])
    # 6. Semicolon list with an exclusion.
    case("filter-list-mixed", ['filter "*.txt;*.TXT;-b.log"', f'load "{L}" "{R}"',
                               "expand all",
                               'folder-report layout:xml output-to:"%3"'])
    # 7. Folder mask only.
    case("filter-folder-only", ['filter "sub\\\\"', f'load "{L}" "{R}"', "expand all",
                                'folder-report layout:xml output-to:"%3"'])
    # 8. Settings after load (order freedom).
    case("settings-after-load", [f'load "{L}" "{R}"', "expand all", 'filter "*.txt"',
                                 'folder-report layout:xml output-to:"%3"'])

    (run_dir / "u5d-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5d-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
