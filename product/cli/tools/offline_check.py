#!/usr/bin/env python3
"""Offline (no-Oracle) acceptance check for the A-2 product binary.

Compares ``reacmp.exe`` against the stored golden corpora:

* ``verify/golden/manifest.json``  45 anchors -> status-sequence parity
  plus normalized-XML parity,
* ``verify/layouts/manifest.json`` 30 layouts -> normalized text parity.

This check NEVER invokes BCompare; the live-Oracle gate is run separately
and serially by the project lead.  ``harness.normalize`` is imported
read-only (sys.path) so the numbers here use the same rule-set (norm-1) as
the official harness and are directly comparable to its reports.

Usage:
    cd D:\\Rea\\product\\cli
    python tools/offline_check.py
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import normalize as norm  # noqa: E402  (read-only import)

EXE = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
WORK = REA / "product" / "cli" / "target" / "offline-check"
OPT_RE = re.compile(r"options:([a-z\-]+)")


def run_engine(left, right, out, *, opt=None, layout=None) -> tuple[int, str]:
    argv = [str(EXE), str(left), str(right), str(out)]
    if opt:
        argv.append(f"--opt={opt}")
    if layout:
        argv.append(f"--layout={layout}")
    p = subprocess.run(argv, capture_output=True)
    return p.returncode, p.stderr.decode("utf-8", errors="replace").strip()


def read_text(path) -> str:
    return pathlib.Path(path).read_bytes().decode("utf-8-sig", errors="replace")


def main() -> int:
    if not EXE.exists():
        raise SystemExit(f"binary not found: {EXE} (run `cargo build --release` in product/cli)")
    WORK.mkdir(parents=True, exist_ok=True)

    anchor_fail: list[str] = []
    xml_fail: list[str] = []
    layout_fail: list[str] = []

    # ---- 45 anchors: status-sequence parity + normalized XML parity ----
    golden = json.loads((REA / "verify/golden/manifest.json").read_text(encoding="utf-8"))
    for cid, entry in golden.items():
        out = WORK / f"{cid}.xml"
        m = OPT_RE.search(entry.get("note", ""))
        code, err = run_engine(entry["left"], entry["right"], out,
                               opt=m.group(1) if m else None)
        if code != entry["exit_code"]:
            anchor_fail.append(f"{cid}: exit {code} != {entry['exit_code']} {err[:120]}")
            continue
        got = re.findall(r'<linecomp status="([a-z]+)"', read_text(out))
        if got != entry["statuses"]:
            anchor_fail.append(
                f"{cid}: statuses {got} != {entry['statuses']}")
            continue
        want = norm.normalize(read_text(entry["report"])).text
        have = norm.normalize(read_text(out)).text
        if have != want:
            xml_fail.append(f"{cid}: normalized XML differs")

    # ---- 30 layouts: normalized text parity ----
    layouts = json.loads((REA / "verify/layouts/manifest.json").read_text(encoding="utf-8"))
    for cid, entry in layouts.items():
        case = entry["case"]
        ext = entry.get("ext", "txt")
        left = REA / "verify" / "layouts" / f"{case}-L.{ext}"
        right = REA / "verify" / "layouts" / f"{case}-R.{ext}"
        out = WORK / f"{cid}.txt"
        code, err = run_engine(left, right, out, layout=entry["layout"])
        if code != entry["exit_code"]:
            layout_fail.append(f"{cid}: exit {code} != {entry['exit_code']} {err[:120]}")
            continue
        want = norm.normalize(read_text(entry["report"])).text
        have = norm.normalize(read_text(out)).text
        if have != want:
            layout_fail.append(f"{cid}: normalized layout differs")

    n_anchor = len(golden)
    n_layout = len(layouts)
    print("=" * 70)
    print(f"anchors          {n_anchor - len(anchor_fail)}/{n_anchor} status-sequence parity")
    print(f"xml (normalized) {n_anchor - len(anchor_fail) - len(xml_fail)}/{n_anchor} parity")
    print(f"layouts          {n_layout - len(layout_fail)}/{n_layout} normalized parity")
    for f in anchor_fail:
        print(f"  ANCHOR-FAIL {f}")
    for f in xml_fail:
        print(f"  XML-DIFF    {f}")
    for f in layout_fail:
        print(f"  LAYOUT-FAIL {f}")
    print("=" * 70)
    ok = (not anchor_fail) and len(layout_fail) <= 1 and n_layout - len(layout_fail) >= 29
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
