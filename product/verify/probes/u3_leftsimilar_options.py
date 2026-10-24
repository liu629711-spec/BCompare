#!/usr/bin/env python3
"""U3 probe -- leftsimilar rows under display options and text layouts (M2).

u2/u2b established the `leftsimilar`/`rightsimilar` statuses and their
`ignore-unimportant` folds, but only in the default XML view.  Before M2
records anchors that exercise display filtering and the text layouts on such
rows, the behaviour must be observed: are one-sided unimportant rows kept by
`display-mismatches` / dropped by `display-matches`?  How does the summary
layout count difference sections?  This probe runs ONE known pair through the
five question-raising modes and prints everything.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u3_leftsimilar_options.py
"""
from __future__ import annotations

import pathlib
import re
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

LEFT = "// a\n// b\nint x;\n"
RIGHT = "// c\nint x;\n"

MODES = [
    "display-mismatches",
    "display-matches",
    "display-context",
    None,  # summary layout, default options
    None,  # statistics layout, default options
]

STATUS_RE = re.compile(r'<linecomp status="([a-z]+)"')


def main() -> int:
    run_dir = REA / "product" / "verify" / "runs" / "u3-probe-leftsimilar"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "fixtures").mkdir(exist_ok=True)
    (run_dir / "reports").mkdir(exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    left = run_dir / "fixtures" / "cf-L.c"
    right = run_dir / "fixtures" / "cf-R.c"
    left.write_text(LEFT, encoding="utf-8")
    right.write_text(RIGHT, encoding="utf-8")

    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")
    for layout, options in [("xml", "display-mismatches"), ("xml", "display-matches"),
                            ("xml", "display-context"), ("summary", None),
                            ("statistics", None)]:
        tag = f"{layout}-{options or 'default'}"
        out = run_dir / "reports" / f"{tag}.out"
        script = orc.write_script(
            run_dir / "reports" / f"{tag}.bcs",
            [orc.text_script(layout, options)])
        run = orc.run(cur.oracle_path, script, left, right, out,
                      timeout=120.0, script_text=orc.text_script(layout, options))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        statuses = STATUS_RE.findall(body)
        print(f"  {tag:<28} exit={run.exit_code} statuses={statuses}")
        for line in body.splitlines():
            if line.strip() and "bcreport" not in line and "xml version" not in line:
                print(f"      | {line.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
