#!/usr/bin/env python3
"""M6.1 batch-3: delimiter detection candidates, summary accounting, extension.

Open items from batch 2:
  * semicolon single-row did NOT split (T17), tab single-row DID split (P10a)
    -> is `;` off the candidate set, or does detection need >=2 rows?
  * does the .csv extension constrain the candidate set?
  * summary accounting: orphans count as rows? changed pairs as rows?

Cases (side-by-side + summary each):
  E1  multi-row semicolon .csv   E2  multi-row tab .csv
  E3  multi-row comma .tsv (mixed-extension: comma content in tsv name)
  E4  multi-row semicolon+comma mix (which wins when both present)
  E5  semicolon inside a quoted comma cell (context sensitivity)
  E6  3-row file, one changed pair + one orphan side (summary counts)
  E7  3-row file, two orphan left (deleted block summary count)

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m61c_detect_probe.py
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
    ("E1-semi2", ".csv", C("a;b;c", "d;e;f", "g;h;i"), C("a;b;c", "d;e;X", "g;h;i")),
    ("E2-tab2",  ".csv", C("a\tb\tc", "d\te\tf", "g\th\ti"), C("a\tb\tc", "d\te\tX", "g\th\ti")),
    ("E3-comma-tsv", ".tsv", C("a,b,c", "d,e,f"), C("a,b,c", "d,e,X")),
    ("E4-mix",   ".csv", C("a,b;c", "d,e;f"), C("a,b;c", "d,X;f")),
    ("E5-quote-semi", ".csv", C('a,"b;c",d', "e,f,g"), C('a,"b;c",d', "e,f,X")),
    ("E6-chg+orph", ".csv", C("h,1", "a,2", "b,3", "c,4"), C("h,1", "a,9", "b,3", "z,4")),
    ("E7-2del",  ".csv", C("h,1", "a,2", "b,3", "z,4"), C("h,1", "z,4")),
]

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m61c-detect-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, ext, left, right in CASES:
        lp = fx / f"{tag}-L{ext}"; rp = fx / f"{tag}-R{ext}"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "ext": ext, "left": left, "right": right, "reports": {}}
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
            tail = body[body.find("模式"):] if k == "side-by-side" else body[body.find("左边"):]
            print(f"-- {k} (exit {v['exit']})")
            print("\n".join(tail.splitlines()[1:]))
        print()

    (run_dir / "m61c-detect.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
