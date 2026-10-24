#!/usr/bin/env python3
"""M6.4 batch-c: residual discriminators the M6.2/6.3 archive does not settle.

Three recorded residuals from docs/13 (S5/S6), one clean fixture each, plus
the frame-level questions the body-only replay could never see:

  N1  interleaved row-number fields with >=100 rows (3-digit widths; W3 only
      reached 13).  L = rows 1..102, R = same with row 100 changed.
      Does the numeric field width grow to the 3-digit max on each side?
  C1  >26 columns: a 28-column header pair (only the last column differs).
      What letters follow Z?  (The Rust renderer puts '#' past 26 and records
      it as a residual; the Oracle decides.)
  E1  EOF blank-line counting: right side ends `b,2\n\n` -- does BC count a
      trailing empty record as a row (W4 suggested yes) and what does the
      left side's `a,1\nb,2\n` do when the right gains the phantom row?
  E2  double trailing newline `b,2\n\n\n` -- one phantom row or two?

Archived WITH FRAMES (exit + raw bytes); replay_m64.py then diffs the product
frame-for-frame with the Produced: stamp folded -- the frame is now part of
the acceptance surface (the dash/slash misread was invisible to body replay).

Usage (serial, after every other Oracle run is finished):
  cd D:\\Rea\\product\\verify && python probes/m64_residual_probe.py
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


def rows102():
    return C(*[f"a{i},{i}" for i in range(1, 103)])


def rows102_changed():
    out = [f"a{i},{i}" for i in range(1, 103)]
    out[99] = "zz,100"          # row 100 (0-based 99) differs
    return C(*out)


HEADER28 = ",".join(f"c{i}" for i in range(1, 29))
ROW28_L = ",".join(str(i) for i in range(1, 29))
ROW28_R = ",".join(str(i) for i in range(1, 28)) + ",99"

CASES = [
    # (tag, left, right, layouts)
    ("N1-3digit",  rows102(), rows102_changed(), ("side-by-side", "interleaved")),
    ("C1-28col",   C(HEADER28, ROW28_L), C(HEADER28, ROW28_R),
     ("side-by-side", "interleaved")),
    ("E1-eof-1",   C("a,1", "b,2"), "a,1\nb,2\n\n", ("side-by-side", "interleaved")),
    ("E2-eof-2",   C("a,1", "b,2"), "a,1\nb,2\n\n\n", ("side-by-side", "interleaved")),
    ("E3-eof-both", "a,1\nb,2\n\n", "a,1\nb,2\n\n", ("side-by-side", "interleaved")),
]


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m64-residual-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, left, right, lays in CASES:
        lp = fx / f"{tag}-L.csv"; rp = fx / f"{tag}-R.csv"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "left": left, "right": right, "reports": {}}
        for lay in lays:
            lines = [f'data-report layout:{lay} output-to:"%3" "%1" "%2"']
            script = orc.write_script(run_dir / "reports" / f"{tag}.{lay}.bcs", lines)
            out = run_dir / "reports" / f"{tag}.{lay}.out"
            run = orc.run(inst.oracle_path, script, str(lp.resolve()),
                          str(rp.resolve()), str(out.resolve()),
                          timeout=180.0, script_text=lines[0])
            body = out.read_bytes() if out.exists() else b""
            rec["reports"][lay] = {"exit": run.exit_code,
                                   "bytes": len(body),
                                   "sha256": __import__("hashlib").sha256(body).hexdigest()}
        results.append(rec)
        print(f"{tag}: " + " ".join(f"[{k}] exit={v['exit']} bytes={v['bytes']}"
                                    for k, v in rec["reports"].items()))

    (run_dir / "m64-residual.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
