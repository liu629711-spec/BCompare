#!/usr/bin/env python3
"""M5.3 batch-2 probe -- XML / HTML / SQL grammar discriminators.

Same protocol as ``m53_java_grammar.py``: one fixture pair per rule, serial
Oracle, archived truth under ``runs/m53b-*``.  Predictions come from
``bcfileformats-spec.json`` plus the U1 contract (verdict = only comment /
whitespace elements may differ).

Measured questions this round:

  XML (no Escape attr on strings, `<!--` -> `-->` comment):
    xml-case-tag        tag-name case change            -> different (verbatim)
    xml-comment-inline  inline `<!-- -->` text differs  -> similar
    xml-comment-span    `<!--` body `-->` across lines  -> similar
    xml-comment-open    unterminated `<!--` persists?   -> similar if yes
    xml-str-unterminated `"` with no close (StopEOL)     -> different
    xml-no-escape       `\` before the closing quote    -> similar (no Escape)
    xml-realistic       small document, row-level truth

  HTML (same shape as XML plus case-insensitive tag keywords):
    html-case-tag       `<DIV>` vs `<div>`              -> different
    html-comment-span   cross-line `<!-- -->`           -> similar
    html-str-unterminated `'` with no close              -> different
    html-no-escape      `\` inert in strings            -> similar
    html-entity         entity change                   -> different
    html-realistic      small document, row-level truth

  SQL (String is a COMPLETE-MATCH regex, not StopEOL: an unterminated quote
  matches nothing, so a following `--` is still a real comment):
    sql-case-keyword    `SELECT` vs `select`            -> different
    sql-comment-line    trailing `--` text differs      -> similar
    sql-comment-block   `/* */` across lines            -> similar
    sql-str-unterminated-comment unterminated `'` then `--` -> SIMILAR (headline)
    sql-doubled-quote   `''` inside a string literal    -> different
    sql-escape          `\'` inside a string literal    -> different
    sql-realistic       small script, row-level truth

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m53b_xml_html_sql.py
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

XML_REAL_L = """\
<?xml version="1.0"?>
<!-- configuration -->
<config debug="true">
    <path value="/usr/bin"/>
    <name value="app"/>
</config>
"""

XML_REAL_R = """\
<?xml version="1.0"?>
<!-- configuration (v2) -->
<config debug="true">
    <path value="/usr/bin"/>
    <name value="App"/>
</config>
"""

HTML_REAL_L = """\
<!DOCTYPE html>
<!-- page header -->
<html>
  <body class="main">
    <p>Hello</p>
  </body>
</html>
"""

HTML_REAL_R = """\
<!DOCTYPE html>
<!-- page header (v2) -->
<html>
  <body class="Main">
    <p>Hello</p>
  </body>
</html>
"""

SQL_REAL_L = """\
-- user table setup
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

INSERT INTO users VALUES (1, 'alice');
"""

SQL_REAL_R = """\
-- user table setup (v2)
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

INSERT INTO users VALUES (1, 'Alice');
"""

#: (tag, ext, left lines, right lines, predicted statuses)
CASES = [
    # ---- XML ----------------------------------------------------------
    ("xml-case-tag", ".xml", ['<Tag v="1">x</Tag>'], ['<tag v="1">x</tag>'],
     ["different"]),
    ("xml-comment-inline", ".xml", ["<!-- a --> <x/>"], ["<!-- b --> <x/>"],
     ["similar"]),
    ("xml-comment-span", ".xml",
     ["<!--", "body one", "--> <x/>"],
     ["<!--", "body two", "--> <x/>"],
     ["same", "similar", "same"]),
    ("xml-comment-open", ".xml",
     ["<!-- open", "int a = 1;"],
     ["<!-- open", "int a = 2;"],
     ["similar", "similar"]),
    ("xml-str-unterminated", ".xml", ['<a href="x'], ['<a href="y'], ["different"]),
    ("xml-no-escape", ".xml", ['<a b="x\\"--> one'], ['<a b="x\\"--> two'],
     ["similar"]),
    ("xml-realistic", ".xml", XML_REAL_L.splitlines(), XML_REAL_R.splitlines(), None),
    # ---- HTML ----------------------------------------------------------
    ("html-case-tag", ".html", ["<DIV>x</DIV>"], ["<div>x</div>"], ["different"]),
    ("html-comment-span", ".html",
     ["<!--", "body one", "--> <p/>"],
     ["<!--", "body two", "--> <p/>"],
     ["same", "similar", "same"]),
    ("html-str-unterminated", ".html", ["<a href='x"], ["<a href='y"], ["different"]),
    ("html-no-escape", ".html", ['<a b="x\\"--> one'], ['<a b="x\\"--> two'],
     ["similar"]),
    ("html-entity", ".html", ["<p>&amp;</p>"], ["<p>&nbsp;</p>"], ["different"]),
    ("html-realistic", ".html", HTML_REAL_L.splitlines(), HTML_REAL_R.splitlines(), None),
    # ---- SQL -----------------------------------------------------------
    ("sql-case-keyword", ".sql", ["SELECT * FROM t1;"], ["select * from t1;"],
     ["different"]),
    ("sql-comment-line", ".sql", ["SELECT 1; -- alpha"], ["SELECT 1; -- beta"],
     ["similar"]),
    ("sql-comment-block", ".sql",
     ["/*", "body", "*/ SELECT 1;"],
     ["/*", "body two", "*/ SELECT 1;"],
     ["same", "similar", "same"]),
    ("sql-str-unterminated-comment", ".sql",
     ["SELECT 'abc -- x"], ["SELECT 'abc -- y"],
     ["similar"]),
    ("sql-doubled-quote", ".sql", ["x = 'It''s fine';"], ["x = 'It''s fine!';"],
     ["different"]),
    ("sql-escape", ".sql", ["x = 'a\\'b';"], ["x = 'a\\'c';"], ["different"]),
    ("sql-realistic", ".sql", SQL_REAL_L.splitlines(), SQL_REAL_R.splitlines(), None),
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
               datetime.now(timezone.utc).strftime("m53b-xml-html-sql-%Y%m%dT%H%M%SZ"))
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
        verdict = "n/a" if predicted is None else (
            "OK" if o_status == predicted else f"PREDICT-MISS expected={predicted}")
        agree = "agree" if o_rows == p_rows else "DIFF"
        results.append({
            "tag": tag, "ext": ext, "predicted": predicted,
            "oracle_rows": o_rows, "product_rows": p_rows,
            "verdict": verdict, "pairing": agree,
        })
        print(f"[{tag}] oracle={o_status}  {verdict}")
        if o_rows != p_rows:
            print(f"    product(now)={ [r[0] for r in p_rows] }")

    n_ok = sum(1 for r in results
               if r["verdict"] == "OK" or r["verdict"] == "n/a")
    n_miss = sum(1 for r in results if r["verdict"].startswith("PREDICT-MISS"))
    print(f"\npredictions: {n_ok} ok, {n_miss} miss "
          f"(realistic has no prediction; row truth archived)")
    (run_dir / "m53b-results.json").write_text(json.dumps(
        {"cases": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"raw: {run_dir / 'm53b-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
