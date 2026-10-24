#!/usr/bin/env python3
"""Build the M5.3 PERL golden anchors (batch 4, final text grammar).

Re-records the live Oracle serially and APPENDS ``m53p-`` manifest entries.
Shapes pin docs/11 §29: everything compares verbatim (the CaseSensitive=False
flag changes tokenization only), POD blocks stop at line-anchored markers
whose full line belongs to the comment, `"`/`'` strings span lines (StopText
without StopEOL) and absorb `#`, and the quote-like forms apply as complete
matches in spec order (`q(...)`, `s/.../.../`, division-shaped `/.../`; NO
`#`-delimited forms).

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m53p_add_anchors.py
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

ANCHORS = [
    ("perl-verbatim-case", "pl", ["my $Name = 1;"], ["my $name = 1;"],
     "m53g: everything compares verbatim; case folds for NO element", None),
    ("perl-bare-word-case", "pl", ["Name = 1;"], ["name = 1;"],
     "m53m: bare identifier case is different (CaseSensitive=False is tokenizing only)",
     None),
    ("perl-comment", "pl", ["$x = 1; # alpha"], ["$x = 1; # beta"],
     "m53g: `#` comment change is unimportant", None),
    ("perl-comment-iu", "pl", ["$x = 1; # alpha"], ["$x = 1; # beta"],
     f"m53g: options:{I} folds the comment-only change", I),
    ("perl-leading-comment", "pl", ["# alpha"], ["# beta"],
     "m53h: leading `#` is a comment (no shebang special case)", None),
    ("perl-pod-block", "pl", ["=pod", "body one", "=cut", "code();"],
     ["=pod", "body two", "=cut", "code();"],
     "m53g: POD bodies are unimportant; stop line is exact", None),
    ("perl-pod-stop-tail", "pl", ["=pod", "b", "=cut Z1", "code();"],
     ["=pod", "b", "=cut Z2", "code();"],
     "m53k: the whole stop line belongs to the comment (Z1 vs Z2 similar)", None),
    ("perl-pod-mid-cut", "pl", ["=pod", "x =cut y", "z"], ["=pod", "x =cut y", "w"],
     "m53g: a mid-line stop marker does NOT close the block", None),
    ("perl-pod-over-back", "pl", ["=over", "body one", "=back"],
     ["=over", "body two", "=back"],
     "m53g: =over/=back is a second POD pairing", None),
    ("perl-str-multi-hash", "pl", ['$x = "a', "# b"], ['$x = "a', "# c"],
     "m53g: StopText-without-StopEOL: string spans lines and absorbs `#`", None),
    ("perl-str-closed-next-line", "pl",
     ['$x = "a', 'b"; # one', "code();"], ['$x = "a', 'b"; # two', "code();"],
     "m53k: a column-0 close ends the span; later `#` is a real comment", None),
    ("perl-regex-division", "pl", ["$x = a / b / c;"], ["$x = a / d / c;"],
     "m53g: the division-shaped `/[^/]*/` element is real", None),
    ("perl-regex-hash", "pl", ["$s = /a # b/;"], ["$s = /a # c/;"],
     "m53g: a matched regex absorbs `#`", None),
    ("perl-q-paren", "pl", ["$w = q(alpha);"], ["$w = q(beta);"],
     "m53g: q(...) quote-like forms are strings", None),
    ("perl-s-slash-hash", "pl", ["s/a # b/c/;"], ["s/a # b/d/;"],
     "m53l: s/.../.../ absorbs `#` in its segments", None),
    ("perl-s-hash-not-form", "pl", ["s#a#b#c#d#;"], ["s#a#b#c#e#;"],
     "m53l: NO #-delimited forms -- first `#` is the comment", None),
    ("perl-realistic", "pl", PERL_REAL_L.splitlines(), PERL_REAL_R.splitlines(),
     "m53g: 13-line script; row truth from runs/m53g-*", None),
    # BASH: measured plain-text behaviour (m53g-m53j); pinned as anchors so
    # the plain comparison stays the spec even as grammars grow around it.
    ("bash-plain-case", "sh", ['echo "abc"'], ['echo "ABC"'],
     "m53j: .sh compares as plain text (case unimportant, strings included)", None),
    ("bash-plain-hash", "sh", ["# alpha"], ["# beta"],
     "m53h: leading `#` differences are important text in .sh (no comment rule)", None),
    ("bash-plain-var", "sh", ["echo $FOO"], ["echo $foo"],
     "m53g: env-var case folds like all plain text", None),
    ("bash-realistic", "sh",
     ["#!/bin/bash", "# greet the user", 'NAME=world', "", "greet() {",
      '    echo "hello $NAME"  # greeting', "", "greet"],
     ["#!/bin/bash", "# greet the user", "NAME=World", "", "greet() {",
      '    echo "hello $NAME"  # salutation', "", "greet"],
     "m53g: 8-line script; row truth (NAME change different, comment line similar "
     "by plain fold)", None),
]


def main() -> int:
    golden = REA / "verify" / "golden"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REA / "product" / "verify" / "runs" / f"m53p-anchors-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.app_version})")

    man_path = golden / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    shutil.copy2(man_path, run_dir / "manifest.json.before")
    new_keys = [f"m53p-{a[0]}" for a in ANCHORS]
    clash = [k for k in new_keys if k in manifest]
    if clash:
        raise SystemExit(f"manifest already has keys: {clash}")

    added = 0
    for name, ext, ll, rl, note, options in ANCHORS:
        key = f"m53p-{name}"
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
            "unit": "M5PerlGrammar",
            "note": note,
            "exit_code": run.exit_code,
            "statuses": statuses,
            "seconds": seconds,
            "left": str(left),
            "right": str(right),
            "report": str(report),
        }
        added += 1
        print(f"  {key:<42} statuses={statuses}")

    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"\nadded {added} anchors; manifest now {len(manifest)} entries")
    print(f"run dir: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
