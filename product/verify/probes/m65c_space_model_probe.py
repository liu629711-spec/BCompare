#!/usr/bin/env python3
"""M6.4 batch-8 (m65c): the SPACE candidate's acceptance + cell model.

Hypothesis from m65/m65b: the space format splits only when the space-run
COLUMNS line up across every row (S4 splits: runs at col 1 in both rows;
SP1 rejects: col 1 vs col 2; W1/SP6-L reject double runs; SP3 rejects a row
without any space; Q1/SP4 reject when a run sits inside a qualified cell).
Cells KEEP the trailing spaces ('a b' -> 'a ' width 2, S4 header 'A  B').

Open questions, one .txt fixture each (side-by-side + interleaved for the
width-bearing ones):

  SP7  aligned multi-boundary: rows 'a b c' / 'd e f' (runs at cols 1,3) --
       three cells, each keeping its run?
  SP8  aligned DOUBLE run: 'a  b' / 'c  d' (both rows run at cols 1-2) --
       does an aligned double run split (SP6-L rejected one single vs one
       double = MISaligned), cell width includes the run?
  SP9  trailing space on one row only: 'a b' / 'c d ' -- reject (empty last
       cell) or split with row2 width 5?
  SP10 leading space: ' ab' / 'cd' -- empty first cell allowed?
  SP11 boundary inside ONE cell region: 'a b' / 'cc dd' (runs at col 1 vs
       col 2 -- misaligned by construction) -- expect reject (SP1 twin with
       both cells 2-wide).
  SP12 ragged runs: 'a b c' / 'd e' -- reject because row2 lacks a run?

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m65c_space_model_probe.py
"""
from __future__ import annotations
import hashlib, json, pathlib, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def C(*rows):
    return "".join(r + "\n" for r in rows)


CASES = [
    ("SP7",  C("a b c", "d e f"),   C("a b c", "d e X"), ("side-by-side",)),
    ("SP8",  C("a  b", "c  d"),     C("a  b", "c  X"),   ("side-by-side",)),
    ("SP9",  C("a b", "c d "),      C("a b", "c d"),     ("side-by-side",)),
    ("SP10", C(" ab", "cd"),        C(" ab", "cX"),      ("side-by-side",)),
    ("SP11", C("a b", "cc dd"),     C("a b", "cc dX"),   ("side-by-side",)),
    ("SP12", C("a b c", "d e"),     C("a b c", "d X"),   ("side-by-side",)),
]


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m65c-spacemodel-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, left, right, lays in CASES:
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "ext": ".txt", "left": left, "right": right, "reports": {}}
        for lay in lays:
            line = f'data-report layout:{lay} output-to:"%3" "%1" "%2"'
            script = orc.write_script(run_dir / "reports" / f"{tag}.{lay}.bcs", [line])
            out = run_dir / "reports" / f"{tag}.{lay}.out"
            r = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                        str(out.resolve()), timeout=120.0, script_text=line)
            body = out.read_bytes() if out.exists() else b""
            rec["reports"][lay] = {"exit": r.exit_code, "bytes": len(body),
                                   "sha256": hashlib.sha256(body).hexdigest()}
            print(f"{tag} [{lay}] exit={r.exit_code}")
            for ln in body.decode("utf-8-sig", errors="replace").splitlines()[6:]:
                if ln.strip():
                    print("   ", repr(ln))
        results.append(rec)

    (run_dir / "m65c-spacemodel.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
