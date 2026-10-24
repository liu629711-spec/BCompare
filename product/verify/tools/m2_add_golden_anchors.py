#!/usr/bin/env python3
"""Build the M2 golden anchors from the U2/U2b/U3 probe matrix (task M2.5).

Every case below was OBSERVED through the live Oracle in ``runs/u2-probe-*``,
``runs/u2b-probe-*`` or ``runs/u3-probe-*``.  This script re-runs each case
serially against the current install (same in-place/Job-Object discipline as
every Oracle call), writes the fixture pair and the Oracle's XML report into
``D:\\Rea\\verify\\golden\\``, and APPENDS the manifest entries.  Existing
manifest keys are never touched; the script refuses to run if a key already
exists, and it snapshots the previous manifest into its run directory.

Layout anchor: one ``summary`` case is added to ``verify/layouts`` too (the
loader reads an optional ``ext`` so the .c fixtures can be referenced).

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m2_add_golden_anchors.py
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

#: (name, ext, left lines, right lines, note, options).
#: Names are prefixed ``m2-``; the fixtures/reports carry the same stem.
ANCHORS: list[tuple[str, str, list[str], list[str], str, str | None]] = [
    # ---- U2: mixed lines ------------------------------------------------
    ("mixed-trailing-comment", "c", ["int x = 1; // note"], ["int x = 1; // other"],
     "u2: comment-only change on a code line is unimportant", None),
    ("mixed-trailing-comment-iu", "c", ["int x = 1; // note"], ["int x = 1; // other"],
     f"options:{I} folds the comment-only change (u2)", I),
    ("mixed-lead-comment", "c", ["/* head */ int x;"], ["/* tail */ int x;"],
     "u2: leading block comment change is unimportant", None),
    # ---- U2: block comments --------------------------------------------
    ("block-comment-body", "c", ["/*", "alpha body", "*/", "int x;"],
     ["/*", "beta body", "*/", "int x;"],
     "u2: block comment bodies are unimportant across lines", None),
    ("block-comment-body-iu", "c", ["/*", "alpha body", "*/", "int x;"],
     ["/*", "beta body", "*/", "int x;"],
     f"options:{I} folds the block comment body (u2)", I),
    ("block-continuation-star", "c", ["/*", " * alpha", " */", "int x;"],
     ["/*", " * beta", " */", "int x;"],
     "u2: `*` continuation lines inside a block comment are unimportant", None),
    # ---- U2: string interiors -------------------------------------------
    ("string-internal-ws", "c", ['char *a = "a b";'], ['char *a = "a  b";'],
     "u2: whitespace inside a string is important", None),
    ("string-case", "c", ['char *a = "ABC";'], ['char *a = "abc";'],
     "u2: case inside a string is important", None),
    ("string-unterminated", "c", ['char *a = "abc'], ['char *a = "abd'],
     "u2: a string to end-of-line still carries important text", None),
    ("string-escaped-quote", "c", ['char *a = "a\\"b";'], ['char *a = "a\\"c";'],
     "u2: escaped quotes keep the string one element", None),
    # ---- U2: comment/blank taxonomy --------------------------------------
    ("comment-syntax-swap", "c", ["// a"], ["/* a */"],
     "u2: comment vs comment across syntax is unimportant", None),
    ("comment-vs-empty", "c", ["// note"], [""],
     "u2: a comment line pairs with an empty line as unimportant", None),
    ("blank-vs-ws", "c", [""], ["   "],
     "u2: empty vs whitespace-only pairs as unimportant", None),
    # ---- U2: number shapes -----------------------------------------------
    ("number-hex", "c", ["int a = 0x10;"], ["int a = 0x20;"],
     "u2: hex literals are important", None),
    ("number-exponent", "c", ["double a = 1.5e3;"], ["double a = 1.5e4;"],
     "u2: exponent literals are important", None),
    # ---- U2: alignment ----------------------------------------------------
    ("align-swap-trailing-comment", "c", ["int a;", "x = 1; // one"],
     ["x = 1; // two", "int a;"],
     "u2: swapped trailing-comment lines align by important text only", None),
    ("align-comments-forward", "c", ["// a", "// b", "int x;"], ["// c", "int x;"],
     "u2: extra comment line is leftsimilar; comments align forward", None),
    ("align-comments-forward-iu", "c", ["// a", "// b", "int x;"], ["// c", "int x;"],
     f"options:{I} folds leftsimilar and reuses the paired rtid (u2b)", I),
    # ---- U2: python --------------------------------------------------------
    ("py-comment", "py", ["# alpha"], ["# beta"],
     "u2: python comments are unimportant", None),
    ("py-indent", "py", ["x = 1"], ["    x = 1"],
     "u2: python indentation is IMPORTANT", None),
    ("py-trailing-ws", "py", ["x = 1   "], ["x = 1"],
     "u2: python trailing whitespace is unimportant", None),
    ("py-hash-midline", "py", ["x = 1  # alpha"], ["x = 1  # beta"],
     "u2: python mid-line comment change is unimportant", None),
    ("py-triple-quote", "py", ["'''", "a b", "'''"], ["'''", "a  b", "'''"],
     "u2: triple-quoted string bodies span lines and are important", None),
    ("py-string-case", "py", ['x = "Abc"'], ['x = "abc"'],
     "u2: python string case is important", None),
    # ---- U2: javascript ------------------------------------------------------
    ("js-comment", "js", ["// alpha"], ["// beta"],
     "u2: javascript comments are unimportant", None),
    ("js-regex-literal", "js", ["var r = /ab/g;"], ["var r = /ac/g;"],
     "u2: regex literals are important", None),
    ("js-regex-ws", "js", ["var r = /a b/g;"], ["var r = /ab/g;"],
     "u2: whitespace inside a regex literal is important", None),
    ("js-string-quote", "js", ["var s = 'ab';"], ["var s = 'ac';"],
     "u2: single-quoted strings are important", None),
    ("js-template-literal", "js", ["var t = `a b`;"], ["var t = `a c`;"],
     "u2: backtick content has no grammar element; important", None),
    # ---- U2: unknown extensions --------------------------------------------
    ("foo-case", "foo", ["Alpha"], ["alpha"],
     "u2: unknown extensions are plain text; case is unimportant", None),
    ("foo-comment", "foo", ["// alpha"], ["// beta"],
     "u2: unknown extensions have no comment rules", None),
    ("foo-syntax", "foo", ["int x = 10;"], ["long x = 20;"],
     "u2: unknown extensions keep text differences important", None),
    ("foo-comment-vs-code", "foo", ["// note"], ["x;"],
     "u2: plain text pairs comment text against code text as different", None),
    # ---- U2b: one-sided unimportant lines -----------------------------------
    ("orphan-comment-trailing", "c", ["int a;", "int b;", "// c"], ["int x;"],
     "u2b: leftover comment is leftsimilar beside a leftorphan", None),
    ("orphan-comment-trailing-iu", "c", ["int a;", "int b;", "// c"], ["int x;"],
     f"options:{I} folds leftsimilar to same with borrowed rtid (u2b)", I),
    ("orphan-comment-lead", "c", ["// c", "int b;"], ["int x;"],
     "u2b: leading leftover comment is leftsimilar", None),
    ("orphan-comment-lead-iu", "c", ["// c", "int b;"], ["int x;"],
     f"options:{I}: no preceding pair means borrowed id 0 (u2b)", I),
    ("orphan-comment-mid", "c", ["int a;", "// c", "int b;"], ["int x;", "int y;"],
     "u2b: mid-file leftover comment is leftsimilar", None),
    ("orphan-comment-mid-iu", "c", ["int a;", "// c", "int b;"], ["int x;", "int y;"],
     f"options:{I} folds the mid-file leftsimilar (u2b)", I),
    ("orphan-two-comments", "c", ["// a", "// b"], ["int x;"],
     "u2b: first comment pairs as different; the leftover is leftsimilar", None),
    ("orphan-right-comment", "c", ["int x;"], ["int y;", "// c"],
     "u2b: right-side mirror is rightsimilar", None),
    ("orphan-right-comment-iu", "c", ["int x;"], ["int y;", "// c"],
     f"options:{I}: folded rightsimilar is a self-closing empty text (u2b)", I),
    ("orphan-ws-line", "c", ["   ", "int x;"], ["int x;"],
     "u2b: whitespace-only leftovers are leftsimilar too", None),
    ("orphan-empty-line", "c", ["int x;", ""], ["int x;"],
     "u2b: empty leftovers are leftsimilar (al-empty-left's orphan has content)", None),
    ("orphan-mixed-trailing-comment", "c", ["int a;", "x = 1; // c"], ["int a;"],
     "u2b: a line with important content is never leftsimilar", None),
    ("orphan-comment-inside-replace", "c", ["// a", "int b;"], ["int x;", "int y;"],
     "u2b: comments pair as different inside a replace block", None),
    ("comment-after-code", "c", ["int x;", "// a"], ["int x;"],
     "u2b: trailing comment after a paired line is leftsimilar", None),
    ("comment-after-code-iu", "c", ["int x;", "// a"], ["int x;"],
     f"options:{I}: fold borrows the preceding pair's rtid (u2b)", I),
    ("comment-before-code", "c", ["// a", "int x;"], ["int x;"],
     "u2b: leading comment before a paired line is leftsimilar", None),
    ("comment-before-code-iu", "c", ["// a", "int x;"], ["int x;"],
     f"options:{I}: fold with no preceding pair borrows id 0 (u2b)", I),
    ("three-comments-one", "c", ["// a", "// b", "// c"], ["// z"],
     "u2b: one comment pairs; two leftovers are leftsimilar", None),
    ("comment-vs-code", "c", ["// note"], ["x;"],
     "u2b: comment vs code is different and survives ignore-unimportant", None),
    ("comment-vs-code-iu", "c", ["// note"], ["x;"],
     f"options:{I}: comment vs code stays different (u2b)", I),
    ("empty-vs-code", "c", [""], ["int x;"],
     "u2b: empty vs code pairs as different", None),
    # ---- U3: display filtering on leftsimilar -------------------------------
    ("align-comments-forward-display-mismatches", "c",
     ["// a", "// b", "int x;"], ["// c", "int x;"],
     "u3: options:display-mismatches keeps similar and leftsimilar rows",
     "display-mismatches"),
    ("align-comments-forward-display-matches", "c",
     ["// a", "// b", "int x;"], ["// c", "int x;"],
     "u3: options:display-matches drops leftsimilar rows", "display-matches"),
]

#: The one layout anchor: summary on the comments-forward pair.
LAYOUT_CASE = ("comments", "c", ["// a", "// b", "int x;"], ["// c", "int x;"])


def main() -> int:
    golden = REA / "verify" / "golden"
    layouts = REA / "verify" / "layouts"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m2-anchors-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")

    man_path = golden / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    shutil.copy2(man_path, run_dir / "manifest.json.before")
    new_keys = [f"m2-{a[0]}" for a in ANCHORS]
    clash = [k for k in new_keys if k in manifest]
    if clash:
        raise SystemExit(f"manifest already has keys: {clash}")

    added = 0
    for name, ext, ll, rl, note, options in ANCHORS:
        key = f"m2-{name}"
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
            "unit": "M2Importance",
            "note": note,
            "exit_code": run.exit_code,
            "statuses": statuses,
            "seconds": seconds,
            "left": str(left),
            "right": str(right),
            "report": str(report),
        }
        added += 1
        print(f"  {key:<48} statuses={statuses}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"manifest: +{added} anchors -> {len(manifest)} total")

    # ---- layout anchor -------------------------------------------------
    case, ext, ll, rl = LAYOUT_CASE
    lman_path = layouts / "manifest.json"
    lmanifest = json.loads(lman_path.read_text(encoding="utf-8"))
    shutil.copy2(lman_path, run_dir / "layouts-manifest.json.before")
    name = f"{case}-summary"
    if name in lmanifest:
        raise SystemExit(f"layouts manifest already has {name}")
    left = layouts / f"{case}-L.{ext}"
    right = layouts / f"{case}-R.{ext}"
    left.write_text("\n".join(ll) + "\n", encoding="utf-8")
    right.write_text("\n".join(rl) + "\n", encoding="utf-8")
    report = layouts / f"{name}.txt"
    script = orc.write_script(run_dir / f"{name}.bcs", [orc.text_script("summary", None)])
    run = orc.run(cur.oracle_path, script, left, right, report,
                  timeout=120.0, script_text=orc.text_script("summary", None))
    if run.exit_code != 0 or not run.report_exists:
        raise SystemExit(f"{name}: oracle exit {run.exit_code}")
    lmanifest[name] = {
        "layout": "summary", "case": case, "ext": "c",
        "exit_code": run.exit_code, "bytes": report.stat().st_size,
        "report": str(report),
    }
    lman_path.write_text(json.dumps(lmanifest, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"layouts manifest: +{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
