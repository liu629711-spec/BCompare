#!/usr/bin/env python3
"""M6.2 batch-6: auto-detect candidate set and priority (non-.csv extensions).

Batch-5 settled: `.csv` is FIXED to comma (mask matches the CSV built-in;
DlmDelimiters "44"), no detection happens (tab/pipe/semicolon stay inside one
cell).  Extensions without a table mask (.txt/.tsv/.xyz) auto-detect.
Open: which candidates does auto-detect try, and what happens when several fit?

  S1 .txt comma+tab both valid-ish   (priority)
  S2 .txt semicolon only
  S3 .txt pipe only
  S4 .txt space-only columns
  S5 .txt ragged comma (row A: 2 fields, row B: 3)
  S6 (no extension) file, comma content
  S7 .TXT uppercase extension
  S8 .txt comma only but 2 rows where only row 1 has comma (detection basis?)

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m62_auto_detect_probe.py
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

CASES = [
    ("S1-ct",     ".txt", C("a,b\tc", "d,e\tf"),      C("a,b\tc", "d,X\tf")),
    ("S2-semi",   ".txt", C("a;b", "c;d"),            C("a;b", "c;X")),
    ("S3-pipe",   ".txt", C("a|b", "c|d"),            C("a|b", "c|X")),
    ("S4-space",  ".txt", C("a b", "c d"),            C("a b", "c X")),
    ("S5-ragged", ".txt", C("a,b", "c,d,e"),          C("a,b", "c,d,X")),
    ("S6-noext",  "",     C("a,b", "c,d"),            C("a,b", "c,X")),
    ("S7-upper",  ".TXT", C("a\tb", "c\td"),          C("a\tb", "c\tX")),
    ("S8-row1",   ".txt", C("a,b", "cd"),             C("a,b", "cX")),
]

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m62-autodetect-%Y%m%dT%H%M%SZ"))
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
        hdr = None
        blines = body.splitlines()
        for i, l in enumerate(blines):
            if i + 1 < len(blines) and l and set(blines[i+1]) == {"-"}:
                hdr = l
                break
        results.append({"tag": tag, "ext": ext, "exit": run.exit_code,
                        "header_row": hdr, "first_body": blines[blines.index(hdr)+2:][:2] if hdr else []})
        print(f"{tag:10} ext={ext or '(none)':6} exit={run.exit_code} header={hdr!r}")

    (run_dir / "m62-autodetect.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
