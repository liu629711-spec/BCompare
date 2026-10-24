#!/usr/bin/env python3
"""M5.2 probe -- which statistics column does a one-sided unimportant line hit?

The product's `statistics` layout counts IDeleted=LeftOrphan, IAdded=RightOrphan,
IChanged=Different, UChanged=Similar and writes 0 for UOriginal/UAdded/UDeleted.
The recorded corpus has no statistics report containing a `leftsimilar` /
`rightsimilar` row (a one-sided comment or blank line), so where BC books those
rows is unmeasured. The M2 working hypothesis: leftsimilar lands in **UDeleted**
and rightsimilar in **UAdded**; this probe measures it, plus what UOriginal
counts and how `options:ignore-unimportant` changes the books.

Shapes (C fixtures -- comments are unimportant only under a grammar):

  ls-comment    L=[int a;, // c]      R=[int b;]      one left comment
  ls-blank      L=[int a;, ""]        R=[int b;]      one left blank line
  rs-comment    L=[int b;]            R=[int a;, // c]  one right comment
  both-sides    L=[int a;, // c1, // c2] R=[int b;, // c3]
  iu-both-sides same as both-sides with options:ignore-unimportant
  plain-comment L=[a, // c]           R=[b]           .txt: `// c` is content

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m52_statistics_columns.py
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

#: name -> (left lines, right lines, options, fixture suffix, purpose)
SHAPES: dict[str, tuple[list[str], list[str], str | None, str, str]] = {
    "ls-comment": (["int a;", "// c"], ["int b;"], None, ".c",
                   "one left comment -> UDeleted?"),
    "ls-blank": (["int a;", ""], ["int b;"], None, ".c",
                 "one left blank line -> UDeleted? UOriginal?"),
    "rs-comment": (["int b;"], ["int a;", "// c"], None, ".c",
                   "one right comment -> UAdded?"),
    "both-sides": (["int a;", "// c1", "// c2"], ["int b;", "// c3"], None, ".c",
                   "two left + one right comments"),
    "iu-both-sides": (["int a;", "// c1", "// c2"], ["int b;", "// c3"],
                      "ignore-unimportant", ".c",
                      "the same books under /iu"),
    "plain-comment": (["a", "// c"], ["b"], None, ".txt",
                      "plain text: `// c` is content -> IDeleted, not U"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m52-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print("purpose : where do one-sided unimportant lines land in statistics?\n")

    records: list[dict] = []
    for tag, (ll, rl, options, ext, purpose) in SHAPES.items():
        lp = fx / f"{tag}-L{ext}"
        rp = fx / f"{tag}-R{ext}"
        lp.write_text("\n".join(ll) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(rl) + "\n", encoding="utf-8", newline="")

        lines = [orc.text_script("statistics", options)]
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        o_out = run_dir / "reports" / f"{tag}.oracle.csv"
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace") \
            if run.report_exists and run.report_bytes else ""

        argv = [str(PRODUCT), str(lp), str(rp),
                str(run_dir / "reports" / f"{tag}.product.csv"),
                "--layout=statistics"]
        if options:
            argv.append(f"--opt={options}")
        subprocess.run(argv, capture_output=True, timeout=120)
        p_out = run_dir / "reports" / f"{tag}.product.csv"
        p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace") \
            if p_out.exists() else ""

        def data_row(body: str) -> str:
            """The CSV data row: the last non-empty line of the report.

            The localized Oracle writes Chinese title/header labels
            (文本比较(T), 源文件,比较文件,...) that no label list can keep up
            with; the data row is always last, whatever the labels say.
            """
            lines = [ln for ln in body.replace("\r\n", "\n").split("\n")
                     if ln.strip()]
            return lines[-1] if lines else ""

        o_row, p_row = data_row(o_body), data_row(p_body)
        # Compare only the 8 numeric counters (paths legitimately differ).
        nums = lambda row: ",".join(row.split(",")[2:10])
        same = nums(o_row) == nums(p_row)
        records.append({"tag": tag, "purpose": purpose, "same": same,
                        "oracle_row": o_row, "product_row": p_row,
                        "oracle_exit": run.exit_code,
                        "oracle_body": o_body, "product_body": p_body})
        mark = "OK  " if same else "DIFF"
        print(f"  {mark} {tag:<15} {purpose}")
        print(f"       oracle : {o_row}")
        if not same:
            print(f"       product: {p_row}")

    (run_dir / "m52-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'm52-results.json'}")
    agree = sum(1 for r in records if r["same"])
    print(f"\n{agree}/{len(records)} counter rows agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
