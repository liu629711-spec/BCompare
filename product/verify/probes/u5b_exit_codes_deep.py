#!/usr/bin/env python3
"""U5b probe -- the two questions U5 left open.

U5 measured the three error classes (105 = script file unreadable, 106 = syntax,
107 = failed to load inputs) and three of the five /qc levels (1 same,
11 binary differences, 13 rules-based differences).  It also produced a result
that contradicts a comment in ``harness/oracle.py``: a bare ``folder-report``
with no ``load`` exited **0** and wrote a 155-byte report, while the harness
comment claims exit 106 and a 0-byte report.  This probe:

  1. dumps that 155-byte report, so the "empty folder comparison" shape is
     recorded rather than guessed;
  2. hunts the two unobserved /qc levels:
       - 2  "Rules-based same"  -- files that differ in bytes but match by rules
       - 12 "Similar"           -- files with unimportant differences only
     by trying the pairs most likely to produce them;
  3. checks whether other folder commands without a prior ``load`` also succeed
     (``expand all``, ``select all``), which decides how M4's state machine must
     behave when a script never loads anything.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5b_exit_codes_deep.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def run_raw(oracle, args: list[str], *, timeout: float = 120.0) -> tuple[int, str]:
    cmd = [str(oracle), "/silent", *args]
    with orc.ProcessTree() as tree:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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
    return code, raw_err.decode("utf-8", errors="replace")[:300]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5b-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    fx = run_dir / "fixtures"
    records: list[dict] = []

    def script_case(tag: str, lines: list[str], left: str, right: str) -> dict:
        out = run_dir / "reports" / f"{tag}.out"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, left, right, out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        rec = {"tag": tag, "kind": "script", "script": lines,
               "exit": run.exit_code, "report_bytes": run.report_bytes,
               "report_body": body[:1200]}
        records.append(rec)
        return rec

    # ------------------------------------------------------------------
    # 1. The 155-byte no-load folder report: record its exact shape.
    # ------------------------------------------------------------------
    rec = script_case("folder-report-no-load.xml",
                      ['folder-report layout:xml output-to:"%3"'],
                      str(fx / "unused-L"), str(fx / "unused-R"))
    print(f"[1] folder-report with no load: exit={rec['exit']} "
          f"bytes={rec['report_bytes']}")
    print("---- report body ----")
    print(rec["report_body"])
    print("---- end ----")

    # ------------------------------------------------------------------
    # 2. Other folder commands with no prior load.
    # ------------------------------------------------------------------
    for tag, lines in [
        ("expand-all-no-load", ["expand all",
                                'folder-report layout:xml output-to:"%3"']),
        ("select-all-no-load", ["select all",
                                'folder-report layout:xml output-to:"%3"']),
        ("log-then-report", ["log normal",
                             'folder-report layout:xml output-to:"%3"']),
        ("criteria-then-report", ["criteria size",
                                  'folder-report layout:xml output-to:"%3"']),
    ]:
        r = script_case(tag, lines, str(fx / "unused-L"), str(fx / "unused-R"))
        print(f"[2] {tag:<22} exit={r['exit']} bytes={r['report_bytes']}")

    # ------------------------------------------------------------------
    # 3. Hunting /qc level 2 (rules-based same) and 12 (Similar).
    #    Text pair whose bytes differ but whose *rules* verdict could be same:
    #      (a) whitespace-only difference  -> rules-based 'same', bytes differ
    #      (b) case-only difference        -> rules same, bytes differ
    #      (c) line-ending difference only -> rules same, bytes differ
    #      (d) comment-only difference     -> rules-based similar?
    # ------------------------------------------------------------------
    pairs = {
        "ws-only":    (b"alpha beta\n", b"alpha   beta\n"),
        "case-only":  (b"Alpha\n", b"alpha\n"),
        "crlf-only":  (b"alpha\nbeta\n", b"alpha\r\nbeta\r\n"),
        "comment-only": (b"int x; // one\n", b"int x; // two\n"),
        "identical":  (b"alpha\nbeta\n", b"alpha\nbeta\n"),
    }
    for name, (lb, rb) in pairs.items():
        lpath, rpath = fx / f"{name}-L.txt", fx / f"{name}-R.txt"
        lpath.write_bytes(lb)
        rpath.write_bytes(rb)
        for kind in [None, "crc", "binary"]:
            flag = f"/qc={kind}" if kind else "/qc"
            code, err = run_raw(inst.oracle_path, [flag, str(lpath), str(rpath)])
            rec = {"tag": f"qc-{kind or 'rules'}-{name}", "kind": "qc",
                   "flag": flag, "exit": code, "stderr": err.strip()[:200]}
            records.append(rec)
            print(f"[3] /qc={kind or 'rules':<6} {name:<13} exit={code}")

    # ------------------------------------------------------------------
    # 4. /qc on missing files (level 100-class errors).
    # ------------------------------------------------------------------
    code, err = run_raw(inst.oracle_path,
                        ["/qc", str(fx / "nope-a.txt"), str(fx / "nope-b.txt")])
    records.append({"tag": "qc-rules-missing", "kind": "qc", "flag": "/qc",
                    "exit": code, "stderr": err.strip()[:200]})
    print(f"[4] /qc missing files         exit={code}")

    (run_dir / "u5b-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5b-results.json'}")

    hist: dict[int, list[str]] = {}
    for r in records:
        hist.setdefault(r["exit"], []).append(r["tag"])
    print("\nexit code histogram:")
    for code in sorted(hist):
        print(f"  {code:>4}: {', '.join(hist[code])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
