#!/usr/bin/env python3
"""U5j probe -- directory STATUS when the subtree is not expanded.

U5g showed that `expand` changes a directory row's `<size>`; the M4 interpreter
must therefore build the tree with an expand policy.  That immediately raises
the question the current `dir` engine cannot answer, because it always recurses:
**what status does BC report for a directory whose contents it has not read?**

Three candidate models:
  H1  status comes from the unexpanded directory's own size/timestamp
  H2  status is always `same` when unexpanded (contents unknown)
  H3  status comes from a shallow (one-level) comparison

The models are separated by making the two sides' *subdirectory contents* differ
while the directories' own metadata is either equal (H1/H2 disagree) or the
size aggregate differs (H1 fires).

Also measured, because the M4 tree change touches them:
  * an unexpanded directory that exists on ONE side only
  * an unexpanded file-vs-dir kind conflict
  * whether `expand "A"` gives A a status even though A's own size is empty

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5j_unexpanded_dir_status.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

FIXED = 1_767_225_600


def rows_of(body: str) -> list[dict]:
    """Ordered rows with depth, kind, status, name, size."""
    rows: list[dict] = []
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
                   "depth": depth, "name": None, "size": None, "seen": False}
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
    return rows


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5j-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"

    # --- tree A: differing CONTENT inside a subdir, identical dir metadata ----
    # Both sides' subdirs are given the same mtime, but their files differ in
    # size, so a shallow size aggregate would fire while own-metadata would not.
    for side, blob in (("L", b"AAAA\n"), ("R", b"BBBBBBBB\n")):
        (fx / "A" / side / "d").mkdir(parents=True, exist_ok=True)
        (fx / "A" / side / "d" / "in.txt").write_bytes(blob)
        (fx / "A" / side / "top.txt").write_bytes(b"top\n")
    # --- tree B: one-sided directory, unexpanded -----------------------------
    (fx / "B" / "L" / "onlyL").mkdir(parents=True, exist_ok=True)
    (fx / "B" / "L" / "onlyL" / "x.txt").write_bytes(b"x\n")
    (fx / "B" / "R").mkdir(parents=True, exist_ok=True)
    # --- tree C: file-vs-dir kind conflict, unexpanded ----------------------
    (fx / "C" / "L").mkdir(parents=True, exist_ok=True)
    (fx / "C" / "R").mkdir(parents=True, exist_ok=True)
    (fx / "C" / "L" / "thing").mkdir(parents=True, exist_ok=True)
    (fx / "C" / "L" / "thing" / "inside.txt").write_bytes(b"inside\n")
    (fx / "C" / "R" / "thing").write_bytes(b"i am a file\n")
    # --- tree D: newer subdir content, same dir mtime -----------------------
    for side, ts in (("L", FIXED), ("R", FIXED + 7200)):
        (fx / "D" / side / "d").mkdir(parents=True, exist_ok=True)
        (fx / "D" / side / "d" / "in.txt").write_bytes(b"same\n")
        os.utime(fx / "D" / side / "d" / "in.txt", (ts, ts))
    for p in fx.rglob("*"):
        try:
            os.utime(p, (FIXED, FIXED))
        except OSError:
            pass
    # Re-apply D's inner timestamps (the loop above reset them).
    for side, ts in (("L", FIXED), ("R", FIXED + 7200)):
        os.utime(fx / "D" / side / "d" / "in.txt", (ts, ts))

    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records: list[dict] = []

    def case(tag: str, tree: str, lines_after_load: list[str]) -> dict:
        L, R = fx / tree / "L", fx / tree / "R"
        lines = [f'load "{L}" "{R}"', *lines_after_load,
                 'folder-report layout:xml output-to:"%3"']
        out = run_dir / "reports" / f"{tag}.xml"
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(L), str(R), out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        rows = rows_of(body)
        rec = {"tag": tag, "tree": tree, "script": lines, "exit": run.exit_code,
               "rows": rows, "report_body": body}
        records.append(rec)
        desc = " | ".join(
            f"{'  ' * r['depth']}{r['kind'][:4]}:{r['name']}={r['size']}"
            f"{'#' + r['status'] if r['status'] else ''}" for r in rows)
        print(f"  {tag:<26} exit={run.exit_code:<4} {desc}")
        return rec

    # A: does an unexpanded subdir see its content difference?
    case("A-noexpand", "A", [])
    case("A-expandall", "A", ["expand all"])
    case("A-expand-d", "A", ['expand "d"'])
    # B: one-sided unexpanded directory
    case("B-noexpand", "B", [])
    case("B-expandall", "B", ["expand all"])
    # C: file-vs-dir conflict unexpanded
    case("C-noexpand", "C", [])
    case("C-expandall", "C", ["expand all"])
    # D: newer inner file, same dir mtime
    case("D-noexpand", "D", [])
    case("D-expandall", "D", ["expand all"])

    (run_dir / "u5j-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5j-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
