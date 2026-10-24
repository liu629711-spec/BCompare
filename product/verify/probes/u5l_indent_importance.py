#!/usr/bin/env python3
"""U5l probe -- indentation importance: /qc said "Similar", M2 said "important".

U5k measured `/qc` on three whitespace-only pairs:

    indent-only-py   4 vs 8 spaces ....... exit 12 (Similar = unimportant only)
    trailing-ws-py   trailing spaces ..... exit 12 (Similar)
    indent-3v2-c     3 vs 2 spaces ....... exit 12 (Similar)

Exit 12 means BC's rules-based verdict was "similar", i.e. the difference is
**unimportant**.  But `product/core/src/importance.rs` (M2) records the Python
leading-`Indent` element as IMPORTANT, and treats leading whitespace as
important for every grammar.  Both cannot be right about the *report* path.

Why this is not just a `/qc` curiosity: if the report path also calls an
indent-only pair `similar`, then M2's engine diverges from the Oracle on a case
its 101 anchors apparently do not cover, and the M4 gate would inherit the
divergence.  This probe measures the **report** verdict for the same three
pairs plus two controls, so the engine can be checked against a first-class
observation rather than an exit code.

Measured here:
  * `text-report layout:xml` status sequence for each pair
  * the same pairs through the product engine (`reacmp.exe`), for a direct
    comparison

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5l_indent_importance.py
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

CANDIDATE = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

PAIRS = {
    "indent-py-4v8":  ("def f():\n    return 1\n", "def f():\n        return 1\n", "py"),
    "indent-c-3v2":   ("int main() {\n   int a;\n}\n", "int main() {\n  int a;\n}\n", "c"),
    "trailing-ws-py": ("x = 1   \n", "x = 1\n", "py"),
    "ws-midline-py":  ("x = 1 + 2\n", "x = 1  +  2\n", "py"),
    "ws-midline-c":   ("int a = 1+2;\n", "int a = 1 + 2;\n", "c"),
    "content-ctrl":   ("x = 1\n", "x = 2\n", "py"),
    "comment-ctrl":   ("x = 1  # one\n", "x = 1  # two\n", "py"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5l-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle    : {inst.oracle_path} ({inst.oracle_version})")
    print(f"candidate : {CANDIDATE} exists={CANDIDATE.exists()}")

    records: list[dict] = []
    for tag, (lb, rb, ext) in PAIRS.items():
        lp = fx / f"{tag}-L.{ext}"
        rp = fx / f"{tag}-R.{ext}"
        lp.write_bytes(lb.encode())
        rp.write_bytes(rb.encode())

        # --- Oracle: text-report XML ---
        out = run_dir / "reports" / f"{tag}.xml"
        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        oracle_statuses = re.findall(r'<linecomp status="([a-z]+)"', body)

        # --- Product engine: same report shape ---
        mine = run_dir / "reports" / f"{tag}.mine.xml"
        proc = subprocess.run(
            [str(CANDIDATE), str(lp), str(rp), str(mine)],
            capture_output=True, timeout=120)
        mine_body = ""
        if mine.exists():
            mine_body = mine.read_bytes().decode("utf-8-sig", errors="replace")
        mine_statuses = re.findall(r'<linecomp status="([a-z]+)"', mine_body)

        rec = {
            "tag": tag, "ext": ext,
            "left": lb, "right": rb,
            "oracle_exit": run.exit_code,
            "oracle_statuses": oracle_statuses,
            "engine_exit": proc.returncode,
            "engine_statuses": mine_statuses,
            "agree": oracle_statuses == mine_statuses,
            "oracle_body": body,
            "engine_body": mine_body,
        }
        records.append(rec)
        mark = "OK " if rec["agree"] else "DIFF"
        print(f"  {mark} {tag:<16} oracle={oracle_statuses} "
              f"engine={mine_statuses}")

    (run_dir / "u5l-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5l-results.json'}")

    bad = [r for r in records if not r["agree"]]
    if bad:
        print(f"\n{len(bad)} disagreement(s) -- bodies for the first:")
        r = bad[0]
        print(f"--- oracle ({r['tag']}) ---")
        print(r["oracle_body"][:800])
        print(f"--- engine ({r['tag']}) ---")
        print(r["engine_body"][:800])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
