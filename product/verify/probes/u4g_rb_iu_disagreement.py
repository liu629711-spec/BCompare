#!/usr/bin/env python3
"""U4g probe -- resolve the crit-rb-iu-fold disagreement.

The engine folds `plain.txt` (whitespace-only, plain text) and
`whitespace_only.c` (whitespace-only C) to `same` under
`rules-based ignore-unimportant`, while the reference model predicts `diff`.
Both are ambiguous readings of the U1/U2 table, so ask the Oracle about
exactly these two files, plus their non-ignored controls.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4g_rb_iu_disagreement.py
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

TREES = REA / "product" / "dir" / "fixtures" / "trees" / "rules-based"

CASES = [
    ("rb", "rules-based"),
    ("rb-iu", "rules-based ignore-unimportant"),
    ("binary", "binary"),
    ("binary-iu", "binary ignore-unimportant"),
    ("crc", "CRC"),
    ("default", ""),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4g-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")
    print(f"trees  : {TREES}\n")

    records = []
    for tag, criteria in CASES:
        out = run_dir / "reports" / f"{tag}.xml"
        lines = []
        if criteria:
            lines.append(f"criteria {criteria}")
        lines += [f'load "{TREES / "L"}" "{TREES / "R"}"', "expand all",
                  f'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, TREES / "L", TREES / "R", out,
                      timeout=180.0, script_text="\n".join(lines))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        # name -> status map
        pairs = re.findall(r'<filecomp status="([a-z]+)">(.*?)</filecomp>', body, re.S)
        mapped = {}
        for status, chunk in pairs:
            for nm in re.findall(r"<name>([^<]*)</name>", chunk):
                mapped.setdefault(nm, status)
        records.append({"tag": tag, "criteria": criteria, "exit": run.exit_code,
                        "map": mapped})
        print(f"  {tag:<10} crit={criteria or '(default)':<32} {json.dumps(mapped, ensure_ascii=False)}")

    (run_dir / "u4g-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4g-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
