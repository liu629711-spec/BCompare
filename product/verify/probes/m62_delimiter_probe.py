#!/usr/bin/env python3
"""M6.2 batch-5: pin the delimiter-detection rule before writing the parser.

Batch-3/4 evidence is contradictory under any single simple model:
  * `.csv` `a,b` splits to 2 cols; `.csv` `a\\tb` does NOT split (stays 1 col).
  * `.tsv` `a\\t1` splits to 2 cols; `.tsv` `a,b` splits to 2 cols (comma wins).
  * `.txt` `a,b` splits to 2 cols.
Spec built-ins: CSV -> DlmDelimiters "44" (comma only); MSEXCEL -> "9" (tab).
No TSV built-in.  So is detection (a) extension-conditional candidate sets,
(b) "try all candidates, pick the one with consistent/most columns", or
(c) declared comma with a tab fallback only when comma yields 1 column?

Each case reports the OBSERVED column count (via the side-by-side header `A
B C ...` letters).  A discriminator is designed so each hypothesis predicts a
DIFFERENT column count.

  D1  .csv  comma,            2 cols   (baseline comma works)
  D2  .csv  tab only, 2f      (hypothesis a/no: 1col ; b: 2col ; c: ? )
  D3  .csv  tab only, 3f
  D4  .csv  pipe only
  D5  .csv  comma+tab, comma 2f tab 3f   (which yields the table?)
  D6  .txt  tab only, 2f
  D7  .tsv  tab only, 3f
  D8  .tsv  comma only, 2f
  D9  .xyz  comma only (unknown extension)
  D10 .xyz  tab only
  D11 .csv  comma 2f + tab elsewhere (mixed density: does tab appear as a col?)
  D12 .csv  semicolon only, 2f (confirm semicolon NEVER a delimiter)

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m62_delimiter_probe.py
"""
from __future__ import annotations
import json, pathlib, re, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

def C(*rows):
    return "".join(r + "\n" for r in rows)

# (tag, extension, left, right)
CASES = [
    ("D1-csv-comma",  ".csv", C("a,b", "c,d"),        C("a,b", "c,X")),
    ("D2-csv-tab2",   ".csv", C("a\tb", "c\td"),       C("a\tb", "c\tX")),
    ("D3-csv-tab3",   ".csv", C("a\tb\tc", "d\te\tf"), C("a\tb\tc", "d\te\tX")),
    ("D4-csv-pipe",   ".csv", C("a|b", "c|d"),         C("a|b", "c|X")),
    ("D5-csv-ct",     ".csv", C("a,b\tc\td", "e,f\tg\th"), C("a,b\tc\td", "e,X\tg\th")),
    ("D6-txt-tab2",   ".txt", C("a\tb", "c\td"),       C("a\tb", "c\tX")),
    ("D7-tsv-tab3",   ".tsv", C("a\tb\tc", "d\te\tf"), C("a\tb\tc", "d\te\tX")),
    ("D8-tsv-comma",  ".tsv", C("a,b", "c,d"),         C("a,b", "c,X")),
    ("D9-xyz-comma",  ".xyz", C("a,b", "c,d"),         C("a,b", "c,X")),
    ("D10-xyz-tab",   ".xyz", C("a\tb", "c\td"),       C("a\tb", "c\tX")),
    ("D11-csv-mixed", ".csv", C("a,b\tc", "d,e"),      C("a,b\tc", "d,X")),
    ("D12-csv-semi2", ".csv", C("a;b", "c;d"),         C("a;b", "c;X")),
]

HDR_RE = re.compile(r"^(A(?: [A-Z])+|A)$")

def cols_of(body: str):
    for ln in body.splitlines():
        if HDR_RE.match(ln.strip()) and " " in ln or ln.strip() == "A":
            letters = [c for c in ln.strip() if c.isalpha()]
            return letters, ln
    return None, None

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m62-delimiter-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, ext, left, right in CASES:
        lp = fx / f"{tag}-L{ext}"; rp = fx / f"{tag}-R{ext}"
        lp.write_text(left, encoding="utf-8", newline="")
        rp.write_text(right, encoding="utf-8", newline="")
        lines = ['data-report layout:side-by-side output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        out = run_dir / "reports" / f"{tag}.out"
        run = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                      str(out.resolve()), timeout=120.0, script_text=lines[0])
        body = out.read_text(encoding="utf-8-sig", errors="replace") if out.exists() else ""
        hdr_letters, hdr = cols_of(body)
        rec = {"tag": tag, "ext": ext, "left": left, "right": right,
               "exit": run.exit_code, "columns": hdr_letters, "header_row": hdr}
        results.append(rec)
        ncol = len(hdr_letters) if hdr_letters else 0
        print(f"{tag:15} ext={ext:5} cols={ncol} header={hdr!r}")

    (run_dir / "m62-delimiter.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
