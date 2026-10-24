#!/usr/bin/env python3
"""M5.3 batch-2b probe -- case-model + escape discriminators for XML/HTML/SQL.

Round 2 for the XML/HTML/SQL formats (m53b measured: tag-name case -> similar,
attribute value case -> different, SQL keyword case -> similar).  The working
model this probe tests:

  XML/HTML (TXMLFormat structural comparer + text grammar):
    case outside String elements is UNIMPORTANT; string contents stay exact.
    Predictions: attr-name / text / entity / PI case -> similar,
    but attr-value case -> different (m53b already measured).

  SQL: Keyword and Identifier elements carry CaseSensitive=False (case-
    insensitive comparison); String contents stay exact.

  XML/HTML strings declare no Escape attribute: `\\` is inert, so `\\"` CLOSES
    a string.  Discriminator `b="x\\" <!-- one`: with `\\` inert the string
    closes and `<!--` opens a comment (similar); with escapes honoured the
    quote is escaped and one/two land in string content (different).

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m53c_case_model.py
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

CASES = [
    # ---- XML case model ------------------------------------------------
    ("xml-attr-name-case", ".xml", ['<a B="1"/>'], ['<a b="1"/>'], ["similar"]),
    ("xml-text-case", ".xml", ["<p>Hello</p>"], ["<p>HELLO</p>"], ["similar"]),
    ("xml-pi-case", ".xml", ['<?xml version="1.0"?>'], ['<?XML version="1.0"?>'],
     ["similar"]),
    ("xml-markup-ci-value-exact", ".xml", ['<a B="x"/>'], ['<a b="X"/>'],
     ["different"]),
    ("xml-bare-text-case", ".xml", ["hello"], ["HELLO"], ["similar"]),
    ("xml-str-single-quote", ".xml", ["<a t='x\"y'/>"], ["<a t='x\"z'/>"],
     ["different"]),
    # ---- XML escape question (redesigned) --------------------------------
    ("xml-no-escape", ".xml", ['<a b="x\\" <!-- one'], ['<a b="x\\" <!-- two'],
     ["similar"]),
    # ---- HTML case model -------------------------------------------------
    ("html-attr-name-case", ".html", ['<a HREF="x">y</a>'], ['<a href="x">y</a>'],
     ["similar"]),
    ("html-entity-case", ".html", ["<p>&AMP;</p>"], ["<p>&amp;</p>"], ["similar"]),
    ("html-text-case", ".html", ["<p>Hello</p>"], ["<p>HELLO</p>"], ["similar"]),
    ("html-no-escape", ".html", ['<a b="x\\" <!-- one'], ['<a b="x\\" <!-- two'],
     ["similar"]),
    # ---- SQL case model ----------------------------------------------------
    ("sql-ident-case", ".sql", ["SELECT * FROM t1;"], ["SELECT * FROM T1;"],
     ["similar"]),
    ("sql-string-absorbs-comment", ".sql", ["SELECT 'a -- b';"], ["SELECT 'a -- c';"],
     ["different"]),
    ("sql-stmt-case", ".sql", ["INSERT INTO t VALUES ('x');"],
     ["insert into t values ('x');"], ["similar"]),
]

ROW_RE = re.compile(r'<linecomp status="(\w+)">(.*?)</linecomp>', re.S)
LTID_RE = re.compile(r'ltid="(-?\d+)"')
RTID_RE = re.compile(r'rtid="(-?\d+)"')


def rows_of(body: str) -> list[tuple[str, str, str]]:
    out = []
    for m in ROW_RE.finditer(body):
        lt = LTID_RE.search(m.group(2))
        rt = RTID_RE.search(m.group(2))
        out.append((m.group(1), lt.group(1) if lt else "-",
                    rt.group(1) if rt else "-"))
    return out


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m53c-case-model-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} (engine {inst.app_version})")
    print(f"product : {PRODUCT}\n")

    results = []
    for tag, ext, left, right, predicted in CASES:
        lp = fx / f"{tag}-L{ext}"
        rp = fx / f"{tag}-R{ext}"
        lp.write_text("\n".join(left) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(right) + "\n", encoding="utf-8", newline="")

        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace") \
            if run.report_exists and run.report_bytes else ""

        p_out = run_dir / "reports" / f"{tag}.product.xml"
        if PRODUCT.exists():
            subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)],
                           capture_output=True, timeout=120)
        p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace") \
            if p_out.exists() else ""

        o_rows = rows_of(o_body)
        p_rows = rows_of(p_body)
        o_status = [r[0] for r in o_rows]
        verdict = "OK" if o_status == predicted else f"PREDICT-MISS expected={predicted}"
        results.append({
            "tag": tag, "ext": ext, "predicted": predicted,
            "oracle_rows": o_rows, "product_rows": p_rows, "verdict": verdict,
        })
        print(f"[{tag}] oracle={o_status}  {verdict}")

    n_ok = sum(1 for r in results if r["verdict"] == "OK")
    print(f"\npredictions: {n_ok}/{len(results)} ok")
    (run_dir / "m53c-results.json").write_text(json.dumps(
        {"cases": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"raw: {run_dir / 'm53c-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
