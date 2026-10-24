#!/usr/bin/env python3
"""M2.6 alignment probe: compare importance-sensitive and plain-text ties.

Run serially; never alongside pytest or another Oracle caller.
    cd D:\\Rea\\product\\verify
    python probes/m26_weighted_diff.py
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
VERIFY = REA / "product" / "verify"
sys.path.insert(0, str(VERIFY))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

# Matched-line positions and candidate unmatched runs are held constant where
# possible; only grammar classification or unimportant-line placement changes.
CASES = [
    ("all-kinds-c", "c",
     ["// a", "int p;", "// q", "int r;"],
     ["int x;", "// b", "int y;", "// s"],
     "known U2 all-kinds case"),
    ("all-kinds-txt", "txt",
     ["// a", "int p;", "// q", "int r;"],
     ["int x;", "// b", "int y;", "// s"],
     "same bytes/text, plain-text grammar control"),
    ("comment-lead-c", "c",
     ["// a", "int p;", "int r;"],
     ["int x;", "int y;", "// s"],
     "unimportant line adjacent to leading replace"),
    ("comment-middle-c", "c",
     ["int p;", "// a", "int r;"],
     ["int x;", "int y;", "// s"],
     "unimportant line inside replace block"),
    ("comment-tail-c", "c",
     ["int p;", "int r;", "// a"],
     ["int x;", "int y;", "// s"],
     "unimportant line after replace"),
    ("tail-1v2-txt", "txt",
     ["alpha", "beta", "?next"],
     ["gamma", "alpha", "beta", "x", "next"],
     "known U8h plain-text tail tie"),
]


def shape(body: str) -> list[tuple[str, str, str]]:
    out = []
    for match in re.finditer(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', body, re.S):
        left = re.search(r'ltid="(\d+)"', match.group(2))
        right = re.search(r'rtid="(\d+)"', match.group(2))
        out.append((match.group(1), left.group(1) if left else "-",
                    right.group(1) if right else "-"))
    return out


def main() -> int:
    run_dir = (VERIFY / "runs" /
               datetime.now(timezone.utc).strftime("m26-weighted-probe-%Y%m%dT%H%M%SZ"))
    fixtures, reports = run_dir / "fixtures", run_dir / "reports"
    fixtures.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")
    print(f"app    : {inst.app_path} ({inst.app_version})")
    print(f"run    : {run_dir}\n")

    records = []
    for tag, ext, left_lines, right_lines, purpose in CASES:
        left = fixtures / f"{tag}-L.{ext}"
        right = fixtures / f"{tag}-R.{ext}"
        left.write_text("\n".join(left_lines) + "\n", encoding="utf-8", newline="")
        right.write_text("\n".join(right_lines) + "\n", encoding="utf-8", newline="")
        command = orc.text_script("xml")
        script = orc.write_script(reports / f"{tag}.bcs", [command])
        oracle_path = reports / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(left), str(right), oracle_path,
                      timeout=180.0, script_text=command)
        oracle_body = (oracle_path.read_bytes().decode("utf-8-sig", errors="replace")
                       if run.report_exists else "")

        product_path = reports / f"{tag}.product.xml"
        proc = subprocess.run([str(PRODUCT), str(left), str(right), str(product_path)],
                              capture_output=True, timeout=120)
        product_body = (product_path.read_bytes().decode("utf-8-sig", errors="replace")
                        if product_path.exists() else "")
        record = {
            "case": tag, "extension": ext, "purpose": purpose,
            "left": left_lines, "right": right_lines,
            "oracle_exit": run.exit_code, "oracle_timeout": run.timed_out,
            "oracle_containment": run.containment,
            "product_exit": proc.returncode,
            "oracle_rows": shape(oracle_body), "product_rows": shape(product_body),
            "same_rows": shape(oracle_body) == shape(product_body),
            "oracle_report": oracle_body, "product_report": product_body,
        }
        records.append(record)
        print(f"{'SAME' if record['same_rows'] else 'DIFF'} {tag} "
              f"oracle={run.exit_code} product={proc.returncode}")
        print(f"  oracle : {record['oracle_rows']}")
        if not record["same_rows"]:
            print(f"  product: {record['product_rows']}")

    out = run_dir / "m26-weighted-results.json"
    out.write_text(json.dumps({
        "oracle": {"path": str(inst.oracle_path), "version": inst.oracle_version,
                   "sha256": inst.oracle_sha256},
        "application": {"path": str(inst.app_path), "version": inst.app_version,
                        "sha256": inst.app_sha256},
        "records": records,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nraw: {out}")
    return 0 if all(r["oracle_exit"] == 0 and r["product_exit"] == 0 for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
