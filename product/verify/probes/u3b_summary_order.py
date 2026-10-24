#!/usr/bin/env python3
"""U3b probe -- summary count-line ORDER with unimportant orphans (M2).

U3 observed a new summary count label (`个不重要的左边独有行`) positioned
BEFORE `个不重要的差异行`, which the M1 order (same, unimportant difference,
left orphan, right orphan, important difference) does not predict.  This
probe pins the full count-line order for the rightsimilar case and for a file
that mixes unimportant and important orphans.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u3b_summary_order.py
"""
from __future__ import annotations

import pathlib
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PAIRS = [
    ("right-unimportant-orphan", ["int x;"], ["int y;", "// c"]),
    ("mixed-unimportant-and-important", ["// a", "// b", "int x;"], ["// c", "int y;"]),
    ("all-kinds", ["// a", "int p;", "// q", "int r;"], ["int x;", "// b", "int y;", "// s"]),
]


def main() -> int:
    run_dir = REA / "product" / "verify" / "runs" / "u3b-probe-summary-order"
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")
    for name, left_lines, right_lines in PAIRS:
        left = run_dir / "fixtures" / f"{name}-L.c"
        right = run_dir / "fixtures" / f"{name}-R.c"
        left.write_text("\n".join(left_lines) + "\n", encoding="utf-8")
        right.write_text("\n".join(right_lines) + "\n", encoding="utf-8")
        out = run_dir / "reports" / f"{name}.summary"
        script = orc.write_script(run_dir / "reports" / f"{name}.bcs",
                                  [orc.text_script("summary", None)])
        run = orc.run(cur.oracle_path, script, left, right, out,
                      timeout=120.0, script_text=orc.text_script("summary", None))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        print(f"  == {name} exit={run.exit_code}")
        for line in body.splitlines():
            if line.strip():
                print(f"     | {line.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
