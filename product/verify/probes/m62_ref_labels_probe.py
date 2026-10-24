#!/usr/bin/env python3
"""M6.2 prerequisite: capture ENGLISH table-report labels from the reference
install (5.2.6.32774) for label-corroboration, mirroring what the labels suite
does for text.

Fixture selection covers every wording the row-model corpus exercises:
  identical-only   -> same-row count wording
  changed pair     -> "difference row(s)" wording
  left orphan      -> "left orphan row(s)" wording
  right orphan     -> "right orphan row(s)" wording
  header + mixed   -> side-by-side/interleaved full bodies
Layouts: side-by-side + interleaved + summary each.

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m62_ref_labels_probe.py
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
    ("G1-ident",  C("h,1", "a,2"),        C("h,1", "a,2")),
    ("G2-chg",    C("h,1", "a,2"),        C("h,1", "a,9")),
    ("G3-lorph",  C("h,1", "a,2", "b,3"), C("h,1", "a,2")),
    ("G4-rorph",  C("h,1", "a,2"),        C("h,1", "a,2", "q,9")),
    ("G5-mixed",  C("h1,h2", "q,1", "r,2", "s,3"), C("h1,h2", "r,2", "q,9", "s,3", "t,4")),
]

def main() -> int:
    installs = inst_mod.discover()
    ref = installs["reference"]
    if not ref.enabled:
        raise SystemExit("reference install unavailable: " + (ref.disabled_reason or ""))
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m62-reflabels-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"reference: {ref.oracle_path} ({ref.app_version})\n")

    results = []
    for tag, left, right in CASES:
        lp = fx / f"{tag}-L.csv"; rp = fx / f"{tag}-R.csv"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "reports": {}}
        for lay in ("side-by-side", "interleaved", "summary"):
            lines = [f'data-report layout:{lay} output-to:"%3" "%1" "%2"']
            script = orc.write_script(run_dir / "reports" / f"{tag}.{lay}.bcs", lines)
            out = run_dir / "reports" / f"{tag}.{lay}.out"
            run = orc.run(ref.oracle_path, script, str(lp.resolve()),
                          str(rp.resolve()), str(out.resolve()),
                          timeout=120.0, script_text=lines[0])
            body = out.read_text(encoding="utf-8-sig", errors="replace") if out.exists() else ""
            rec["reports"][lay] = {"exit": run.exit_code, "body": body}
            print(f"-- {tag} [{lay}] exit={run.exit_code}")
            print(body)
        results.append(rec)
        print("=" * 60)

    (run_dir / "m62-reflabels.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
