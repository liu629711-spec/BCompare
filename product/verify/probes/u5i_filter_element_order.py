#!/usr/bin/env python3
"""U5i probe -- element order and layout coverage for `filter` (final M4 unknown).

u5d/u5g showed `<filters>` appears in `folder-report layout:xml` right after
`<rtpath>`.  Two things still decide the report writer:

  1. When a script sets BOTH `filter` and
     `criteria rules-based ignore-unimportant`, what is the element order of
     `<filters>` and `<ignoreunimportant/>`?
  2. Do the non-XML folder layouts (summary, side-by-side) carry the filter
     text too, or only the XML layout?

Both are byte-level facts the M4 writer must reproduce, and both are cheap to
measure.  This is the last probe before the M4 interfaces are frozen.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5i_filter_element_order.py
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5i-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    for side in ("L", "R"):
        (fx / side).mkdir(parents=True, exist_ok=True)
        (fx / side / "a.txt").write_bytes(b"alpha\n// c\n")
        (fx / side / "b.log").write_bytes(b"beta\n")
    L, R = fx / "L", fx / "R"
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records: list[dict] = []

    def case(tag: str, lines: list[str]) -> dict:
        out = run_dir / "reports" / f"{tag}.out"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(L), str(R), out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        rec = {"tag": tag, "script": lines, "exit": run.exit_code,
               "report_bytes": run.report_bytes, "report_body": body}
        records.append(rec)
        print(f"  {tag:<30} exit={run.exit_code:<4} bytes={run.report_bytes}")
        # Print the header region (everything before the first row element).
        head = []
        for line in body.splitlines():
            s = line.strip()
            if s.startswith(("<foldercomp", "<filecomp")) and head:
                break
            head.append(line)
        print("    header:", [h.strip() for h in head if h.strip()])
        return rec

    base = [f'load "{L}" "{R}"', "expand all",
            'folder-report layout:xml output-to:"%3"']

    case("xml-filter-only", ['filter "*.txt"'] + base)
    case("xml-iu-only", ["criteria rules-based ignore-unimportant"] + base)
    case("xml-filter-and-iu",
         ['filter "*.txt"', "criteria rules-based ignore-unimportant"] + base)
    case("xml-iu-then-filter",
         ["criteria rules-based ignore-unimportant", 'filter "*.txt"'] + base)
    case("xml-filter-then-iu",
         ['filter "*.txt"', "criteria rules-based ignore-unimportant"] + base)
    case("summary-filter", ['filter "*.txt"', f'load "{L}" "{R}"', "expand all",
                            'folder-report layout:summary output-to:"%3"'])
    case("sxs-filter", ['filter "*.txt"', f'load "{L}" "{R}"', "expand all",
                        'folder-report layout:side-by-side output-to:"%3"'])
    case("xml-filter-twice", ['filter "*.txt"', 'filter "*.log"',
                              f'load "{L}" "{R}"', "expand all",
                              'folder-report layout:xml output-to:"%3"'])

    (run_dir / "u5i-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5i-results.json'}")

    print("\n---- full bodies of the two sorting cases ----")
    for r in records:
        if r["tag"] in ("xml-filter-and-iu", "summary-filter", "xml-filter-twice"):
            print(f"##### {r['tag']} #####")
            print(r["report_body"][:900])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
