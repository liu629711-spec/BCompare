#!/usr/bin/env python3
"""M6.4 table goldens: build the verify/table golden tree from the measured
discriminating cells of the m60-m65 probe archive (task M6.4-a).

Every fixture below reproduces an OBSERVED probe case; the script re-runs it
serially against the current install (same in-place / Job-Object discipline
as every Oracle call), writes the fixture pair and the Oracle report into
``D:\\Rea\\verify\\table\\``, and APPENDS the manifest entries (append-only,
like the anchor manifest; a key clash aborts and a manifest snapshot lands in
the run directory).

The cells cover the discriminating surface of docs/13:
frame+markers, tie direction, gap zip, duplicates, quoted-newline rows,
ragged columns, numeric alignment (sbs rjust + interleaved 2-digit fields),
summary counting, EOF phantom rows, the 3-letter column floor (AA/AB),
auto-detect (tab, priority, rawline fallback) and the title replacement.

Space-split cells (S4/SP6-SP9) are deliberately EXCLUDED: acceptance is a
recorded residual (docs/13 §7); a golden would freeze an unresolved rule.

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m64_add_table_goldens.py
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


def C(*rows):
    return "".join(r + "\n" for r in rows)


#: (name, ext, layout, left text, right text, note, title)
CASES = [
    ("t-sbs-changed", "csv", "side-by-side",
     C("h,1", "banana,5", "c,3"), C("h,1", "cherry,2", "c,3"),
     "T1 lineage: header + one changed row pair, `=`/`<>` markers", None),
    ("t-int-changed", "csv", "interleaved",
     C("h,1", "banana,5", "c,3"), C("h,1", "cherry,2", "c,3"),
     "same pair on interleaved: `<>` pair shares ONE block", None),
    ("t-summary-mixed", "csv", "summary",
     C("a,1", "b,2", "zz,9"), C("a,1", "b,2", "q,7", "z,9"),
     "E/F lineage: 2 same + 1 important difference + 1 important right orphan", None),
    ("t-swap-tie", "csv", "side-by-side",
     C("k1,a", "k2,b", "k3,c", "k4,d"), C("k1,a", "k2,b", "k4,d", "k3,c"),
     "T13 tie direction: k3+- / k4= / -+k3 (anchor at EARLIER right index)", None),
    ("t-dups-positional", "csv", "side-by-side",
     C("k,v", "r,1", "r,1", "r,1", "z,9"), C("k,v", "r,1", "r,1", "z,9"),
     "T14 duplicates consume positionally: two `=` then one `+-`", None),
    ("t-zip-gap", "csv", "side-by-side",
     C("aaa,1", "zz,9"), C("bbb,2", "qq,8"),
     "P1: 2x2 all-different gap zips to two `<>`, never four orphans", None),
    ("t-quoted-newline", "csv", "interleaved",
     C('k,"x\ny",2', "b,3"), C('k,"x\ny",2', "b,4"),
     "T21: quoted embedded newline is ONE row; NUL in the display cell", None),
    ("t-ragged-cols", "csv", "side-by-side",
     C("a,1", "b,2"), C("a,1,x", "b,2"),
     "T18: global column count from the wider side; empty column on the left", None),
    ("t-nums-sbs", "csv", "side-by-side",
     C("h,1", "a1,2", "a2,10", "a3,9"), C("h,1", "a1,2", "a2,10", "a3,99"),
     "W1/W3: numeric cells right-justified per-side (widths from that side)", None),
    ("t-nums-int2digit", "csv", "interleaved",
     C(*[f"a{i},{i}" for i in range(1, 13)]),
     C(*[f"a{i},{i}" for i in range(1, 13)], "x,13"),
     "W3: interleaved number fields rjust to the digit width of the last row", None),
    ("t-eof-phantom", "csv", "side-by-side",
     C("a,1", "b,2"), "a,1\nb,2\n\n",
     "m64 E1: a blank line before EOF is a real right-orphan row on the right", None),
    ("t-letters-aa", "csv", "side-by-side",
     C(",".join(["h"] * 29), ",".join(["x"] * 29)),
     C(",".join(["h"] * 29), ",".join(["y"] * 28 + ["z"])),
     "m64c2 C2: 29 single-char columns; letters A..Z,AA,AB,AC set width floors", None),
    ("t-detect-tab", "txt", "side-by-side",
     C("a\tb", "c\td"), C("a\tb", "c\tdX"),
     "D6: non-.csv auto-detects the tab delimiter", None),
    ("t-detect-prio", "txt", "side-by-side",
     C("a\tb,c", "d\te,f"), C("a\tb,c", "d\te,X"),
     "G-tc: comma beats tab in the priority chain", None),
    ("t-rawline", "txt", "side-by-side",
     C("hello", "world"), C("hello", "warld"),
     "S1: no candidate outside quotes -> rawline fallback, one cell per line", None),
    ("t-title", "csv", "summary",
     C("a,1"), C("b,1"),
     "X4: title:\"MyTitle\" REPLACES the frame's first line", "MyTitle"),
]


def main() -> int:
    tree = REA / "verify" / "table"
    tree.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m64-table-goldens-{stamp}"
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
    for name, ext, layout, left_t, right_t, note, title in CASES:
        key = name
        left = tree / f"{key}-L.{ext}"
        right = tree / f"{key}-R.{ext}"
        left.write_text(left_t, encoding="utf-8", newline="")
        right.write_text(right_t, encoding="utf-8", newline="")
        report = tree / f"{key}.txt"
        script_text = orc.table_script(layout, title)
        sp = orc.write_script(run_dir / f"{key}.bcs", [script_text])
        run = orc.run(cur.oracle_path, sp, left, right, report,
                      timeout=120.0, script_text=script_text)
        if run.exit_code != 0 or not run.report_exists:
            raise SystemExit(f"{key}: oracle exit {run.exit_code}, "
                             f"report={run.report_exists}")
        manifest[key] = {
            "layout": layout,
            "ext": ext,
            "title": title,
            "note": note,
            "exit_code": run.exit_code,
            "bytes": report.stat().st_size,
            "report": str(report),
        }
        added += 1
        print(f"  {key:<22} [{layout}] exit={run.exit_code} "
              f"bytes={report.stat().st_size}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"manifest: +{added} table goldens -> {len(manifest)} total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
