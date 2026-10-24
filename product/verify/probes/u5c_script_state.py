#!/usr/bin/env python3
"""U5c probe -- the script state machine and `filter`, before M4 is split up.

U5/U5b settled the exit-code table.  What is still unmeasured is the behaviour
that decides how M4's script interpreter is built:

  1. `criteria <bogus-token>` -- parse error at criteria level: which code?
  2. `filter "*.txt"` -- does the name filter actually remove rows from
     `folder-report layout:xml`, or is it only a view setting?
  3. `filter "-*.txt"` (exclusion) and `filter "sub\\"` (folder-only mask).
  4. `load` given two *files* instead of folders -- the unified entry point
     wants to dispatch on file-vs-folder after `load`, so this must be known.
  5. `load` a folder pair, then `text-report` -- is that a syntax error?
  6. Two report commands in one script (does state persist / is the first
     report overwritten?).
  7. `log normal "<path>"` -- where does the log land, and does it exist?

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5c_script_state.py
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5c-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    (fx / "L" / "sub").mkdir(parents=True, exist_ok=True)
    (fx / "R" / "sub").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    # A tree with two extensions and a subfolder holding the same two.
    for side, tag in (("L", "L"), ("R", "R")):
        (fx / side / "a.txt").write_bytes(b"alpha\n" + tag.encode() + b"\n")
        (fx / side / "b.log").write_bytes(b"log line\n" + tag.encode() + b"\n")
        (fx / side / "sub" / "c.txt").write_bytes(b"c\n" + tag.encode() + b"\n")
        (fx / side / "sub" / "d.log").write_bytes(b"d\n" + tag.encode() + b"\n")

    L, R = fx / "L", fx / "R"
    records: list[dict] = []

    def case(tag: str, lines: list[str], left=str(L), right=str(R),
             show: bool = False) -> dict:
        out = run_dir / "reports" / f"{tag}.out"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, left, right, out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        names = sorted(set(
            part for part in __import__("re").findall(r'<filecomp[^>]*>', body)
        ))
        rec = {"tag": tag, "script": lines, "exit": run.exit_code,
               "report_bytes": run.report_bytes,
               "filecomp_rows": len(__import__("re").findall(r'<filecomp', body)),
               "foldercomp_rows": len(__import__("re").findall(r'<foldercomp', body)),
               "names": names, "report_body": body[:2500] if show else body[:400]}
        records.append(rec)
        print(f"  {tag:<28} exit={run.exit_code:<4} bytes={run.report_bytes:<5} "
              f"filecomp={rec['filecomp_rows']} foldercomp={rec['foldercomp_rows']}")
        return rec

    base = [f'load "{L}" "{R}"', "expand all"]
    report = ['folder-report layout:xml output-to:"%3"']

    # 1. Bad criteria token.
    case("criteria-bogus", ["criteria bogus-token"] + base + report)
    # 2. Name filter include.
    r = case("filter-include-txt", ['filter "*.txt"'] + base + report)
    print("     rows:", r["names"])
    # 3. Name filter exclude.
    r = case("filter-exclude-txt", ['filter "-*.txt"'] + base + report)
    print("     rows:", r["names"])
    # 3b. Folder-only mask.
    r = case("filter-folder-mask", ['filter "sub\\\\"'] + base + report)
    print("     rows:", r["names"])
    # 3c. Empty-result filter.
    r = case("filter-match-nothing", ['filter "*.nomatch"'] + base + report)
    print("     rows:", r["names"])
    # 4. load two files.
    case("load-files-then-folder-report",
         [f'load "{fx}/L/a.txt" "{fx}/R/a.txt"', "expand all"] + report)
    # 5. load folders then text-report (no comparison args).
    case("load-folders-then-text-report",
         base + ['text-report layout:xml output-to:"%3"'])
    # 6. Two reports in one script.
    second = run_dir / "reports" / "second.out"
    case("two-reports", base + report + [
        f'folder-report layout:summary output-to:"{second.as_posix()}"'])
    print(f"     second report exists={second.exists()} "
          f"bytes={second.stat().st_size if second.exists() else 0}")
    records[-1]["second_report_bytes"] = (
        second.stat().st_size if second.exists() else None)
    # 7. log with an explicit path.
    log_path = run_dir / "reports" / "script.log"
    case("log-explicit", [f'log verbose "{log_path.as_posix()}"'] + base + report)
    print(f"     log exists={log_path.exists()} "
          f"bytes={log_path.stat().st_size if log_path.exists() else 0}")
    records[-1]["log_path"] = str(log_path)
    records[-1]["log_exists"] = log_path.exists()
    if log_path.exists():
        records[-1]["log_head"] = log_path.read_text(
            encoding="utf-8", errors="replace")[:600]

    (run_dir / "u5c-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5c-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
