#!/usr/bin/env python3
"""U5 probe -- exit-code semantics for the M4 CLI subset.

M4 must reproduce BC's exit codes, and until now the only *measured* data
points were:

  * 0   -- a successful script run (`oracle.py` records this on every anchor)
  * 106 -- `folder-report` without a preceding `load` (observed while the
           folder recipe was being fixed)

Everything else in `oracle.py`'s ``EXIT_MEANINGS`` came from the help file
(`help/command_line_reference.html` "Return codes" table), i.e. it is
**documentation, not observation**.  The table in the help file also disagrees
with the prose descriptions that were recorded earlier in this workspace:

    help file : 104 Trial expired / 105 Error loading script file /
                106 Script syntax error / 107 Script failed to load folders
    oracle.py : 104 licensing / 105 script error /
                106 script command error / 107 file not found

Both cannot be right about 105/106/107, and M4.3's exit-code tests must assert
measured behaviour.  This probe therefore runs the smallest script set that
separates the three documented error classes, plus the documented `/qc`
quick-compare levels (1/2/11/12/13), and records the actual exit code of each.

Design notes:

* Every invocation carries ``/silent``.  Without it the Oracle may raise a
  MODAL dialog and wait for a click forever; with it, "any unresolved issue
  that would normally show a dialog will log an error instead"
  (`help/command_line_reference.html`, /silent).
* All runs go through ``harness.oracle``'s Job Object containment, so no
  ``BCompare.exe`` GUI host can outlive a call, and the Oracle is invoked in
  place from its install directory.
* The `/qc` cases invoke the executable directly (no ``@script``), so they use
  the containment primitives from ``harness.oracle`` rather than ``oracle.run``
  (whose command shape is fixed to the script recipe).

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5_exit_codes.py
"""
from __future__ import annotations

import ctypes
import json
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def run_raw(oracle, args: list[str], *, timeout: float = 120.0) -> tuple[int, str]:
    """Run the Oracle with an exact argv (no script wrapper). Returns (exit, stderr)."""
    cmd = [str(oracle), "/silent", *args]
    with orc.ProcessTree() as tree:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(pathlib.Path(oracle).parent),
            creationflags=orc._CREATE_SUSPENDED if tree.enabled else 0,
        )
        tree.assign(proc)
        if tree.enabled:
            orc._resume(proc)
        try:
            raw_out, raw_err = proc.communicate(timeout=timeout)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            tree.kill_tree()
            proc.kill()
            raw_out, raw_err = proc.communicate(timeout=10)
            code = -1
    return code, raw_err.decode("utf-8", errors="replace")[:400]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    L = run_dir / "fixtures" / "L.txt"
    R = run_dir / "fixtures" / "R.txt"
    OUT = run_dir / "reports" / "out.txt"
    L.write_bytes(b"alpha\nbeta\n")
    R.write_bytes(b"alpha\nGAMMA\n")

    records: list[dict] = []

    def script_case(tag: str, lines: list[str], left: str, right: str,
                    expect_report: bool = False) -> None:
        out = run_dir / "reports" / f"{tag}.out"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, left, right, out,
                      timeout=180.0, script_text="\n".join(lines))
        rec = {
            "tag": tag,
            "kind": "script",
            "script": lines,
            "exit": run.exit_code,
            "timed_out": run.timed_out,
            "report_bytes": run.report_bytes,
            "report_exists": run.report_exists,
            "stderr": run.stderr.strip()[:300],
        }
        records.append(rec)
        print(f"  {tag:<28} exit={run.exit_code:<4} report={run.report_bytes}B"
              + (f" stderr={rec['stderr']!r}" if rec["stderr"] else ""))

    # ---------------------------------------------------------------
    # 1. Control: the documented-good text recipe must exit 0.
    # ---------------------------------------------------------------
    script_case("control-text-report",
                ['text-report layout:xml output-to:"%3" "%1" "%2"'],
                str(L), str(R), expect_report=True)

    # ---------------------------------------------------------------
    # 2. Error classes. Which of 105/106/107 fires for which mistake?
    # ---------------------------------------------------------------
    # 2a. @script file that does not exist is handled by the caller shell, not
    #     by run() -- pass a path that is not there.
    missing = run_dir / "reports" / "does-not-exist.bcs"
    out = run_dir / "reports" / "missing-script.out"
    run = orc.run(inst.oracle_path, missing, str(L), str(R), out, timeout=180.0)
    records.append({"tag": "missing-script-file", "kind": "script",
                    "script": None, "exit": run.exit_code,
                    "timed_out": run.timed_out, "report_bytes": run.report_bytes,
                    "report_exists": run.report_exists,
                    "stderr": run.stderr.strip()[:300]})
    print(f"  {'missing-script-file':<28} exit={run.exit_code}")

    # 2b. Unknown command name.
    script_case("unknown-command", ["frobnicate all"], str(L), str(R))

    # 2c. Known command, malformed arguments (text-report without output-to).
    script_case("missing-required-arg", ["text-report layout:xml"], str(L), str(R))

    # 2d. Known command, bad enum value (unknown layout name).
    script_case("bad-option-value",
                ['text-report layout:not-a-layout output-to:"%3" "%1" "%2"'],
                str(L), str(R))

    # 2e. load of a folder that does not exist.
    script_case("load-missing-folder",
                [f'load "{run_dir / "fixtures" / "nope-L"}" "{run_dir / "fixtures" / "nope-R"}"',
                 "expand all",
                 'folder-report layout:xml output-to:"%3"'],
                str(L), str(R))

    # 2f. folder-report with no preceding load (the historically-observed 106).
    script_case("folder-report-no-load",
                ['folder-report layout:xml output-to:"%3"'], str(L), str(R))

    # 2g. text-report naming files that do not exist.
    script_case("text-report-missing-files",
                ['text-report layout:xml output-to:"%3" "%1" "%2"'],
                str(run_dir / "fixtures" / "nope1.txt"),
                str(run_dir / "fixtures" / "nope2.txt"))

    # 2h. A syntactically broken report command (unclosed quote).
    script_case("unclosed-quote",
                ['text-report layout:xml output-to:"%3 "%1" "%2"'],
                str(L), str(R))

    # ---------------------------------------------------------------
    # 3. /qc quick-compare levels (documented 1/2/11/12/13).
    # ---------------------------------------------------------------
    same_size = run_dir / "fixtures" / "same-size.bin"
    diff_size = run_dir / "fixtures" / "diff-size.bin"
    same_size.write_bytes(b"0123456789")
    diff_size.write_bytes(b"0123456789" + b"\x00" * 32)
    same_text = run_dir / "fixtures" / "same-text.txt"
    same_text.write_bytes(b"alpha\nbeta\n")

    qc_cases = [
        ("qc-crc-same", "crc", str(L), str(same_text)),
        ("qc-crc-diff", "crc", str(L), str(R)),
        ("qc-size-same", "size", str(same_size), str(same_size)),
        ("qc-size-diff", "size", str(same_size), str(diff_size)),
        ("qc-binary-same", "binary", str(L), str(same_text)),
        ("qc-binary-diff", "binary", str(L), str(R)),
        ("qc-rules-same", None, str(L), str(same_text)),
        ("qc-rules-diff", None, str(L), str(R)),
    ]
    for tag, kind, left, right in qc_cases:
        flag = f"/qc={kind}" if kind else "/qc"
        code, err = run_raw(inst.oracle_path, [flag, left, right])
        records.append({"tag": tag, "kind": "qc", "flag": flag, "exit": code,
                        "stderr": err.strip()[:200]})
        print(f"  {tag:<28} exit={code}")

    (run_dir / "u5-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5-results.json'}")

    # Compact summary of the observed code -> class mapping.
    print("\nexit code histogram:")
    hist: dict[int, list[str]] = {}
    for r in records:
        hist.setdefault(r["exit"], []).append(r["tag"])
    for code in sorted(hist):
        print(f"  {code:>4}: {', '.join(hist[code])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
