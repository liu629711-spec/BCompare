#!/usr/bin/env python3
"""M5.3 probe -- JAVA grammar discriminators (BC truth recording).

The product currently falls back to plain text for `.java`/`.jav` (a recorded
M2 known difference: a case-only change reports `similar` where BC's JAVA
grammar should report `different`).  Before implementing `Grammar::Java` this
probe records the live Oracle's verdict for one fixture pair per rule, so the
implementation targets measured behaviour instead of the spec JSON alone.

Each case isolates one grammar question; the predicted status comes from the
`bcfileformats-spec.json` JAVA grammar plus the U1 contract (verdict = only
comment/whitespace elements may differ, everything else compares verbatim):

  case-ident       identifier case-only change          -> different (KD closes)
  case-keyword     keyword case-only change             -> different
  comment-line     trailing `//` text differs           -> similar
  comment-block    `/* ... */` spans lines, body differs -> similar
  comment-vs-blank comment line vs empty line           -> similar
  indent-ws        leading indentation differs          -> similar (no Indent el)
  ws-code          intra-code whitespace differs        -> similar
  str-ws-inside    whitespace inside a closed string    -> different (content)
  str-vs-comment   `//` inside an unterminated string   -> different (StopEOL)
  str-vs-block     `/*` inside an unterminated string, next line code
                                                        -> different (no leak)
  str-escape       `\"` then `//` inside string         -> different (Escape=92)
  char-literal     single-quote literal case change     -> different
  char-unterminated `'` then `//` inside string         -> different (StopEOL)
  mixed-case-comment code case differs, comment same    -> different
  realistic        12-line class, three change kinds    -> mixed (row-level)
  plain-control    same case-only change on `.foo`      -> similar (fallback)

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m53_java_grammar.py
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

#: (tag, ext, left lines, right lines, predicted statuses in linecomp order)
CASES = [
    ("case-ident", ".java", ["int value = 1;"], ["int Value = 1;"], ["different"]),
    ("case-keyword", ".java", ["if (x) { return; }"], ["IF (x) { RETURN; }"], ["different"]),
    ("comment-line", ".java", ["int x = 1; // alpha"], ["int x = 1; // beta"], ["similar"]),
    ("comment-block", ".java",
     ["/* head", "body one", "*/ int y = 1;"],
     ["/* head", "body two", "*/ int y = 1;"],
     ["similar", "similar", "similar"]),
    ("comment-vs-blank", ".java", ["// note", "int x = 1;"], ["", "int x = 1;"],
     ["similar", "same"]),
    ("indent-ws", ".java", ["    int x = 1;"], ["int x = 1;"], ["similar"]),
    ("ws-code", ".java", ["int x = 1;"], ["int  x = 1;"], ["similar"]),
    ("str-ws-inside", ".java", ['String s = "a b";'], ['String s = "ab";'], ["different"]),
    ("str-vs-comment", ".java", ['String s = "abc // x'], ['String s = "abc // y'],
     ["different"]),
    ("str-vs-block", ".java",
     ['String s = "x /* y', "int z = 1;"],
     ['String s = "x /* y', "int z = 2;"],
     ["same", "different"]),
    ("str-escape", ".java", ['s = "a\\" // x";'], ['s = "a\\" // y";'], ["different"]),
    ("char-literal", ".java", ["char c = 'a';"], ["char c = 'A';"], ["different"]),
    ("char-unterminated", ".java", ["char c = 'x // y"], ["char c = 'x // z"], ["different"]),
    ("mixed-case-comment", ".java", ["int X = 1; // c"], ["int x = 1; // c"], ["different"]),
    ("realistic", ".java", REALISTIC_L.splitlines(), REALISTIC_R.splitlines(), None),
    ("plain-control", ".foo", ["int value = 1;"], ["int Value = 1;"], ["similar"]),
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
               datetime.now(timezone.utc).strftime("m53-java-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
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
    (run_dir / "m53-results.json").write_text(json.dumps(
        {"cases": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"raw: {run_dir / 'm53-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
