#!/usr/bin/env python3
"""M7 hex goldens: build the verify/hex golden tree from the measured
discriminating cells of the m70-m70g archive (function 5, U5).

Every fixture below reproduces an OBSERVED probe case; the script re-runs
it serially against the current install (same in-place / Job-Object
discipline as every Oracle call), writes the fixture pair and the Oracle
report into ``D:\\Rea\\verify\\hex\\``, and APPENDS the manifest entries
(append-only; a key clash aborts and a manifest snapshot lands in the run
directory).

The cells cover the discriminating surface of docs/14: frame+cli surface
(106/107 classes are the CLI tests' job, not goldens here), slot geometry,
block breaks, marker widths, orphan columns, interleaved two-pass diff
ordering, 8-digit offsets past 0xFFFF, empty-side collapse, title, summary
count order/omission, empty-empty body.

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m71_add_hex_goldens.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def seq(n: int) -> bytes:
    return bytes(i & 0xFF for i in range(n))


L64 = seq(64)

#: (name, layout, left bytes, right bytes, note, title)
CASES = [
    ("h-sbs-equal", "side-by-side", L64, L64,
     "Y1: all-same report -> zone width 1 (` = ` once), single block rule", None),
    ("h-sbs-insert", "side-by-side", L64,
     bytes(L64[:4]) + b"\x41" + bytes(L64[4:]),
     "Y2: one inserted byte -> orphan slot keeps row positions; `<>` zone width 2", None),
    ("h-sbs-append", "side-by-side", L64[:24], L64,
     "Y3: right-only rows with a blank left column, `<>` once at the boundary", None),
    ("h-sbs-delete", "side-by-side", L64,
     bytes(L64[:16]) + bytes(L64[24:]),
     "Y4: left-only row; the block rule uses the GLOBAL max width (70)", None),
    ("h-sbs-many", "side-by-side",
     bytes(L64[:4]) + b"\xFF" + bytes(L64[5:12]) + b"\xFF" + bytes(L64[13:24]) + b"\xFF" + bytes(L64[25:]),
     L64,
     "Y5: marker text only on each block's FIRST row", None),
    ("h-int-insert", "interleaved", L64,
     bytes(L64[:4]) + b"\x41" + bytes(L64[4:]),
     "Y6: diff rows split per side; merged same rows carry both offsets", None),
    ("h-sum-diff", "summary", L64, bytes(L64[:4]) + b"\xFF" + bytes(L64[5:]),
     "Y7: same + difference lines only, in the measured order", None),
    ("h-int-title", "interleaved", None, None,
     "V3: interleaved title replaces frame line 1; the last block emits all "
     "left rows before the right line (V3 block ordering)", "HexIntTitle"),
    ("h-int-600", "interleaved", seq(600), bytes(seq(600)) + b"\xFF",
     "Z7: offsets stay 8 hex digits past 0xFFFF", None),
    ("h-sbs-600", "side-by-side", seq(600), seq(600)[:0x258] + b"\xFF" + seq(600)[0x259:],
     "Y12: 600-byte pair, first changed row at 0x258", None),
    ("h-sbs-empty-left", "side-by-side", b"", seq(16),
     "Y13: empty side collapses its column; ` <> ` then the right field", None),
    ("h-sbs-title", "side-by-side", L64, L64[:60],
     "Y11: title replaces frame line 1; a same+orphan leftover row is ONE block", "HexTitle"),
    ("h-sum-mixed", "summary", None, None,
     "V5: all four count categories (m70e2, both installs): 56/31/1/1", None),
]


def main() -> int:
    tree = REA / "verify" / "hex"
    tree.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m71-hex-goldens-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")

    man_path = tree / "manifest.json"
    manifest: dict = {}
    if man_path.exists():
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
        shutil.copy2(man_path, run_dir / "manifest.json.before")
    clash = [name for name, *_ in CASES if name in manifest]
    if clash:
        raise SystemExit(f"manifest already has keys: {clash}")

    added = 0
    for name, layout, left_t, right_t, note, title in CASES:
        # fixture bytes: shared V1 fixtures for the cells that reproduce them
        if left_t is None:
            left_t = seq(64) + seq(16)          # V1-L: 80 bytes
        if right_t is None:
            right_t = b"\xFF" + seq(59) + b"\x41"  # V1-R: 62 bytes
        left = tree / f"{name}-L.bin"
        right = tree / f"{name}-R.bin"
        left.write_bytes(left_t)
        right.write_bytes(right_t)
        report = tree / f"{name}.txt"
        script_text = orc.hex_script(layout, title)
        sp = orc.write_script(run_dir / f"{name}.bcs", [script_text])
        run = orc.run(cur.oracle_path, sp, left, right, report,
                      timeout=120.0, script_text=script_text)
        if run.exit_code != 0 or not run.report_exists:
            raise SystemExit(f"{name}: oracle exit {run.exit_code}, "
                             f"report={run.report_exists}")
        entry = {
            "layout": layout,
            "note": note,
            "exit_code": run.exit_code,
            "bytes": report.stat().st_size,
            "report": str(report),
        }
        if title:
            entry["title"] = title
        manifest[name] = entry
        added += 1
        print(f"  {name:<18} [{layout}] exit={run.exit_code} "
              f"bytes={report.stat().st_size}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"manifest: +{added} hex goldens -> {len(manifest)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
