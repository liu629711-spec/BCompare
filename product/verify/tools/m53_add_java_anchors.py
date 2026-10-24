#!/usr/bin/env python3
"""Build the M5.3 JAVA golden anchors from the m53 probe matrix.

Every case below was OBSERVED through the live Oracle in ``runs/m53-java-*``
(the probe first recorded each rule's verdict; this script re-runs the same
shapes serially against the current install under the standard in-place/Job-
Object discipline and APPENDS manifest entries keyed ``m53-``).  Existing
manifest keys are never touched; the script refuses to run if a key already
exists and snapshots the previous manifest into its run directory.

The fixtures pin the measured JAVA grammar (docs/11 §26): case-sensitive
important text, `//` and `/* */` comments unimportant across lines, both quote
kinds carry backslash escapes and StopEOL, and unknown extensions keep the
plain-text fallback.

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m53_add_java_anchors.py
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

REALISTIC_L = """\
package com.example;

import java.util.List;

// Service facade
public class Greeter {
    private static final String TAG = "greeter";

    public String greet(String name) {
        if (name == null) {
            return "hello anonymous";
        }
        // trailing note
        return "hello " + name;
    }
}
"""

REALISTIC_R = """\
package com.example;

import java.util.List;

// Service facade (v2)
public class Greeter {
    private static final String TAG = "greeter";

    public string greet(String Name) {
        if (name == null) {
            return "hello anonymous";
        }
        // trailing note
        return "hello " + name;
    }
}
"""

#: (name, ext, left lines, right lines, note, options). Names are prefixed
#: ``m53-``; fixtures/reports carry the same stem.
ANCHORS: list[tuple[str, str, list[str], list[str], str, str | None]] = [
    # ---- case sensitivity -------------------------------------------------
    ("java-case-ident", "java", ["int value = 1;"], ["int Value = 1;"],
     "m53: identifier case-only change is different (M2 known difference closed)",
     None),
    ("java-case-keyword", "java", ["if (x) { return; }"], ["IF (x) { RETURN; }"],
     "m53: keyword case-only change is different", None),
    ("java-mixed-case-comment", "java", ["int X = 1; // c"], ["int x = 1; // c"],
     "m53: a matching comment does not rescue a code case change", None),
    # ---- comments ----------------------------------------------------------
    ("java-comment-line", "java", ["int x = 1; // alpha"], ["int x = 1; // beta"],
     "m53: trailing comment change is unimportant", None),
    ("java-comment-line-iu", "java", ["int x = 1; // alpha"], ["int x = 1; // beta"],
     f"m53: options:{I} folds the comment-only change", I),
    ("java-comment-block", "java",
     ["/* head", "body one", "*/ int y = 1;"],
     ["/* head", "body two", "*/ int y = 1;"],
     "m53: block comment bodies span lines and are unimportant", None),
    ("java-comment-vs-blank", "java", ["// note", "int x = 1;"], ["", "int x = 1;"],
     "m53: a comment line pairs with an empty line as unimportant", None),
    ("java-comment-vs-code", "java", ["// note"], ["x;"],
     "m53: comment vs code is different and survives ignore-unimportant", None),
    ("java-comment-vs-code-iu", "java", ["// note"], ["x;"],
     f"m53: options:{I} keeps comment vs code different", I),
    ("java-indent-ws", "java", ["    int x = 1;"], ["int x = 1;"],
     "m53: java has no Indent element; leading whitespace is unimportant", None),
    # ---- strings -----------------------------------------------------------
    ("java-string-internal-ws", "java", ['String s = "a b";'], ['String s = "ab";'],
     "m53: whitespace inside a closed string is important", None),
    ("java-string-unterminated-comment", "java",
     ['String s = "abc // x'], ['String s = "abc // y'],
     "m53: StopEOL string absorbs `//` as content", None),
    ("java-string-escape-comment", "java",
     ['s = "a\\" // x";'], ['s = "a\\" // y";'],
     "m53: Escape=92 keeps `\"` inside the string; `//` stays content", None),
    ("java-char-literal-case", "java", ["char c = 'a';"], ["char c = 'A';"],
     "m53: single-quote char literals are strings; case is important", None),
    ("java-char-unterminated-comment", "java",
     ["char c = 'x // y"], ["char c = 'x // z"],
     "m53: unterminated char literal runs to EOL as string content", None),
    # ---- alignment / folding ------------------------------------------------
    ("java-orphan-comment", "java", ["int a;", "int b;", "// c"], ["int x;"],
     "m53: leftover comment is leftsimilar beside a leftorphan", None),
    ("java-orphan-comment-iu", "java", ["int a;", "int b;", "// c"], ["int x;"],
     f"m53: options:{I} folds leftsimilar with the borrowed rtid", I),
    # ---- mask / fallback ------------------------------------------------------
    ("java-jav-ext", "jav", ["int value = 1;"], ["int Value = 1;"],
     "m53: the .jav mask selects the same JAVA grammar", None),
    ("java-plain-fallback", "foo", ["int value = 1;"], ["int Value = 1;"],
     "m53: unknown extensions stay plain text (case unimportant)", None),
    # ---- row-level regression -------------------------------------------------
    ("java-realistic", "java", REALISTIC_L.splitlines(), REALISTIC_R.splitlines(),
     "m53: 16-line class with comment + case changes; row truth from runs/m53-java-*",
     None),
]


def main() -> int:
    golden = REA / "verify" / "golden"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m53-anchors-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.app_version})")

    man_path = golden / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    shutil.copy2(man_path, run_dir / "manifest.json.before")
    new_keys = [f"m53-{a[0]}" for a in ANCHORS]
    clash = [k for k in new_keys if k in manifest]
    if clash:
        raise SystemExit(f"manifest already has keys: {clash}")

    added = 0
    for name, ext, ll, rl, note, options in ANCHORS:
        key = f"m53-{name}"
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
            "unit": "M5JavaGrammar",
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
