#!/usr/bin/env python3
"""M5.3 batch-4 probe -- BASH / PERL grammar discriminators (final text grammars).

Same protocol as the m53 series: one fixture pair per rule, serial Oracle,
archived truth under ``runs/m53g-*``.  These two grammars carry the mechanisms
the earlier batches never used, and each question below is decided by BC, not
by shell/Perl semantics:

  BASH:  `'`, `$'`, `"`, `$"` strings declare StopText WITHOUT StopEOL --
         do they really span lines?  EnvironmentVar `$NAME/${NAME}/$@` is a
         CaseSensitive=False element: does `$FOO` vs `$foo` fold -- and stay
         verbatim inside strings?  Is `#` unanchored (mid-`x=a#b`)?
  PERL:  `'`/`"` with Escape=92 and NO StopEOL -- multi-line?  POD blocks
         `=pod/=head/=item` -> `=cut`, `=over`->`=back` (line-anchored start;
         is the stop line-anchored too?).  The IsRegExp String list: does
         `/.../` really absorb `/ b /` between divisions?  `q(...)`, `s///`.
  Both:  keyword elements have no CaseSensitive attr (case-sensitive) while
         identifiers fold -- `if` vs `IF` (K vs ci-O) is the class-pair test
         that decided HTML entities (m53d); what does BC do here?

Cases with predicted=None are open questions (recorded, not guessed).

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m53g_bash_perl.py
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

BASH_REAL_L = """\
#!/bin/bash
# greet the user
NAME=world

greet() {
    echo "hello $NAME"  # greeting
}

greet
"""

BASH_REAL_R = """\
#!/bin/bash
# greet the user
NAME=World

greet() {
    echo "hello $NAME"  # salutation
}

greet
"""

PERL_REAL_L = """\
#!/usr/bin/perl
# main program

=pod
Documentation block
=cut

sub greet {
    my ($name) = @_;
    return "hello $name";
}

print greet("world");
"""

PERL_REAL_R = """\
#!/usr/bin/perl
# main program

=pod
Documentation block v2
=cut

sub greet {
    my ($Name) = @_;
    return "hello $name";
}

print greet("world");
"""

CASES = [
    # ---- BASH ------------------------------------------------------------
    ("bash-keyword-case", ".sh", ["if x; then"], ["IF x; THEN"], None),
    ("bash-ident-case", ".sh", ["name=1"], ["NAME=1"], ["similar"]),
    ("bash-envvar-case", ".sh", ["echo $FOO"], ["echo $foo"], None),
    ("bash-envvar-brace-case", ".sh", ["echo ${FOO}"], ["echo ${foo}"], None),
    ("bash-envvar-in-string", ".sh", ['echo "$FOO"'], ['echo "$foo"'], ["different"]),
    ("bash-str-multi-hash", ".sh", ["x='a", "# alpha"], ["x='a", "# beta"], None),
    ("bash-dquote-multi-hash", ".sh", ['x="a', "# alpha"], ['x="a', "# beta"], None),
    ("bash-comment-line", ".sh", ["echo hi # alpha"], ["echo hi # beta"], ["similar"]),
    ("bash-mid-hash", ".sh", ["x=a#b"], ["x=a#c"], None),
    ("bash-dollar-quote", ".sh", ["x=$'a b'"], ["x=$'a c'"], ["different"]),
    ("bash-dollar-dquote", ".sh", ['x=$"ab"'], ['x=$"ac"'], ["different"]),
    ("bash-dquote-escape", ".sh", ['x="a\\"b"'], ['x="a\\"c"'], ["different"]),
    ("bash-squote-noescape", ".sh", ["x='a\\b'"], ["x='a\\c'"], ["different"]),
    ("bash-hex-case", ".sh", ["x=0x1F"], ["x=0x1f"], None),
    ("bash-realistic", ".sh", BASH_REAL_L.splitlines(), BASH_REAL_R.splitlines(), None),
    # ---- PERL --------------------------------------------------------------
    ("perl-ident-case", ".pl", ["my $Name = 1;"], ["my $name = 1;"], None),
    ("perl-keyword-case", ".pl", ["if (1) { exit; }"], ["IF (1) { EXIT; }"], None),
    ("perl-comment", ".pl", ["$x = 1; # alpha"], ["$x = 1; # beta"], ["similar"]),
    ("perl-pod-block", ".pl", ["=pod", "body one", "=cut", "code();"],
     ["=pod", "body two", "=cut", "code();"], ["same", "similar", "same", "same"]),
    ("perl-pod-item", ".pl", ["=item alpha"], ["=item beta"], None),
    ("perl-pod-mid-cut", ".pl", ["=pod", "x =cut y", "z"], ["=pod", "x =cut y", "w"], None),
    ("perl-pod-unterminated", ".pl", ["=pod", "x"], ["=pod", "y"], None),
    ("perl-over-back", ".pl", ["=over", "body one", "=back"],
     ["=over", "body two", "=back"], None),
    ("perl-regex-division", ".pl", ["$x = a / b / c;"], ["$x = a / d / c;"], None),
    ("perl-regex-hash", ".pl", ["$s = /a # b/;"], ["$s = /a # c/;"], None),
    ("perl-q-paren", ".pl", ["$w = q(alpha);"], ["$w = q(beta);"], None),
    ("perl-s-form-case", ".pl", ["s/ONE/TWO/;"], ["s/one/two/;"], None),
    ("perl-str-escape", ".pl", ["$x = 'a\\'b';"], ["$x = 'a\\'c';"], ["different"]),
    ("perl-dquote-multi-hash", ".pl", ['$x = "a', "# b"], ['$x = "a', "# c"], None),
    ("perl-squote-multi-hash", ".pl", ["$x = 'a", "# b"], ["$x = 'a", "# c"], None),
    ("perl-array-sigil", ".pl", ["@Items = (1);"], ["@items = (1);"], None),
    ("perl-realistic", ".pl", PERL_REAL_L.splitlines(), PERL_REAL_R.splitlines(), None),
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
               datetime.now(timezone.utc).strftime("m53g-bash-perl-%Y%m%dT%H%M%SZ"))
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
        verdict = "open" if predicted is None else (
            "OK" if o_status == predicted else f"PREDICT-MISS expected={predicted}")
        results.append({
            "tag": tag, "ext": ext, "predicted": predicted,
            "oracle_rows": o_rows, "product_rows": p_rows, "verdict": verdict,
        })
        print(f"[{tag}] oracle={o_status}  {verdict}")

    n_ok = sum(1 for r in results if r["verdict"] == "OK")
    n_miss = sum(1 for r in results if r["verdict"].startswith("PREDICT-MISS"))
    n_open = sum(1 for r in results if r["verdict"] == "open")
    print(f"\npredictions: {n_ok} ok, {n_miss} miss, {n_open} open questions recorded")
    (run_dir / "m53g-results.json").write_text(json.dumps(
        {"cases": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"raw: {run_dir / 'm53g-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
