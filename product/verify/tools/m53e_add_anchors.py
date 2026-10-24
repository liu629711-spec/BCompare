#!/usr/bin/env python3
"""Build the M5.3 batch-3 (PAS/VB/REG/COBOL/DFM) golden anchors.

Re-records the live Oracle serially (standard in-place/Job-Object discipline)
and APPENDS manifest entries keyed ``m53e-``.  Shapes pin the measured rules
of docs/11 §28: Pascal directives vs brace comments, complete-match string
regexes, VB's unanchored `rem` and EOL-anchored string fallback, REG's
line-anchored comments, COBOL's unimportant LineNum columns, and DFM's
missing comment element.

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m53e_add_anchors.py
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

PAS_REAL_L = """\
program Hello;

{ prints a greeting }
begin
  writeln('hello world');
end.
"""

PAS_REAL_R = """\
program Hello;

{ prints a greeting (v2) }
begin
  writeln('HELLO WORLD');
end.
"""

VB_REAL_L = """\
' simple module
Sub Main()
    Dim S As String
    S = "hi"
    MsgBox S
End Sub
"""

VB_REAL_R = """\
' simple module (v2)
Sub Main()
    Dim S As String
    S = "HI"
    MsgBox S
End Sub
"""

COB72 = "IDENTIFICATION DIVISION.".ljust(72)

ANCHORS: list[tuple[str, str, list[str], list[str], str, str | None]] = [
    # ---- PAS ------------------------------------------------------------
    ("pas-case-ident", "pas", ["Value := 1;"], ["value := 1;"],
     "m53e: identifier case folds", None),
    ("pas-case-keyword", "pas", ["BEGIN X := 1; END."], ["begin x := 1; end."],
     "m53e: keyword case folds", None),
    ("pas-comment-line", "pas", ["x := 1; // alpha"], ["x := 1; // beta"],
     "m53e: `//` comment change is unimportant", None),
    ("pas-comment-line-iu", "pas", ["x := 1; // alpha"], ["x := 1; // beta"],
     f"m53e: options:{I} folds the comment-only change", I),
    ("pas-comment-brace", "pas", ["{ alpha } x := 1;"], ["{ beta } x := 1;"],
     "m53e: brace comment change is unimportant", None),
    ("pas-comment-paren", "pas", ["(* alpha *) x := 1;"], ["(* beta *) x := 1;"],
     "m53e: paren comment change is unimportant", None),
    ("pas-directive-vs-comment", "pas", ["{$X+}"], ["{$Y+}"],
     "m53e: compiler directives are IMPORTANT (vs brace comments)", None),
    ("pas-comment-brace-span", "pas",
     ["{", "body one", "} x := 1;"], ["{", "body two", "} x := 1;"],
     "m53e: brace comment bodies span lines", None),
    ("pas-comment-paren-span", "pas",
     ["(*", "body", "*) x := 1;"], ["(*", "body two", "*) x := 1;"],
     "m53f: paren comment bodies span lines", None),
    ("pas-string-doubled", "pas", ["x := 'It''s';"], ["x := 'It''s!';"],
     "m53e: `''` stays inside one string element", None),
    ("pas-char-literal", "pas", ["c := #65;"], ["c := #66;"],
     "m53e: `#65` char literals are strings", None),
    ("pas-string-unterminated-comment", "pas",
     ["x := 'abc // y"], ["x := 'abc // z"],
     "m53e: complete-match strings leave an unterminated `'`'s `//` a real comment",
     None),
    ("pas-realistic", "pas", PAS_REAL_L.splitlines(), PAS_REAL_R.splitlines(),
     "m53e: 6-line program; row truth from runs/m53e-*", None),
    # ---- VB ---------------------------------------------------------------
    ("vb-case-keyword", "bas", ["Dim X As Integer"], ["dim x as integer"],
     "m53e: keyword case folds", None),
    ("vb-comment-quote", "bas", ["x = 1 ' alpha"], ["x = 1 ' beta"],
     "m53e: `'` comment change is unimportant", None),
    ("vb-comment-rem", "bas", ["Rem alpha"], ["rem beta"],
     "m53e: `rem` comments are unimportant", None),
    ("vb-rem-midline", "bas", ["x = 1 rem alpha"], ["x = 1 rem beta"],
     "m53e: `rem ` matches UNANCHORED mid-line", None),
    ("vb-string-doubled", "bas", ['s = "a""b"'], ['s = "a""c"'],
     "m53e: `""` stays inside one string element", None),
    ("vb-string-unterminated", "bas", ['s = "abc'], ['s = "abd'],
     "m53e: EOL-anchored fallback absorbs an unterminated string", None),
    ("vb-string-unterminated-comment", "bas",
     ['s = "x \' a'], ['s = "x \' b'],
     "m53e: an absorbed `'` stays string content", None),
    ("vb-realistic", "bas", VB_REAL_L.splitlines(), VB_REAL_R.splitlines(),
     "m53e: 6-line module; row truth from runs/m53e-*", None),
    # ---- REG ----------------------------------------------------------------
    ("reg-line-comment", "ini", ["; alpha"], ["; beta"],
     "m53e: line-leading `;` comments are unimportant", None),
    ("reg-midline-semicolon", "ini", ["x = 1 ; note"], ["x = 1 ; other"],
     "m53e: mid-line `;` stays unclaimed text (line-anchored comment)", None),
    ("reg-string", "ini", ['a="x"'], ['a="y"'],
     "m53e: string contents compare verbatim", None),
    ("reg-string-unterminated-comment", "ini",
     ['a="x ; y'], ['a="x ; z'],
     "m53e: StopEOL strings absorb a later `;`", None),
    ("reg-keyword-case", "ini", ["a=dword:00000001"], ["a=DWORD:00000001"],
     "m53f: `dword` keyword is case-sensitive", None),
    # ---- COBOL ----------------------------------------------------------------
    ("cobol-linenum", "cbl",
     ["000100 IDENTIFICATION DIVISION."], ["000200 IDENTIFICATION DIVISION."],
     "m53e: columns 1-6 LineNum are unimportant", None),
    ("cobol-comment-col7", "cbl",
     ["000100* note", "000200       DISPLAY 'X'."],
     ["000300* other", "000200       DISPLAY 'X'."],
     "m53e: column-7 `*` comments the rest of the line", None),
    ("cobol-linenum-trailer", "cbl",
     [COB72 + "00010001"], [COB72 + "00020002"],
     "m53e: columns 73-80 LineNum are unimportant", None),
    ("cobol-star-not-col7", "cbl",
     ["000100       DISPLAY X * Y."], ["000100       DISPLAY X * Z."],
     "m53f: a `*` outside column 7 stays an operator", None),
    ("cobol-string", "cbl", ["000100       DISPLAY 'X'."],
     ["000100       DISPLAY 'Y'."],
     "m53e: string contents compare verbatim", None),
    # ---- DFM ------------------------------------------------------------------
    ("dfm-case-keyword", "dfm", ["object A: B"], ["OBJECT A: B"],
     "m53e: keyword case folds", None),
    ("dfm-char-literal", "dfm", ["Text = #65"], ["Text = #66"],
     "m53e: `#65` char literals are strings", None),
    ("dfm-string-doubled", "dfm", ["Caption = 'It''s'"], ["Caption = 'It''x'"],
     "m53e: `''` stays inside one string element", None),
    ("dfm-no-comment", "dfm", ["{ note }"], ["{ other }"],
     "m53e: DFM has no comment element; `{` is unclaimed text", None),
]


def main() -> int:
    golden = REA / "verify" / "golden"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m53e-anchors-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.app_version})")

    man_path = golden / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    shutil.copy2(man_path, run_dir / "manifest.json.before")
    new_keys = [f"m53e-{a[0]}" for a in ANCHORS]
    clash = [k for k in new_keys if k in manifest]
    if clash:
        raise SystemExit(f"manifest already has keys: {clash}")

    added = 0
    for name, ext, ll, rl, note, options in ANCHORS:
        key = f"m53e-{name}"
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
            "unit": "M5PasVbRegCobolDfm",
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
