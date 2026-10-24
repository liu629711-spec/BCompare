#!/usr/bin/env python3
"""M6.5b table goldens: append the m68 discriminating cells to the
verify/table golden tree (append-only, same discipline as
tools/m64_add_table_goldens.py).

Cells (each reproduces an OBSERVED m68 probe, runs/m68-mixedext-*):

  t-mixed-csvp   L=`a;b` .txt / R=`a;b` .csv, side-by-side.
      The ONLY mixed-extension pair in the archive that separates the pin
      rules: MX6 rendered ONE column (`a;b =`), so the `.csv` side pins
      the comma format for BOTH files (candidate rule (i); (ii) would have
      joint-scanned the .txt side and semi-split it). No comma exists
      anywhere, so nothing else explains the single column.

  t-int-rawline  L=` ab`/`cd` vs ` ab`/`cX`, interleaved (.txt both).
      First interleaved rawline cell end-to-end: leading whitespace is
      dropped (`ab`, SP10/IR1), rows are compared verbatim otherwise,
      single column `A`, markers `=`/`<>` pairs in one block.

  t-int-num      L=`1`/`2` vs `1`/`3`, interleaved (.txt both).
      Numeric rawline cells left-justify in interleaved (IR3) -- the same
      rule as delimited numbers (T19/T21); `1 =` then `2`/`3` pair.

Space-split cells stay EXCLUDED (permanent KNOWN, docs/13 §8).

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m68_add_table_goldens.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def C(*rows):
    return "".join(r + "\n" for r in rows)


#: (name, ext, ext_right, layout, left text, right text, note)
CASES = [
    ("t-mixed-csvp", "txt", "csv", "side-by-side",
     C("a;b"), C("a;b"),
     "MX6: mixed .txt/.csv with NO comma anywhere -> ONE column: either "
     "file .csv pins fixed comma for BOTH files (docs/13 \u00a78.2)"),
    ("t-int-rawline", "txt", "", "interleaved",
     C(" ab", "cd"), C(" ab", "cX"),
     "IR1: interleaved rawline -- leading whitespace dropped (SP10), "
     "single column, verbatim equality otherwise"),
    ("t-int-num", "txt", "", "interleaved",
     C("1", "2"), C("1", "3"),
     "IR3: numeric rawline cells left-justify in interleaved (T19/T21 "
     "rule holds for rawline too)"),
]


def main() -> int:
    tree = REA / "verify" / "table"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m68-table-goldens-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")

    man_path = tree / "manifest.json"
    manifest: dict = json.loads(man_path.read_text(encoding="utf-8"))
    shutil.copy2(man_path, run_dir / "manifest.json.before")
    clash = [name for name, *_ in CASES if name in manifest]
    if clash:
        raise SystemExit(f"manifest already has keys: {clash}")

    added = 0
    for name, ext, ext_right, layout, left_t, right_t, note in CASES:
        left = tree / f"{name}-L.{ext}"
        right = tree / f"{name}-R.{ext_right or ext}"
        left.write_text(left_t, encoding="utf-8", newline="")
        right.write_text(right_t, encoding="utf-8", newline="")
        report = tree / f"{name}.txt"
        script_text = orc.table_script(layout)
        sp = orc.write_script(run_dir / f"{name}.bcs", [script_text])
        run = orc.run(cur.oracle_path, sp, left, right, report,
                      timeout=120.0, script_text=script_text)
        if run.exit_code != 0 or not run.report_exists:
            raise SystemExit(f"{name}: oracle exit {run.exit_code}, "
                             f"report={run.report_exists}")
        entry = {
            "layout": layout,
            "ext": ext,
            "note": note,
            "exit_code": run.exit_code,
            "bytes": report.stat().st_size,
            "report": str(report),
        }
        if ext_right:
            entry["ext_right"] = ext_right
        manifest[name] = entry
        added += 1
        print(f"  {name:<16} [{layout}] exit={run.exit_code} "
              f"bytes={report.stat().st_size}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"manifest: +{added} table goldens -> {len(manifest)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
