#!/usr/bin/env python3
"""Build the M5.3 XML/HTML/SQL golden anchors from the m53b/m53c/m53d matrix.

Every case re-records the live Oracle serially (standard in-place/Job-Object
discipline) and APPENDS manifest entries keyed ``m53b-``.  The shapes pin the
measured rules of docs/11 §27: XML/HTML fold case outside strings (structural
comparer behaviour) while string contents and listed HTML entities compare
verbatim, comments span lines and persist when unterminated, and SQL strings
are complete-match elements so an unterminated quote leaves `--` as a real
comment.

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m53b_add_anchors.py
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import sys
import time
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

STATUS_RE = re.compile(r'<linecomp status="([a-z]+)"')

I = "ignore-unimportant"

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

ANCHORS: list[tuple[str, str, list[str], list[str], str, str | None]] = [
    # ---- XML ----------------------------------------------------------
    ("xml-case-tag", "xml", ['<Tag v="1">x</Tag>'], ['<tag v="1">x</tag>'],
     "m53b: XML tag-name case folds (structural comparer)", None),
    ("xml-attr-name-case", "xml", ['<a B="1"/>'], ['<a b="1"/>'],
     "m53c: attribute-name case folds", None),
    ("xml-attr-value-case", "xml", ['<a b="x"/>'], ['<a b="X"/>'],
     "m53c: string contents compare verbatim", None),
    ("xml-text-case", "xml", ["<p>Hello</p>"], ["<p>HELLO</p>"],
     "m53c: text content case folds", None),
    ("xml-entity-no-element", "xml", ["<p>&amp;</p>"], ["<p>&AMP;</p>"],
     "m53d: XML has no entity element; `&amp;` is unclaimed text", None),
    ("xml-comment-inline", "xml", ["<!-- a --> <x/>"], ["<!-- b --> <x/>"],
     "m53b: inline comment change is unimportant", None),
    ("xml-comment-line-iu", "xml", ["<a/> <!-- one"], ["<a/> <!-- two"],
     f"m53b: options:{I} folds the trailing comment change", I),
    ("xml-comment-block", "xml",
     ["<!--", "body one", "--> <x/>"], ["<!--", "body two", "--> <x/>"],
     "m53b: comment bodies span lines", None),
    ("xml-comment-open-persist", "xml",
     ["<!-- open", "int a = 1;"], ["<!-- open", "int a = 2;"],
     "m53b: unterminated `<!--` carries the comment across lines", None),
    ("xml-str-unterminated", "xml", ['<a href="x'], ['<a href="y'],
     "m53b: StopEOL string to end of line", None),
    ("xml-no-escape", "xml", ['<a b="x\\" <!-- one'], ['<a b="x\\" <!-- two'],
     "m53c: `\\\\` is inert (no Escape attribute); `<!--` opens a comment", None),
    ("xml-orphan-comment", "xml", ["<a/>", "<b/>", "<!-- c -->"], ["<x/>"],
     "m53: leftover comment is leftsimilar beside a leftorphan", None),
    ("xml-realistic", "xml", XML_REAL_L.splitlines(), XML_REAL_R.splitlines(),
     "m53b: 6-line document; row truth from runs/m53b-*", None),
    # ---- HTML ----------------------------------------------------------
    ("html-case-tag", "html", ["<DIV>x</DIV>"], ["<div>x</div>"],
     "m53b: HTML tag-name case folds", None),
    ("html-attr-name-case", "html", ['<a HREF="x">y</a>'], ['<a href="x">y</a>'],
     "m53c: attribute-name case folds", None),
    ("html-text-case", "html", ["<p>Hello</p>"], ["<p>HELLO</p>"],
     "m53c: text content case folds", None),
    ("html-entity-known-case", "html", ["<p>&COPY;</p>"], ["<p>&copy;</p>"],
     "m53d: listed entity matched case-sensitively; class pair K vs O is important", None),
    ("html-entity-bogus-case", "html", ["<p>&bogus;</p>"], ["<p>&BOGUS;</p>"],
     "m53d: unlisted `&name;` is unclaimed text on both sides; folds", None),
    ("html-entity-numeric", "html", ["<p>&#38;</p>"], ["<p>&#39;</p>"],
     "m53d: numeric references are keyword elements", None),
    ("html-single-quote-value-case", "html", ["<a t='X'>y</a>"], ["<a t='x'>y</a>"],
     "m53d: single-quoted string contents compare verbatim", None),
    ("html-comment-block", "html",
     ["<!--", "body one", "--> <p/>"], ["<!--", "body two", "--> <p/>"],
     "m53b: comment bodies span lines", None),
    ("html-str-unterminated", "html", ["<a href='x"], ["<a href='y"],
     "m53b: StopEOL string to end of line", None),
    ("html-no-escape", "html", ['<a b="x\\" <!-- one'], ['<a b="x\\" <!-- two'],
     "m53c: `\\\\` is inert; `<!--` opens a comment", None),
    ("html-realistic", "html", HTML_REAL_L.splitlines(), HTML_REAL_R.splitlines(),
     "m53b: 7-line document; row truth from runs/m53b-*", None),
    # ---- SQL -----------------------------------------------------------
    ("sql-case-keyword", "sql", ["SELECT * FROM t1;"], ["select * from t1;"],
     "m53b: keyword case folds (CaseSensitive=False elements)", None),
    ("sql-ident-case", "sql", ["SELECT * FROM t1;"], ["SELECT * FROM T1;"],
     "m53c: identifier case folds", None),
    ("sql-comment-line", "sql", ["SELECT 1; -- alpha"], ["SELECT 1; -- beta"],
     "m53b: trailing `--` comment change is unimportant", None),
    ("sql-comment-line-iu", "sql", ["SELECT 1; -- alpha"], ["SELECT 1; -- beta"],
     f"m53b: options:{I} folds the comment-only change", I),
    ("sql-comment-block", "sql",
     ["/*", "body", "*/ SELECT 1;"], ["/*", "body two", "*/ SELECT 1;"],
     "m53b: `/* */` bodies span lines", None),
    ("sql-str-unterminated-comment", "sql",
     ["SELECT 'abc -- x"], ["SELECT 'abc -- y"],
     "m53b: complete-match strings leave an unterminated quote's `--` a real comment",
     None),
    ("sql-string-absorbs-comment", "sql", ["SELECT 'a -- b';"], ["SELECT 'a -- c';"],
     "m53c: a matched string absorbs `--` as content", None),
    ("sql-doubled-quote", "sql", ["x = 'It''s fine';"], ["x = 'It''s fine!';"],
     "m53b: `''` stays inside one string element", None),
    ("sql-escape", "sql", ["x = 'a\\'b';"], ["x = 'a\\'c';"],
     "m53b: `\\\\x` escapes stay inside the string", None),
    ("sql-nprefix-case", "sql", ["x = n'abc';"], ["x = N'abc';"],
     "m53d: the n/N prefix is part of the string token; verbatim", None),
    ("sql-realistic", "sql", SQL_REAL_L.splitlines(), SQL_REAL_R.splitlines(),
     "m53b: 7-line script; row truth from runs/m53b-*", None),
]


def main() -> int:
    golden = REA / "verify" / "golden"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m53b-anchors-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.app_version})")

    man_path = golden / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    shutil.copy2(man_path, run_dir / "manifest.json.before")
    new_keys = [f"m53b-{a[0]}" for a in ANCHORS]
    clash = [k for k in new_keys if k in manifest]
    if clash:
        raise SystemExit(f"manifest already has keys: {clash}")

    added = 0
    for name, ext, ll, rl, note, options in ANCHORS:
        key = f"m53b-{name}"
        left = golden / f"{key}-L.{ext}"
        right = golden / f"{key}-R.{ext}"
        left.write_text("\n".join(ll) + "\n", encoding="utf-8")
        right.write_text("\n".join(rl) + "\n", encoding="utf-8")
        report = golden / f"{key}.xml"
        t0 = time.perf_counter()
        script = orc.write_script(run_dir / f"{key}.bcs",
                                  [orc.text_script("xml", options)])
        run = orc.run(cur.oracle_path, script, left, right, report,
                      timeout=120.0, script_text=orc.text_script("xml", options))
        seconds = round(time.perf_counter() - t0, 3)
        if run.exit_code != 0 or not run.report_exists:
            raise SystemExit(f"{key}: oracle exit {run.exit_code}, report={run.report_exists}")
        statuses = STATUS_RE.findall(
            report.read_bytes().decode("utf-8-sig", errors="replace"))
        manifest[key] = {
            "unit": "M5XmlHtmlSql",
            "note": note,
            "exit_code": run.exit_code,
            "statuses": statuses,
            "seconds": seconds,
            "left": str(left),
            "right": str(right),
            "report": str(report),
        }
        added += 1
        print(f"  {key:<44} statuses={statuses}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"\nadded {added} anchors; manifest now {len(manifest)} entries")
    print(f"run dir: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
