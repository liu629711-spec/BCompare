#!/usr/bin/env python3
"""M6.2 batch-b: column-width / padding discriminators for the table report.

The 56 archived m60-m62 bodies pinned the core model (global column count =
max over sides with min-1 empty columns; per-side widths from that side only;
interleaved shared widths; sbs numeric rjust / interleaved numeric ljust;
header left block padded to the FULL left cell width + 4-space blank field;
every line end rstripped; '=' interleaved rows show BOTH row numbers).

Five behaviors the archive does NOT discriminate, one clean fixture each
(Serial Oracle; Chinese install; both layouts unless noted):

  W1  right-orphan ('-+') row when LEFT widths are WIDER than right widths
      (L 'wwww,1' vs R 'q,3','r,4'): is the blank left field built from the
      LEFT widths (forcing) or the RIGHT widths?  Also whether the right
      cells themselves are rendered at rw (plain) or padded up to lw.
  W2  mirror of W1: left orphan with wide right side ('+-' row rstripped,
      so only the <> row discriminates rw-vs-forced-lw on the right side).
  W3  interleaved row-number fields with >=10 rows both sides (2-digit
      rjust fields; '<>' pair numbering at two digits; orphan numbering).
  W4  BLANK right-orphan row ('\n\n' trailing empty record on one side):
      ws/lw-blank cells vs full rstrip of the line.
  W5  ragged orphan: right has 3-column rows plus a 2-column orphan row --
      empty trailing column rendering inside '-+' rows (both layouts).
  W7  mirror T18: LEFT has the extra column (L 'a,1,x' vs R 'a,1') -- right
      side renders the global column count with empty cells too?

Archived verbatim; replay_table.py picks the new run dir up automatically.

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m62b_width_probe.py
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

def rows12():
    return C(*[f"a{i},{i}" for i in range(1, 13)])

def rows13():
    return C(*[f"a{i},{i}" for i in range(1, 13)], "x,13")

CASES = [
    ("W1-rorph-wide-L", C("wwww,1"), C("q,3", "r,4")),
    ("W2-lorph-wide-R", C("q,3", "r,4"), C("wwww,1")),
    ("W3-2digit",       rows12(), rows13()),
    ("W4-blank-orph",   C("h,1", "", "b,2"), C("h,1", "", "b,2", "q,9", "")),
    ("W5-ragged-orph",  C("a,1"), C("a,1,xx", "yy,2,zz", "w,3")),
    ("W7-mirror-T18",   C("a,1,x"), C("a,1")),
]

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m62b-width-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, left, right in CASES:
        lp = fx / f"{tag}-L.csv"; rp = fx / f"{tag}-R.csv"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "left": left, "right": right, "reports": {}}
        for lay in ("side-by-side", "interleaved"):
            lines = [f'data-report layout:{lay} output-to:"%3" "%1" "%2"']
            script = orc.write_script(run_dir / "reports" / f"{tag}.{lay}.bcs", lines)
            out = run_dir / "reports" / f"{tag}.{lay}.out"
            run = orc.run(inst.oracle_path, script, str(lp.resolve()),
                          str(rp.resolve()), str(out.resolve()),
                          timeout=120.0, script_text=lines[0])
            body = out.read_text(encoding="utf-8-sig", errors="replace") if out.exists() else ""
            rec["reports"][lay] = {"exit": run.exit_code, "body": body}
        results.append(rec)
        for k, v in rec["reports"].items():
            print(f"{tag} [{k}] exit={v['exit']}")
            tail = v["body"][v["body"].find("模式"):] if "模式" in v["body"] else v["body"]
            for ln in tail.splitlines()[1:]:
                print("   ", repr(ln))
            print()
        print("-" * 50)

    (run_dir / "m62b-width.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
