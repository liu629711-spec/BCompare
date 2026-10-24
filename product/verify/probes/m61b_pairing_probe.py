#!/usr/bin/env python3
"""M6.1 batch-2: block pairing rule, alignment key, importance, options.

Batch 1 (m61-rowalign) established: row model (quoted-EOL cells are ONE row),
content alignment with LCS positional choice on dups, marks `=`/`<>`/`+-`/`-+`,
interleaved per-row numbering.  Open questions, one discriminator each:

  P1  2x2 zero-similarity block: closeness-pair or 4 orphans?
  P2  1x2 / 2x1 blocks: pairing shape under asymmetry
  P3  equal-after-decode, different raw (`k,"a b",1` vs `k,a b,1`): key = cell model or raw line?
  P4  interior/trailing whitespace inside cells: cell-wise importance?
  P5  anchored 1x1 middle block (a,1/b,2/c,3 vs a,1/x,9/c,3): `<>` pair?
  P6  options:display-mismatches on mixed file
  P7  options:display-matches
  P8  options:line-numbers on side-by-side
  P9  options:ignore-unimportant on whitespace-only cell diff
  P10 .tsv (tab) routing -- spec has NO TSV built-in; text or table?
  P11 empty cell diff (`a,,c` vs `a,b,c`)
  P12 3x3 block with one identical interior (LCS anchor inside block)

Serial Oracle; both side-by-side and interleaved unless the option is
layout-specific.  Archived verbatim.

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m61b_pairing_probe.py
"""
from __future__ import annotations
import json, pathlib, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

def C(*rows):
    return "".join(r + "\n" for r in rows)

CASES = [
    # tag, left, right, [ (layout, options) ... ]
    ("P1-2x2",  C("aaa,1", "zz,9"),  C("bbb,2", "qq,8"), None),
    ("P2-1x2",  C("x,1"),            C("y,2", "z,3"), None),
    ("P2-2x1",  C("x,1", "y,2"),     C("z,3"), None),
    ("P3-raw",  C('k,"a b",1'),      C("k,a b,1"), None),
    ("P4-ws",   C("k,a  b,1", "n,1 "), C("k,a b,1", "n,1"), None),
    ("P5-anchor", C("a,1", "b,2", "c,3"), C("a,1", "x,9", "c,3"), None),
    ("P6-dismis", C("k,1", "a,2", "b,3"), C("k,1", "a,9", "c,3"),
        [("side-by-side", "display-mismatches"), ("interleaved", "display-mismatches")]),
    ("P7-disma",  C("k,1", "a,2", "b,3"), C("k,1", "a,9", "c,3"),
        [("side-by-side", "display-matches")]),
    ("P8-lineno", C("k,1", "a,2", "b,3"), C("k,1", "a,9", "c,3"),
        [("side-by-side", "line-numbers")]),
    ("P9-iu",     C("k,a  b,1"), C("k,a b,1"),
        [("side-by-side", "ignore-unimportant")]),
    ("P12-3x3",   C("m,1", "a,2", "b,3", "n,4"), C("m,1", "a,2", "x,9", "b,3", "n,4"), None),
]

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m61b-pairing-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, left, right, variants in CASES:
        lays = variants or [("side-by-side", None), ("interleaved", None)]
        lp = fx / f"{tag}-L.csv"; rp = fx / f"{tag}-R.csv"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "left": left, "right": right, "reports": {}}
        for lay, opt in lays:
            o = f" options:{opt}" if opt else ""
            lines = [f'data-report layout:{lay}{o} output-to:"%3" "%1" "%2"']
            script = orc.write_script(run_dir / "reports" / f"{tag}.{lay}{o}.bcs", lines)
            out = run_dir / "reports" / f"{tag}.{lay}{o or ''}.out"
            run = orc.run(inst.oracle_path, script, str(lp.resolve()),
                          str(rp.resolve()), str(out.resolve()),
                          timeout=120.0, script_text=lines[0])
            body = out.read_text(encoding="utf-8-sig", errors="replace") if out.exists() else ""
            rec["reports"][f"{lay}{o}"] = {"exit": run.exit_code, "body": body}
        results.append(rec)
        for k, v in rec["reports"].items():
            print(f"{tag} [{k}] exit={v['exit']}")
            tail = v["body"][v["body"].find("模式"):]
            print("\n".join(tail.splitlines()[2:]))
            print()
        print("-" * 50)

    # P10: extension routing (.tsv tab file; also .txt with commas)
    p10 = []
    for name, content in [("P10a.tsv", "a\t1\nb\t2\n"), ("P10b.txt", "a,1\nb,2\n")]:
        lp = fx / name; rp = fx / ("R-" + name)
        left = content; right = content.replace("2", "9")
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        lines = ['data-report layout:side-by-side output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{name}.bcs", lines)
        out = run_dir / "reports" / f"{name}.out"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(out.resolve()), timeout=120.0, script_text=lines[0])
        body = out.read_text(encoding="utf-8-sig", errors="replace") if out.exists() else ""
        head = body.splitlines()[0] if body else ""
        p10.append({"name": name, "exit": run.exit_code, "first_line": head,
                    "is_table": "表格" in head})
        print(f"{name}: exit={run.exit_code} first_line={head!r}")
    results.append({"tag": "P10-routing", "reports": {}, "routing": p10})

    (run_dir / "m61b-pairing.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
