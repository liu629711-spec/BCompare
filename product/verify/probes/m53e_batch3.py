#!/usr/bin/env python3
"""M5.3 batch-3 probe -- PAS / VB / REG / COBOL / DFM grammar discriminators.

Same protocol as the earlier m53 probes: one fixture pair per rule, serial
Oracle, archived truth under ``runs/m53e-*``.  Predictions come from the
spec JSON plus the case policies already measured for SQL (Keyword /
Identifier with CaseSensitive=False fold; complete-match string regexes
leave unterminated quotes to ordinary tokenizing).

Measured questions this round:

  PAS   `{$...}` DIRECTIVE vs `{...}` COMMENT ordering; `{ }` and `(* *)`
        span lines; strings are complete-match (`'..'` with `''` doubling,
        `#65` char literals) so an unterminated `'` leaves `//` a real
        comment; keyword/identifier case folds.
  VB    `'` and `rem ` comments to EOL; strings are regexes with an
        EOL-anchored fallback (`"..."` unterminated still matches to end of
        line) and `""` doubling; case folds.
  REG   comments are LINE-ANCHORED (`^\\s*;`) so a mid-line `;` stays
        important; strings carry Escape=92 and StopEOL.
  COBOL LineNum class (cols 1-6 and 73-80) importance is UNKNOWN -- probed;
        col-7 `*` comment lines; `"` strings StopEOL.
  DFM   keywords fold; `#65` and `'..'` string regexes; NO comment element
        (`{` is unclaimed text).

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m53e_batch3.py
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
CASES = [
    # ---- PAS ------------------------------------------------------------
    ("pas-case-ident", ".pas", ["Value := 1;"], ["value := 1;"], ["similar"]),
    ("pas-case-keyword", ".pas", ["BEGIN X := 1; END."], ["begin x := 1; end."],
     ["similar"]),
    ("pas-comment-line", ".pas", ["x := 1; // alpha"], ["x := 1; // beta"], ["similar"]),
    ("pas-comment-brace", ".pas", ["{ alpha } x := 1;"], ["{ beta } x := 1;"],
     ["similar"]),
    ("pas-comment-paren", ".pas", ["(* alpha *) x := 1;"], ["(* beta *) x := 1;"],
     ["similar"]),
    ("pas-directive-vs-comment", ".pas", ["{$X+}"], ["{$Y+}"], ["different"]),
    ("pas-comment-brace-span", ".pas",
     ["{", "body one", "} x := 1;"], ["{", "body two", "} x := 1;"],
     ["same", "similar", "same"]),
    ("pas-string-doubled", ".pas", ["x := 'It''s';"], ["x := 'It''s!';"],
     ["different"]),
    ("pas-char-literal", ".pas", ["c := #65;"], ["c := #66;"], ["different"]),
    ("pas-string-unterminated-comment", ".pas",
     ["x := 'abc // y"], ["x := 'abc // z"], ["similar"]),
    ("pas-realistic", ".pas", PAS_REAL_L.splitlines(), PAS_REAL_R.splitlines(), None),
    # ---- VB ---------------------------------------------------------------
    ("vb-case-keyword", ".bas", ["Dim X As Integer"], ["dim x as integer"],
     ["similar"]),
    ("vb-comment-quote", ".bas", ["x = 1 ' alpha"], ["x = 1 ' beta"], ["similar"]),
    ("vb-comment-rem", ".bas", ["Rem alpha"], ["rem beta"], ["similar"]),
    ("vb-rem-midline", ".bas", ["x = 1 rem alpha"], ["x = 1 rem beta"], None),
    ("vb-string-doubled", ".bas", ['s = "a""b"'], ['s = "a""c"'], ["different"]),
    ("vb-string-unterminated", ".bas", ['s = "abc'], ['s = "abd'], ["different"]),
    ("vb-string-unterminated-comment", ".bas",
     ['s = "x \' a'], ['s = "x \' b'], None),
    ("vb-realistic", ".bas", VB_REAL_L.splitlines(), VB_REAL_R.splitlines(), None),
    # ---- REG ----------------------------------------------------------------
    ("reg-line-comment", ".ini", ["; alpha"], ["; beta"], ["similar"]),
    ("reg-midline-semicolon", ".ini", ["x = 1 ; note"], ["x = 1 ; other"],
     ["different"]),
    ("reg-string", ".ini", ['a="x"'], ['a="y"'], ["different"]),
    ("reg-string-unterminated-comment", ".ini",
     ['a="x ; y'], ['a="x ; z'], ["different"]),
    # ---- COBOL ----------------------------------------------------------------
    ("cobol-linenum", ".cbl",
     ["000100 IDENTIFICATION DIVISION."],
     ["000200 IDENTIFICATION DIVISION."], None),
    ("cobol-comment-col7", ".cbl",
     ["000100* note", "000200       DISPLAY 'X'."],
     ["000300* other", "000200       DISPLAY 'X'."], None),
    ("cobol-linenum-trailer", ".cbl",
     [COB72 + "00010001"], [COB72 + "00020002"], None),
    ("cobol-string", ".cbl", ["000100       DISPLAY 'X'."],
     ["000100       DISPLAY 'Y'."], ["different"]),
    # ---- DFM ------------------------------------------------------------------
    ("dfm-case-keyword", ".dfm", ["object A: B"], ["OBJECT A: B"], ["similar"]),
    ("dfm-char-literal", ".dfm", ["Text = #65"], ["Text = #66"], ["different"]),
    ("dfm-string-doubled", ".dfm", ["Caption = 'It''s'"], ["Caption = 'It''x'"],
     ["different"]),
    ("dfm-no-comment", ".dfm", ["{ note }"], ["{ other }"], ["different"]),
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
               datetime.now(timezone.utc).strftime("m53e-batch3-%Y%m%dT%H%M%SZ"))
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
        results.append({
            "tag": tag, "ext": ext, "predicted": predicted,
            "oracle_rows": o_rows, "product_rows": p_rows, "verdict": verdict,
        })
        print(f"[{tag}] oracle={o_status}  {verdict}")
        if o_rows != p_rows:
            print(f"    product(now)={ [r[0] for r in p_rows] }")

    n_ok = sum(1 for r in results if r["verdict"] == "OK" or r["verdict"] == "n/a")
    n_miss = sum(1 for r in results if r["verdict"].startswith("PREDICT-MISS"))
    print(f"\npredictions: {n_ok} ok, {n_miss} miss "
          f"(None = recording unknown truth; row truth archived)")
    (run_dir / "m53e-results.json").write_text(json.dumps(
        {"cases": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"raw: {run_dir / 'm53e-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
