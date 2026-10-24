#!/usr/bin/env python3
"""U2 probe -- importance edges the U1 table leaves open (M2 prerequisite).

U1 settled the per-element rule for single-class single-line .c pairs: a
changed line is unimportant iff every differing element is a comment or
whitespace element.  That probe deliberately left several boundaries open
(recorded in U1-FINDINGS.md "Boundaries of this evidence"):

  * mixed lines        -- comment + code on one line (implied, not probed)
  * block comments     -- multi-line /* */ bodies, `*` continuation lines
  * string interiors   -- whitespace/case INSIDE a string literal
  * other formats      -- .py (Indent element, trailing-ws-as-comment, triple
                          quotes), .js (regex literals), unknown extensions
  * alignment          -- do trailing-comment lines align with other
                          trailing-comment lines; do comment lines align
                          forward in a longer file
  * blank/comment vs empty

Method identical to U1: minimal pairs through the live Oracle as
``text-report layout:xml`` in two modes (default, ``options:ignore-
unimportant``), every call through ``harness.oracle`` (in-place cwd, Job
Object, timeout), serial.  Raw outputs land in
``product/verify/runs/u2-probe-<ts>/``; the interpreted table is printed and
written to ``U2-FINDINGS.md`` next to this script.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u2_element_edges.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

#: (probe name, extension, left lines, right lines).  One intent per pair.
PAIRS = [
    # ---- .c: mixed lines (the U1 "implied" cases) -----------------------
    ("mixed-trailing-comment", "c",
     ["int x = 1; // note"], ["int x = 1; // other"]),
    ("mixed-lead-comment", "c",
     ["/* head */ int x;"], ["/* tail */ int x;"]),
    # ---- .c: block comments ---------------------------------------------
    ("block-comment-body", "c",
     ["/*", "alpha body", "*/", "int x;"],
     ["/*", "beta body", "*/", "int x;"]),
    ("block-continuation-star", "c",
     ["/*", " * alpha", " */", "int x;"],
     ["/*", " * beta", " */", "int x;"]),
    # ---- .c: string interiors -------------------------------------------
    ("string-internal-ws", "c",
     ['char *a = "a b";'], ['char *a = "a  b";']),
    ("string-case", "c",
     ['char *a = "ABC";'], ['char *a = "abc";']),
    ("string-unterminated", "c",
     ['char *a = "abc'], ['char *a = "abd']),
    ("string-escaped-quote", "c",
     ['char *a = "a\\"b";'], ['char *a = "a\\"c";']),
    # ---- .c: comment/blank taxonomy -------------------------------------
    ("comment-syntax-swap", "c", ["// a"], ["/* a */"]),
    ("comment-vs-empty", "c", ["// note"], [""]),
    ("blank-vs-ws", "c", [""], ["   "]),
    # ---- .c: number shapes ----------------------------------------------
    ("number-hex", "c", ["int a = 0x10;"], ["int a = 0x20;"]),
    ("number-exponent", "c", ["double a = 1.5e3;"], ["double a = 1.5e4;"]),
    # ---- .c: alignment semantics (multi-line) ----------------------------
    ("align-swap-trailing-comment", "c",
     ["int a;", "x = 1; // one"],
     ["x = 1; // two", "int a;"]),
    ("align-comments-forward", "c",
     ["// a", "// b", "int x;"],
     ["// c", "int x;"]),
    # ---- .py -------------------------------------------------------------
    ("py-comment", "py", ["# alpha"], ["# beta"]),
    ("py-indent", "py", ["x = 1"], ["    x = 1"]),
    ("py-trailing-ws", "py", ["x = 1   "], ["x = 1"]),
    ("py-hash-midline", "py", ["x = 1  # alpha"], ["x = 1  # beta"]),
    ("py-triple-quote", "py",
     ["'''", "a b", "'''"], ["'''", "a  b", "'''"]),
    ("py-string-case", "py", ['x = "Abc"'], ['x = "abc"']),
    # ---- .js -------------------------------------------------------------
    ("js-comment", "js", ["// alpha"], ["// beta"]),
    ("js-regex-literal", "js", ["var r = /ab/g;"], ["var r = /ac/g;"]),
    ("js-regex-ws", "js", ["var r = /a b/g;"], ["var r = /ab/g;"]),
    ("js-string-quote", "js", ["var s = 'ab';"], ["var s = 'ac';"]),
    ("js-template-literal", "js",
     ["var t = `a b`;"], ["var t = `a c`;"]),
    # ---- unknown extension ------------------------------------------------
    ("foo-case", "foo", ["Alpha"], ["alpha"]),
    ("foo-comment", "foo", ["// alpha"], ["// beta"]),
    ("foo-syntax", "foo", ["int x = 10;"], ["long x = 20;"]),
    ("foo-comment-vs-code", "foo", ["// note"], ["x;"]),
]

MODES = [None, "ignore-unimportant"]

STATUS_RE = re.compile(r'<linecomp status="([a-z]+)"')


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u2-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")
    print(f"run dir: {run_dir}\n")

    records = []
    for name, ext, left_lines, right_lines in PAIRS:
        left = run_dir / "fixtures" / f"{name}-L.{ext}"
        right = run_dir / "fixtures" / f"{name}-R.{ext}"
        left.write_text("\n".join(left_lines) + "\n", encoding="utf-8")
        right.write_text("\n".join(right_lines) + "\n", encoding="utf-8")
        for mode in MODES:
            tag = name if mode is None else f"{name}+iu"
            out = run_dir / "reports" / f"{tag}.xml"
            script = orc.write_script(
                run_dir / "reports" / f"{tag}.bcs",
                [orc.text_script("xml", mode)])
            run = orc.run(cur.oracle_path, script, left, right, out,
                          timeout=120.0, script_text=orc.text_script("xml", mode))
            statuses = []
            if run.report_exists:
                statuses = STATUS_RE.findall(
                    out.read_bytes().decode("utf-8-sig", errors="replace"))
            records.append({
                "probe": name, "ext": ext, "mode": mode or "default",
                "tag": tag,
                "left": left_lines, "right": right_lines,
                "exit": run.exit_code, "statuses": statuses,
                "containment": run.containment,
            })
            print(f"  {tag:<34} exit={run.exit_code} statuses={statuses}")

    # ---- interpret ------------------------------------------------------
    by_probe: dict[str, dict[str, list[str]]] = {}
    for r in records:
        by_probe.setdefault(r["probe"], {})[r["mode"]] = r["statuses"]

    print("\n=== U2 observed table (live Oracle) ===")
    print(f"{'probe':<30} {'default':<34} {'ignore-unimportant':<24}")
    for name, ext, ll, rl in PAIRS:
        d = by_probe[name].get("default", [])
        iu = by_probe[name].get("ignore-unimportant", [])
        ds = ",".join(d) or "(none)"
        is_ = ",".join(iu) or "(none)"
        print(f"{name + '.' + ext:<30} {ds:<34} {is_:<24}")

    (run_dir / "u2-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw results: {run_dir / 'u2-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
