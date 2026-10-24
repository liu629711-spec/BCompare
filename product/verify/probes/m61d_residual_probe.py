#!/usr/bin/env python3
"""M6.1 batch-4 residuals: empty cell, comma+tab priority, right-orphan
accounting wording, blank-row importance.  Side-by-side + summary each.

  F1  empty middle cell               F2  both , and \\t present (priority?)
  F3  right-only orphan (wording)     F4  blank row between data rows

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m61d_residual_probe.py
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
    ("F1-empty", C("a,,c", "x,y"),      C("a,b,c", "x,y")),
    ("F2-mix",   C("a,b\tc", "d,e\tf"), C("a,b\tc", "d,X\tf")),
    ("F3-rorph", C("h,1", "z,4"),       C("h,1", "q,9", "z,4")),
    ("F4-blank", C("h,1", "", "b,2"),   C("h,1", "", "b,9")),
]

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m61d-residual-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, left, right in CASES:
        lp = fx / f"{tag}-L.csv"; rp = fx / f"{tag}-R.csv"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "left": left, "right": right, "reports": {}}
        for lay in ("side-by-side", "summary"):
            lines = [f'data-report layout:{lay} output-to:"%3" "%1" "%2"']
            script = orc.write_script(run_dir / "reports" / f"{tag}.{lay}.bcs", lines)
            out = run_dir / "reports" / f"{tag}.{lay}.out"
            run = orc.run(inst.oracle_path, script, str(lp.resolve()),
                          str(rp.resolve()), str(out.resolve()),
                          timeout=120.0, script_text=lines[0])
            body = out.read_text(encoding="utf-8-sig", errors="replace") if out.exists() else ""
            rec["reports"][lay] = {"exit": run.exit_code, "body": body}
        results.append(rec)
        print("="*16, tag)
        for k in ("side-by-side", "summary"):
            v = rec["reports"][k]
            body = v["body"]
            tail = body[body.find("A"):] if k == "side-by-side" else body.splitlines()[-3:]
            print(f"-- {k} exit={v['exit']}")
            if k == "side-by-side":
                print(tail)
            else:
                print("\n".join(tail))
        print()

    (run_dir / "m61d-residual.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
