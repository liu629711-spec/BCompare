#!/usr/bin/env python3
"""M6.5 (m67): space-candidate attack round -- settle the cell model.

m65/m65b/m65c left the space candidate as a documented contradiction
(docs/13 7.4): S4 splits, SP1 does not, SP6/SP9 render byte-identical rows
as `<>`. The sbs report cannot arbitrate: its column padding overwrites the
cell bytes, so "what are the cells" is unreadable from it. The interleaved
layout DOES print each side's row verbatim with a row number and no column
padding, so every cell below runs BOTH layouts and interleaved is the
binding readout.

Open questions this batch pins (one .txt pair each, sbs + interleaved):

  H1  single row, one run: 'a b' vs 'a b' (identical file) --
      acceptance is about run ALIGNMENT across rows; a lone row aligns
      trivially. Interleaved shows 1 raw cell or 2 split cells.
  H2  single row, DOUBLE run: 'a  b' vs 'a  b' -- same but run width 2.
  H3  mixed run widths: 'a b' / 'c  d' vs itself (identical) --
      SP6-L had exactly this shape and looked un-splittable while SP6-R
      split; the same file compared with itself makes the cell dump the
      only evidence needed.
  H4  same tokens, different run widths on the two sides:
      'a b' / 'c d' vs 'a  b' / 'c  d' -- if both split, do the cells
      (which keep their runs, S4) compare `<>` or do the split cells get
      trimmed to `=`? Settles SP6's `<>`-on-identical rendering.
  H5  trailing space on one row: 'a b' / 'c d ' vs 'a b' / 'c X' --
      a run at the end-of-row boundary: empty trailing cell? SP9 twin
      that changes row 2 so the split decision shows up as a marker.
  H6  comma vs space priority inside one file: 'a b,c' / 'd e,f' vs
      'a,b c' / 'd,e f' -- the G-matrix only crossed {comma,tab,semi,
      pipe}; this puts space next to comma. Interleaved cells identify
      the winning delimiter directly.
  H7  row without a run: 'ab' / 'c d' vs 'ab' / 'c X' -- SP3 said reject;
      re-run with interleaved so the "rawline" verdict is directly read
      instead of inferred from header width.
  H8  control: aligned single runs 'a b' / 'c d' vs itself -- must show
      a space split in every archive reading; anchors the readout.

Usage (serial, install dir):  cd D:\\Rea\\product\\verify && python probes/m67_space_attack_probe.py
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
    ("H1", C("a b"),                  C("a b"),              "single row one run, identical"),
    ("H2", C("a  b"),                 C("a  b"),             "single row double run, identical"),
    ("H3", C("a b", "c  d"),          C("a b", "c  d"),      "mixed run widths, identical"),
    ("H4", C("a b", "c d"),           C("a  b", "c  d"),     "same tokens, run widths differ per side"),
    ("H5", C("a b", "c d "),          C("a b", "c X"),       "trailing space one row"),
    ("H6", C("a b,c", "d e,f"),       C("a,b c", "d,e f"),   "comma vs space priority"),
    ("H7", C("ab", "c d"),            C("ab", "c X"),        "row without a run (SP3 twin)"),
    ("H8", C("a b", "c d"),           C("a b", "c d"),       "control: aligned single runs identical"),
]

LAYOUTS = ("side-by-side", "interleaved")


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m67-spaceattack-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, left, right, note in CASES:
        lp = fx / f"{tag}-L.txt"; rp = fx / f"{tag}-R.txt"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        rec = {"tag": tag, "ext": ".txt", "note": note,
               "left": left, "right": right, "reports": {}}
        for lay in LAYOUTS:
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

    (run_dir / "m67-spaceattack.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
