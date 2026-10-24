#!/usr/bin/env python3
"""Verify this engine's XML against the one stored Beyond Compare folder report.

    python D:\\Rea\\product\\dir\\tools\\verify_against_oracle_xml.py

# What this proves, and what it does not

The only stored Oracle folder report in this workspace is
`tools/_audit/dir-load-expand-report.xml` (produced by the audit's
`probe-dir-oracle.py` against BCompare 5.2.1.32035 over the read-only fixture
`D:\\Rea\\verify\\dir\\trees`). This script runs the local engine over that same
tree pair and compares byte-for-byte, after removing the wall-clock `created`
attribute that both sides stamp.

A PASS therefore means: **for this one tree pair, under the default criteria, this
engine's XML is byte-identical to what Beyond Compare produced.**

It does **not** mean folder comparison is compatible in general:
`product/verify/README.md` section 9 states there is no golden folder report
corpus, and this task was forbidden from invoking the Oracle, so no other tree
pair or criteria setting has been measured. The other 74 fixture cases check this
engine against derived expectations, not against BC.

Exit codes: 0 identical, 1 differs, 2 could not run (missing evidence).
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DIR_CRATE = HERE.parent
BINARY = DIR_CRATE / "target" / "debug" / ("reacmp-dir.exe" if sys.platform == "win32" else "reacmp-dir")

ORACLE_REPORTS = [
    pathlib.Path(r"D:\Rea\tools\_audit\dir-load-expand-report.xml"),
    pathlib.Path(r"D:\Rea\product\verify\runs\A1-final\raw\folder-current-trees.xml"),
]
AUDIT_TREES = pathlib.Path(r"D:\Rea\verify\dir\trees")

#: The observed report was rendered in the host's local zone; this constant makes
#: the comparison independent of the machine it is re-run on. 480 = UTC+08:00.
TZ_OFFSET_MINUTES = "480"

#: The observed report begins with a UTF-8 BOM (measured: the first three bytes of
#: `dir-load-expand-report.xml` are `EF BB BF`). Named so the comparison reads it
#: explicitly rather than relying on a decoder.
BOM = b"\xef\xbb\xbf"


def strip_created(xml: str) -> str:
    """Remove the wall-clock `created` attribute.

    Both writers stamp the generation time, so two runs of the *same* engine
    already differ there. Removing it is the minimum normalization that makes the
    comparison meaningful; nothing else is normalized.
    """
    return re.sub(r'<bcreport created="[^"]*">', "<bcreport>", xml, count=1)


def main() -> int:
    if not BINARY.is_file():
        print(f"FAIL: {BINARY} not found; run `cargo build` in {DIR_CRATE}")
        return 2

    oracle_path = next((p for p in ORACLE_REPORTS if p.is_file()), None)
    if oracle_path is None:
        print("FAIL: no stored Oracle folder report found at any of:")
        for p in ORACLE_REPORTS:
            print(f"  {p}")
        return 2

    if not AUDIT_TREES.is_dir():
        print(f"FAIL: the read-only audit fixture {AUDIT_TREES} is not present")
        return 2

    # Compare at the **byte** level. Decoding first would be a mistake: this report
    # starts with a UTF-8 BOM (`EF BB BF`, an observed property of the Oracle's
    # output), and `utf-8-sig` strips it from one side only — which made an earlier
    # version of this script report a spurious difference on line 1.
    oracle_raw = oracle_path.read_bytes()
    oracle = strip_created(oracle_raw.decode("utf-8"))

    out = DIR_CRATE / "target" / "oracle-parity-check.xml"
    result = subprocess.run(
        [
            str(BINARY),
            "--print-exit-code",
            "--tz-offset", TZ_OFFSET_MINUTES,
            "--out", str(out),
            str(AUDIT_TREES / "L"),
            str(AUDIT_TREES / "R"),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"FAIL: the engine exited {result.returncode}: {result.stderr.strip()}")
        return 2

    mine_raw = out.read_bytes()
    mine = strip_created(mine_raw.decode("utf-8"))

    print(f"oracle report : {oracle_path}")
    print(f"  bytes       : {len(oracle_raw)} raw")
    print(f"  BOM present : {oracle_raw.startswith(BOM)}")
    print(f"local engine  : {out}")
    print(f"  bytes       : {len(mine_raw)} raw")
    print(f"  BOM present : {mine_raw.startswith(BOM)}")
    print()

    if oracle == mine:
        print("PASS: byte-identical to the observed Beyond Compare folder report")
        print("      (one tree pair, default criteria — NOT a general parity claim)")
        return 0

    print("FAIL: output differs from the observed Oracle report")
    import difflib

    diff = list(
        difflib.unified_diff(
            oracle.splitlines(keepends=True),
            mine_cmp.splitlines(keepends=True),
            "bcompare",
            "reacmp-dir",
            n=1,
        )
    )
    for line in diff[:60]:
        sys.stdout.write(line if line.endswith("\n") else line + "\n")
    if len(diff) > 60:
        print(f"... and {len(diff) - 60} more diff lines")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
