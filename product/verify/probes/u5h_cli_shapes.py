#!/usr/bin/env python3
"""U5h probe -- bare command-line shapes and the remaining filter rule.

M4.1 requires BC-compatible command lines (two files / two folders / three
files).  For a headless tool the question is what BComp.com itself *returns*
for those shapes under /silent, since M4 must not invent behaviour it cannot
reproduce.  Short timeouts are used: if a shape would open a view and wait, the
Job Object reclaims it instead of leaving a GUI host behind.

Also settled here: `filter "-A\\"` (a folder-mask exclusion) with `expand all`,
which the help text says prevents excluded subfolders from being expanded --
the one filter rule u5d could not separate.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5h_cli_shapes.py
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


def run_raw(oracle, args: list[str], *, timeout: float) -> tuple[int, str, bool]:
    cmd = [str(oracle), *args]
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
            return proc.returncode, raw_err.decode("utf-8", errors="replace")[:300], False
        except subprocess.TimeoutExpired:
            tree.kill_tree()
            proc.kill()
            try:
                raw_out, raw_err = proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                raw_out, raw_err = b"", b""
            return -1, raw_err.decode("utf-8", errors="replace")[:300], True


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5h-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    (fx / "Ldir" / "A" / "B").mkdir(parents=True, exist_ok=True)
    (fx / "Rdir" / "A" / "B").mkdir(parents=True, exist_ok=True)
    for side in ("Ldir", "Rdir"):
        (fx / side / "A" / "B" / "f.txt").write_bytes(b"fffff\n")
        (fx / side / "A" / "g.txt").write_bytes(b"ggg\n")
        (fx / side / "h.txt").write_bytes(b"hhhh\n")
    lf, rf = fx / "file-L.txt", fx / "file-R.txt"
    lf.write_bytes(b"alpha\nbeta\n")
    rf.write_bytes(b"alpha\nGAMMA\n")
    third = fx / "file-C.txt"
    third.write_bytes(b"alpha\nCENTER\n")
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records: list[dict] = []

    # ---- Bare command-line shapes -------------------------------------
    shapes = [
        ("two-files", ["/silent", str(lf), str(rf)]),
        ("two-files-same", ["/silent", str(lf), str(lf)]),
        ("two-folders", ["/silent", str(fx / "Ldir"), str(fx / "Rdir")]),
        ("three-files", ["/silent", str(lf), str(rf), str(third)]),
        ("no-args", ["/silent"]),
        ("unknown-switch", ["/silent", "/frobnicate", str(lf), str(rf)]),
    ]
    for tag, args in shapes:
        code, err, timed_out = run_raw(inst.oracle_path, args, timeout=40.0)
        rec = {"tag": tag, "kind": "cli", "argv": args, "exit": code,
               "timed_out": timed_out, "stderr": err.strip()}
        records.append(rec)
        print(f"  {tag:<18} exit={code}{' TIMEOUT' if timed_out else ''}"
              + (f" stderr={err.strip()[:80]!r}" if err.strip() else ""))

    # ---- Filter: folder-mask exclusion + expand ------------------------
    def script_case(tag: str, lines: list[str]) -> dict:
        out = run_dir / "reports" / f"{tag}.xml"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(fx / "Ldir"), str(fx / "Rdir"),
                      out, timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        rows = []
        depth = 0
        cur = None
        for raw in body.splitlines():
            s = raw.strip()
            if s.startswith("<foldercomp") or s.startswith("<filecomp"):
                if cur:
                    rows.append(cur)
                kind = "folder" if s.startswith("<foldercomp") else "file"
                m = re.search(r'status="([a-z]+)"', s)
                cur = {"kind": kind, "status": m.group(1) if m else None,
                       "depth": depth, "name": None, "size": None,
                       "seen": False}
                continue
            if s.startswith("</foldercomp") or s.startswith("</filecomp"):
                if cur:
                    rows.append(cur)
                    cur = None
                depth -= 1
                continue
            if cur is not None:
                if s.startswith("<name>") and not cur["seen"]:
                    cur["name"] = s[6:-7]
                    cur["seen"] = True
                elif s.startswith("<size") and cur["size"] is None:
                    cur["size"] = "EMPTY" if s == "<size/>" else s[6:-7]
        if cur:
            rows.append(cur)
        rec = {"tag": tag, "kind": "script", "script": lines,
               "exit": run.exit_code, "report_bytes": run.report_bytes,
               "rows": rows, "report_body": body}
        records.append(rec)
        desc = " | ".join(f"{'  ' * r['depth']}{r['kind'][:4]}:{r['name']}={r['size']}"
                          for r in rows)
        print(f"  {tag:<22} exit={run.exit_code:<4} {desc}")
        return rec

    script_case("fg-exclude-A-expandall",
                [f'load "{fx / "Ldir"}" "{fx / "Rdir"}"', 'filter "-A\\\\"',
                 "expand all", 'folder-report layout:xml output-to:"%3"'])
    script_case("fg-exclude-A-noexp",
                [f'load "{fx / "Ldir"}" "{fx / "Rdir"}"', 'filter "-A\\\\"',
                 'folder-report layout:xml output-to:"%3"'])
    script_case("expand-trailing-sep",
                [f'load "{fx / "Ldir"}" "{fx / "Rdir"}"', 'expand "A\\\\"',
                 'folder-report layout:xml output-to:"%3"'])
    script_case("expand-forward-slash",
                [f'load "{fx / "Ldir"}" "{fx / "Rdir"}"', 'expand "A/B"',
                 'folder-report layout:xml output-to:"%3"'])
    script_case("expand-a-file",
                [f'load "{fx / "Ldir"}" "{fx / "Rdir"}"', 'expand "h.txt"',
                 'folder-report layout:xml output-to:"%3"'])

    (run_dir / "u5h-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5h-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
