#!/usr/bin/env python3
"""M4 gate -- script-level Oracle comparison for the CLI/script subset.

Milestone M4's acceptance is: **given a script, this tool and BC produce
equivalent reports** (`product/docs/04-milestones.md` M4).  This runner is that
acceptance: it takes a corpus of scripts, runs each one through the Oracle and
through the product, and compares exit codes and normalized report bytes.

Design
------

* Every case declares its script lines with ``%1 %2 %3`` where the paths go, so
  one corpus entry drives both engines (the Oracle's own convention, see
  ``harness/oracle.py``).  Only ``%3`` (the output path) differs between the two
  runs.
* Fixtures are materialised under the run directory with pinned mtimes, so the
  archived reports — including their ``<modified>`` columns — are reproducible
  rather than merely same-run-consistent.
* The verdict is a comparison, never a declaration: an ``expected_exit`` is
  recorded for each case (each one traceable to a measurement), and a case fails
  if either engine disagrees with it OR if the two normalized reports differ.
* The Oracle runs through ``harness.oracle``: in place, ``/silent``, inside a
  Windows job object, one call at a time.  This runner must not run concurrently
  with itself, with pytest, or with any other Oracle user.

Usage:
    cd D:\\Rea\\product\\verify
    python tools/m4_gate.py                    # every case
    python tools/m4_gate.py --filter filter    # only cases whose name matches
    python tools/m4_gate.py --list             # list the corpus, run nothing
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
VERIFY = REA / "product" / "verify"
sys.path.insert(0, str(VERIFY))

from harness import installs as inst_mod  # noqa: E402
from harness import normalize as norm_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

#: The product binary the harness declares (``harness/candidate.py``), so the
#: path lives in one place.  The M1 template does not describe the M4 command
#: shapes, so the commands below are built here from this path.
PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

#: A fixed instant for fixture mtimes, so the archived reports are reproducible.
FIXED_MTIME = 1_767_225_600  # 2026-01-01T08:00:00Z


# ==========================================================================
# The corpus
# ==========================================================================
# Each case:
#   name        -- stable id, also the report file stem
#   kind        -- "text" (file pair) | "folder" (folder pair)
#   fixture     -- the name of a fixture pair builder (see FIXTURES)
#   script      -- the script lines; %1 %2 %3 substitute left, right, output
#   expect      -- the exit code both engines must return
#   evidence    -- where expect comes from (probe file / case id)
#   report      -- True when a report is expected to exist (default True)
#   second_report -- True when the script writes a second report to compare
#   known_difference -- a reason string, for cases whose REPORT is known not to
#                       be byte-equivalent.  Such a case is still run and its
#                       difference is still recorded in full; it is counted in
#                       its own category rather than as a pass or a failure,
#                       because neither "we match" nor "we are broken" is true.
#                       Deleting the case would hide the gap.
#
# ``evidence`` is mandatory: a case with no measured basis for its expected exit
# would be asserting our own behaviour back at ourselves.

SCRIPT_CASES: list[dict] = [
    # ---- text reports: every layout -----------------------------------
    dict(name="text-xml", kind="text", fixture="text-differ",
         script=['text-report layout:xml output-to:"%3" "%1" "%2"'],
         expect=0, evidence="M1 corpus (101 anchors): text-report layout:xml exits 0"),
    dict(name="text-side-by-side", kind="text", fixture="text-differ",
         script=['text-report layout:side-by-side output-to:"%3" "%1" "%2"'],
         expect=0, evidence="M2 layouts corpus (31 cases)"),
    dict(name="text-summary", kind="text", fixture="text-differ",
         script=['text-report layout:summary output-to:"%3" "%1" "%2"'],
         expect=0, evidence="M2 layouts corpus"),
    dict(name="text-interleaved", kind="text", fixture="text-differ",
         script=['text-report layout:interleaved output-to:"%3" "%1" "%2"'],
         expect=0, evidence="M2 layouts corpus"),
    dict(name="text-patch", kind="text", fixture="text-differ",
         script=['text-report layout:patch output-to:"%3" "%1" "%2"'],
         expect=0, evidence="M2 layouts corpus"),
    dict(name="text-statistics", kind="text", fixture="text-differ",
         script=['text-report layout:statistics output-to:"%3" "%1" "%2"'],
         expect=0, evidence="M2 layouts corpus"),
    dict(name="text-python-grammar", kind="text", fixture="py-differ",
         script=['text-report layout:xml output-to:"%3" "%1" "%2"'],
         expect=0, evidence="probes/u5l: python pair, Oracle statuses same+different"),
    dict(name="text-c-grammar", kind="text", fixture="c-differ",
         script=['text-report layout:xml output-to:"%3" "%1" "%2"'],
         expect=0, evidence="probes/u5l: C pair, Oracle statuses same+similar+same"),

    # ---- the multi-line form the official samples use ------------------
    dict(name="text-multiline-continuation", kind="text", fixture="text-differ",
         script=['# A report command split with the official continuation form.',
                 'text-report layout:xml &',
                 '  output-to:"%3" &',
                 '  "%1" "%2"'],
         expect=0, evidence="help/sample_scripts.html (the '&' continuation)"),

    # ---- folder reports: every layout ---------------------------------
    dict(name="folder-xml-expand-all", kind="folder", fixture="folder-mixed",
         script=['load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5g s2 / u5d expand-all"),
    dict(name="folder-summary-expand-all", kind="folder", fixture="folder-mixed",
         script=['load "%1" "%2"', "expand all",
                 'folder-report layout:summary output-to:"%3"'],
         expect=0, evidence="probes/u5i summary layout",
         known_difference="folder text layouts are not byte-compatible: the "
                          "renderer states so in its own output, and M3's "
                          "acceptance used layout:xml only. The case is kept so "
                          "the gap stays measured, not hidden."),
    dict(name="folder-side-by-side-expand-all", kind="folder",
         fixture="folder-mixed",
         script=['load "%1" "%2"', "expand all",
                 'folder-report layout:side-by-side output-to:"%3"'],
         expect=0, evidence="probes/u5i side-by-side layout",
         known_difference="same as folder-summary-expand-all"),

    # ---- the expand shapes that change <size> -------------------------
    dict(name="folder-no-expand", kind="folder", fixture="folder-mixed",
         script=['load "%1" "%2"',
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5g s1 / u5d no-expand: <size/> self-closing"),
    dict(name="folder-expand-one-subfolder", kind="folder", fixture="folder-mixed",
         script=['load "%1" "%2"', 'expand "sub"',
                 'folder-report layout:xml output-to:"%3"'],
         expect=0,
         evidence="probes/u5g s3 / u5d expand-sub: partially expanded stays <size/>"),
    dict(name="folder-expand-nested-fully", kind="folder", fixture="folder-nested",
         script=['load "%1" "%2"', 'expand "A\\B"',
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5g s4: expanding A\\B fully expands A"),
    dict(name="folder-expand-accumulates", kind="folder", fixture="folder-nested",
         script=['load "%1" "%2"', 'expand "A"', 'expand "A\\B"',
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5g s5: repeated expand commands accumulate"),

    # ---- filter -------------------------------------------------------
    dict(name="folder-filter-include", kind="folder", fixture="folder-exts",
         script=['filter "*.txt"', 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5c filter-include-txt, u5d filter-upper-txt"),
    dict(name="folder-filter-exclude", kind="folder", fixture="folder-exts",
         script=['filter "-*.txt"', 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5c filter-exclude-txt"),
    dict(name="folder-filter-folder-mask", kind="folder", fixture="folder-exts",
         script=['filter "sub\\\\"', 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5d filter-folder-only"),
    dict(name="folder-filter-match-nothing", kind="folder", fixture="folder-exts",
         script=['filter "*.nomatch"', 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0,
         evidence="probes/u5c filter-match-nothing: folder rows stay, files go"),
    dict(name="folder-filter-after-load", kind="folder", fixture="folder-exts",
         script=['load "%1" "%2"', "expand all", 'filter "*.txt"',
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5d settings-after-load"),
    dict(name="folder-filter-and-iu", kind="folder", fixture="folder-exts",
         script=['filter "*.txt"',
                 "criteria rules-based ignore-unimportant",
                 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0,
         evidence="probes/u5i xml-filter-and-iu: <ignoreunimportant/> before <filters>"),

    # ---- criteria -----------------------------------------------------
    dict(name="folder-criteria-crc", kind="folder", fixture="folder-crc",
         script=["criteria CRC", 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u4c/u5e: criteria CRC sees equal-size changes"),
    dict(name="folder-criteria-timestamp-tolerance", kind="folder",
         fixture="folder-tolerance",
         script=["criteria timestamp:2sec", 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5e crit-tol-sec"),
    dict(name="folder-criteria-after-load", kind="folder", fixture="folder-crc",
         script=['load "%1" "%2"', "expand all", "criteria CRC",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5e crit-after-load (takes effect after load)"),
    dict(name="folder-criteria-between-reports", kind="folder",
         fixture="folder-crc", second_report=True,
         script=['load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3.first"',
                 "criteria CRC",
                 'folder-report layout:xml output-to:"%3.second"'],
         expect=0,
         evidence="probes/u5e crit-after-report: the first report keeps the "
                  "default criteria (measured: first=same, second=diff)"),

    # ---- load <default> and the shell report shapes -------------------
    dict(name="folder-load-default", kind="folder", fixture="folder-mixed",
         script=["load <default>", 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5g s10: 155-byte empty shell, exit 0"),
    dict(name="text-shell-no-load", kind="text", fixture="text-differ",
         script=['text-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5f no-load-xml: 122-byte shell, exit 0"),

    # ---- option / log are accepted and change nothing ------------------
    dict(name="folder-option-accepted", kind="folder", fixture="folder-mixed",
         script=["option stop-on-error", "option confirm:yes-to-all",
                 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=0, evidence="probes/u5e option-stop-on-error / option-confirm-yes"),

    # ---- error paths: one case per measured code ----------------------
    dict(name="err-unknown-command", kind="text", fixture="text-differ",
         script=["frobnicate all"],
         expect=106, report=False, evidence="probes/u5 unknown-command"),
    dict(name="err-missing-report-arg", kind="text", fixture="text-differ",
         script=["text-report layout:xml"],
         expect=106, report=False, evidence="probes/u5 missing-required-arg"),
    dict(name="err-bad-layout-value", kind="text", fixture="text-differ",
         script=['text-report layout:not-a-layout output-to:"%3" "%1" "%2"'],
         expect=106, report=False, evidence="probes/u5 bad-option-value"),
    dict(name="err-criteria-bogus", kind="folder", fixture="folder-mixed",
         script=["criteria bogus-token", 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=106, report=False, evidence="probes/u5c criteria-bogus"),
    dict(name="err-option-bogus", kind="folder", fixture="folder-mixed",
         script=["option frobnicate", 'load "%1" "%2"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=106, report=False, evidence="probes/u5e option-bogus"),
    dict(name="err-expand-missing-path", kind="folder", fixture="folder-mixed",
         script=['load "%1" "%2"', 'expand "nope"',
                 'folder-report layout:xml output-to:"%3"'],
         expect=106, report=False, evidence="probes/u5e expand-missing"),
    dict(name="err-unclosed-quote", kind="text", fixture="text-differ",
         script=['text-report layout:xml output-to:"%3 "%1" "%2"'],
         expect=107, report=False, evidence="probes/u5 unclosed-quote"),
    dict(name="err-load-missing-folder", kind="folder", fixture="folder-mixed",
         script=['load "%1.does-not-exist" "%2.does-not-exist"', "expand all",
                 'folder-report layout:xml output-to:"%3"'],
         expect=107, report=False, evidence="probes/u5 load-missing-folder"),
    dict(name="err-text-report-missing-files", kind="text", fixture="text-differ",
         script=['text-report layout:xml output-to:"%3" "%1.nope" "%2.nope"'],
         expect=107, report=False, evidence="probes/u5 text-report-missing-files"),

    # ---- undecodable input: the `<errorN>` contract --------------------
    # The side number is DATA: `error1` is the left file, `error2` the right,
    # and a report with both carries both in that order (u7).  The first
    # implementation wrote `error1` twice, because only the left case had ever
    # been observed; these cases are what stops that regressing.
    dict(name="enc-left-invalid", kind="text", fixture="enc-left-invalid",
         script=['text-report layout:xml output-to:"%3" "%1" "%2"'],
         expect=0, evidence="probes/u7 left-invalid; golden enc-latin1"),
    dict(name="enc-right-invalid", kind="text", fixture="enc-right-invalid",
         script=['text-report layout:xml output-to:"%3" "%1" "%2"'],
         expect=0, evidence="probes/u7 right-invalid (<error2>)"),
    dict(name="enc-both-invalid", kind="text", fixture="enc-both-invalid",
         script=['text-report layout:xml output-to:"%3" "%1" "%2"'],
         expect=0, evidence="probes/u7 both-invalid (<error1> then <error2>)"),
    dict(name="enc-second-line", kind="text", fixture="enc-second-line",
         script=['text-report layout:xml output-to:"%3" "%1" "%2"'],
         expect=0, evidence="probes/u7 second-line (the line number is DATA)"),
]

#: `/qc` cases: the bare command line, exit code only.  ``kind`` is the /qc type
#: (None = rules-based).
QC_CASES: list[dict] = [
    dict(name="qc-rules-identical", kind=None, fixture="qc-identical", expect=1,
         evidence="probes/u5b qc-rules-identical"),
    dict(name="qc-rules-crlf-only", kind=None, fixture="qc-crlf", expect=2,
         evidence="probes/u5b qc-rules-crlf-only"),
    dict(name="qc-rules-ws-only", kind=None, fixture="qc-ws", expect=12,
         evidence="probes/u5b qc-rules-ws-only"),
    dict(name="qc-rules-case-only", kind=None, fixture="qc-case", expect=12,
         evidence="probes/u5b qc-rules-case-only"),
    dict(name="qc-rules-indent-only", kind=None, fixture="qc-indent", expect=13,
         evidence="probes/u5k indent-only-py MEASURED 13, not 12: a Python "
                  "leading-indent element is IMPORTANT (u1/07-m2-importance), "
                  "so the pair is 'rules-based differences'. The first draft of "
                  "this corpus guessed 12 from the 'whitespace is unimportant' "
                  "generalisation; the gate caught it and the probe is the "
                  "authority."),
    dict(name="qc-rules-trailing-ws", kind=None, fixture="qc-trailing-ws",
         expect=12, evidence="probes/u5k trailing-ws-py"),
    dict(name="qc-rules-comment-only", kind=None, fixture="qc-comment",
         expect=13, evidence="probes/u5b qc-rules-comment-only"),
    dict(name="qc-rules-content", kind=None, fixture="qc-content", expect=13,
         evidence="probes/u5b qc-rules-diff"),
    dict(name="qc-crc-identical", kind="crc", fixture="qc-identical", expect=1,
         evidence="probes/u5b qc-crc-same"),
    dict(name="qc-crc-content", kind="crc", fixture="qc-content", expect=11,
         evidence="probes/u5b qc-crc-diff"),
    dict(name="qc-crc-ws-only", kind="crc", fixture="qc-ws", expect=11,
         evidence="probes/u5b qc-crc-ws-only (crc does not fold unimportant)"),
    dict(name="qc-size-equal-bytes-differ", kind="size",
         fixture="qc-equal-size", expect=11,
         evidence="probes/u5k eq-size-diff-bytes"),
    dict(name="qc-binary-identical", kind="binary", fixture="qc-identical",
         expect=1, evidence="probes/u5b qc-binary-same"),
    dict(name="qc-binary-content", kind="binary", fixture="qc-content",
         expect=11, evidence="probes/u5b qc-binary-diff"),
    dict(name="qc-missing-files", kind=None, fixture="qc-missing", expect=100,
         evidence="probes/u5b qc-rules-missing"),
]


# ==========================================================================
# Fixtures
# ==========================================================================
# Each entry maps a relative path to its bytes; directories come from the path
# shape.  The paths are spelled out literally on purpose: an earlier version
# used a `__` to `/` shortcut, which silently turned `a__txt` into a DIRECTORY
# `a` holding a file `txt`, so every "text" case correctly failed to load and
# the corpus tested nothing.  (The gate caught it: both engines returned 107.)
#
# Everything is written with a pinned mtime, so the report's `<modified>` column
# is reproducible rather than a function of when the fixture was created.

FIXTURES: dict[str, tuple[dict[str, bytes], dict[str, bytes]]] = {
    "text-differ": (
        {"a.txt": b"alpha\nbeta\n"},
        {"a.txt": b"alpha\nGAMMA\n"},
    ),
    "py-differ": (
        {"m.py": b"def f():\n    return 1\n"},
        {"m.py": b"def f():\n        return 2\n"},
    ),
    "c-differ": (
        {"m.c": b"int main() {\n  int a;\n  return 0;\n}\n"},
        {"m.c": b"int main() {\n   int a;\n  return 0;\n}\n"},
    ),
    "folder-mixed": (
        {"same.txt": b"same\n", "leftonly.txt": b"L\n",
         "sub/inner.txt": b"inner\n"},
        {"same.txt": b"same\n", "rightonly.txt": b"R\n",
         "sub/inner.txt": b"INNER\n"},
    ),
    "folder-nested": (
        {"A/B/f.txt": b"fffff\n", "A/g.txt": b"ggg\n", "h.txt": b"hhhh\n",
         "C/i.txt": b"ii\n"},
        {"A/B/f.txt": b"fffff\n", "A/g.txt": b"ggg\n", "h.txt": b"hhhh\n",
         "C/i.txt": b"ii\n"},
    ),
    "folder-exts": (
        {"a.txt": b"alpha\n", "b.log": b"log line\n", "c.TXT": b"upper\n",
         "d1.bin": b"x\n", "sub/e.txt": b"e\n", "other/g.log": b"g\n"},
        {"a.txt": b"ALPHA\n", "b.log": b"log line\n", "c.TXT": b"upper\n",
         "d1.bin": b"x\n", "sub/e.txt": b"E\n", "other/g.log": b"g\n"},
    ),
    "folder-crc": (
        {"samesize.bin": b"AAAABBBB"},
        {"samesize.bin": b"CCCCDDDD"},
    ),
    "folder-tolerance": (
        {"within.txt": b"same\n", "beyond.txt": b"same\n"},
        {"within.txt": b"same\n", "beyond.txt": b"same\n"},
    ),
    # ---- /qc file pairs -------------------------------------------------
    "qc-identical": ({"f.txt": b"alpha\nbeta\n"}, {"f.txt": b"alpha\nbeta\n"}),
    "qc-crlf": ({"f.txt": b"alpha\nbeta\n"}, {"f.txt": b"alpha\r\nbeta\r\n"}),
    "qc-ws": ({"f.txt": b"alpha beta\n"}, {"f.txt": b"alpha   beta\n"}),
    "qc-case": ({"f.txt": b"Alpha\n"}, {"f.txt": b"alpha\n"}),
    "qc-indent": ({"f.py": b"def f():\n    return 1\n"},
                  {"f.py": b"def f():\n        return 1\n"}),
    "qc-trailing-ws": ({"f.py": b"x = 1   \n"}, {"f.py": b"x = 1\n"}),
    "qc-comment": ({"f.txt": b"int x; // one\n"},
                   {"f.txt": b"int x; // two\n"}),
    "qc-content": ({"f.txt": b"alpha\nbeta\n"}, {"f.txt": b"alpha\nGAMMA\n"}),
    "qc-equal-size": ({"f.bin": b"AAAABBBB"}, {"f.bin": b"CCCCDDDD"}),
    "qc-missing": ({}, {}),  # no files: the paths below do not exist
    # ---- undecodable input ------------------------------------------------
    # `\xe9` is a lone Latin-1 e-acute, invalid in UTF-8; `\xc3\xa9` is its
    # correct UTF-8 spelling.  Both files are valid on the side that decodes.
    "enc-left-invalid": ({"a.txt": b"caf\xe9\n"}, {"a.txt": b"caf\xc3\xa9\n"}),
    "enc-right-invalid": ({"a.txt": b"caf\xc3\xa9\n"}, {"a.txt": b"caf\xe9\n"}),
    "enc-both-invalid": ({"a.txt": b"caf\xe9\n"}, {"a.txt": b"caf\xe8\n"}),
    "enc-second-line": ({"a.txt": b"ok\naf\xe9\n"}, {"a.txt": b"ok\naf\xc3\xa9\n"}),
}

#: The two files a /qc case compares.  `qc-missing` is special: it points at
#: paths that were never created, which is what code 100 means.
QC_FILES = {
    "qc-missing": ("does-not-exist-L.bin", "does-not-exist-R.bin"),
}


# ==========================================================================
# Running
# ==========================================================================

def write_tree(root: pathlib.Path, files: dict[str, bytes]) -> None:
    for rel, blob in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
    # Pin every mtime, deepest first, so the report's <modified> column is
    # reproducible rather than a function of when the fixture was created.
    for p in sorted(root.rglob("*"), key=lambda q: -len(q.parts)):
        os.utime(p, (FIXED_MTIME, FIXED_MTIME))


def build_fixture(run_dir: pathlib.Path, name: str) -> tuple[pathlib.Path,
                                                           pathlib.Path]:
    left_files, right_files = FIXTURES[name]
    L = run_dir / "fixtures" / name / "L"
    R = run_dir / "fixtures" / name / "R"
    if not L.exists():
        write_tree(L, left_files)
    if not R.exists():
        write_tree(R, right_files)
    # `folder-tolerance` exists to exercise `criteria timestamp:2sec`, so its
    # two files need a controlled timestamp relationship: one inside the
    # tolerance, one outside it.  The pinned mtime alone would make every row
    # `same`, which would test nothing.
    if name == "folder-tolerance":
        os.utime(L / "within.txt", (FIXED_MTIME, FIXED_MTIME))
        os.utime(R / "within.txt", (FIXED_MTIME + 1, FIXED_MTIME + 1))
        os.utime(L / "beyond.txt", (FIXED_MTIME, FIXED_MTIME))
        os.utime(R / "beyond.txt", (FIXED_MTIME + 5, FIXED_MTIME + 5))
    return L, R


@dataclass
class CaseResult:
    name: str
    kind: str
    oracle_exit: int
    product_exit: int
    expected: int
    verdict: str
    detail: str = ""
    artifacts: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Pass and known-difference both count as "not a regression".

        ``known_difference`` is a recorded, evidenced gap — the same treatment
        `04-milestones.md` §5 prescribes ("记录为已知差异... 不隐藏").  It is not a
        pass, so it is reported separately and never folded into the pass count.
        """
        return self.verdict in ("pass", "known_difference")


def run_product_script(script: pathlib.Path, args: list[str]) -> tuple[int, str]:
    cmd = [str(PRODUCT), "/silent", f"@{script}", *args]
    proc = subprocess.run(cmd, capture_output=True, timeout=300,
                          cwd=str(script.parent))
    return proc.returncode, proc.stderr.decode("utf-8", errors="replace")


def run_product_qc(kind: str | None, left: pathlib.Path,
                   right: pathlib.Path) -> int:
    flag = f"/qc={kind}" if kind else "/qc"
    proc = subprocess.run([str(PRODUCT), flag, str(left), str(right)],
                          capture_output=True, timeout=300)
    return proc.returncode


def run_oracle_qc(kind: str | None, left: pathlib.Path,
                  right: pathlib.Path) -> int:
    """The /qc lane: the bare command line, still inside the job object.

    ``harness.oracle.run`` is fixed to the ``@script`` recipe, so this builds the
    argv directly while reusing its containment: in-place ``cwd``, CREATE_SUSPENDED
    then resume only after the job assignment, and a whole-tree kill on timeout.
    """
    args = [f"/qc={kind}" if kind else "/qc", str(left), str(right)]
    cmd = [str(ORACLE), "/silent", *args]
    with orc.ProcessTree() as tree:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(ORACLE.parent),
            creationflags=orc._CREATE_SUSPENDED if tree.enabled else 0,
        )
        tree.assign(proc)
        if tree.enabled:
            orc._resume(proc)
        try:
            proc.communicate(timeout=180)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            tree.kill_tree()
            proc.kill()
            proc.communicate(timeout=10)
            code = -1
    return code


def compare_reports(oracle_path: pathlib.Path, product_path: pathlib.Path,
                    expect_report: bool) -> tuple[bool, str]:
    """Compare two report files after normalisation.

    The comparison is the milestone's actual acceptance: same layout, same
    content.  A missing report on both sides is agreement only when the case
    declares no report (an error path).
    """
    o_exists = oracle_path.exists() and oracle_path.stat().st_size > 0
    p_exists = product_path.exists() and product_path.stat().st_size > 0
    if not expect_report:
        if o_exists or p_exists:
            return False, (f"expected no report, got oracle={o_exists} "
                           f"product={p_exists}")
        return True, "both wrote no report"
    if not o_exists:
        return False, "the Oracle wrote no report"
    if not p_exists:
        return False, "the product wrote no report"
    o_text = norm_mod.read_report(oracle_path)
    p_text = norm_mod.read_report(product_path)
    try:
        o_norm = norm_mod.normalize(o_text, path=str(oracle_path))
        p_norm = norm_mod.normalize(p_text, path=str(product_path))
    except norm_mod.NormalizerRefusal as exc:
        return False, f"normalizer refused ({exc.reason}): {exc.detail}"
    if o_norm.text == p_norm.text:
        return True, "normalized reports identical"
    diff = _first_diff(o_norm.text, p_norm.text)
    return False, f"normalized reports differ: {diff}"


def _first_diff(a: str, b: str) -> str:
    al, bl = a.splitlines(), b.splitlines()
    for i in range(max(len(al), len(bl))):
        x = al[i] if i < len(al) else "<missing>"
        y = bl[i] if i < len(bl) else "<missing>"
        if x != y:
            return f"line {i + 1}: oracle={x.strip()[:90]!r} product={y.strip()[:90]!r}"
    return "(no differing line found)"


def main() -> int:
    ap = argparse.ArgumentParser(description="M4 script-level Oracle gate")
    ap.add_argument("--run", default=None, help="run directory name")
    ap.add_argument("--filter", default=None,
                    help="only run cases whose name contains this")
    ap.add_argument("--list", action="store_true", help="list the corpus and exit")
    ap.add_argument("--qc-only", action="store_true")
    ap.add_argument("--script-only", action="store_true")
    args = ap.parse_args()

    if args.list:
        print(f"script cases ({len(SCRIPT_CASES)}):")
        for c in SCRIPT_CASES:
            print(f"  {c['name']:<38} expect={c['expect']}")
        print(f"\n/qc cases ({len(QC_CASES)}):")
        for c in QC_CASES:
            print(f"  {c['name']:<38} kind={c['kind'] or 'rules':<7} "
                  f"expect={c['expect']}")
        return 0

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        print(f"the Oracle is unavailable: {inst.disabled_reason}")
        return 2
    global ORACLE
    ORACLE = pathlib.Path(inst.oracle_path)

    if not PRODUCT.exists():
        print(f"the product binary is missing: {PRODUCT}\n"
              f"build it with: cd {PRODUCT.parent.parent.parent} && "
              f"cargo build --release")
        return 2

    run_name = args.run or ("M4-gate-serial-01" if not args.filter
                            else f"M4-gate-{args.filter}")
    run_dir = VERIFY / "runs" / run_name
    (run_dir / "oracle").mkdir(parents=True, exist_ok=True)
    (run_dir / "product").mkdir(parents=True, exist_ok=True)
    (run_dir / "scripts").mkdir(parents=True, exist_ok=True)

    print(f"oracle  : {ORACLE} ({inst.oracle_version})")
    print(f"product : {PRODUCT}")
    print(f"run     : {run_dir}\n")

    results: list[CaseResult] = []
    started = time.perf_counter()

    # ---- script cases ---------------------------------------------------
    if not args.qc_only:
        for case in SCRIPT_CASES:
            if args.filter and args.filter not in case["name"]:
                continue
            L, R = build_fixture(run_dir, case["fixture"])
            left = (L / "a.txt") if case["kind"] == "text" else L
            right = (R / "a.txt") if case["kind"] == "text" else R
            if case["fixture"] == "py-differ":
                left, right = L / "m.py", R / "m.py"
            elif case["fixture"] == "c-differ":
                left, right = L / "m.c", R / "m.c"

            o_out = run_dir / "oracle" / f"{case['name']}.out"
            p_out = run_dir / "product" / f"{case['name']}.out"
            script = orc.write_script(run_dir / "scripts" / f"{case['name']}.bcs",
                                      case["script"])

            # The Oracle first, alone: one call at a time, always.
            run = orc.run(ORACLE, script, str(left), str(right), str(o_out),
                          timeout=180.0, script_text="\n".join(case["script"]))
            o_exit = run.exit_code

            p_exit, p_err = run_product_script(
                script, [str(left), str(right), str(p_out)])

            # Compare the reports this case actually writes.  A case may write
            # more than one: `folder-criteria-between-reports` uses `%3.first`
            # and `%3.second`, so there is no plain `%3` file to compare, and
            # looking for one would report "the Oracle wrote no report" for a
            # case that wrote two.
            expect_report = case.get("report", True)
            if case.get("second_report"):
                checks = [
                    (pathlib.Path(str(o_out) + ".first"),
                     pathlib.Path(str(p_out) + ".first")),
                    (pathlib.Path(str(o_out) + ".second"),
                     pathlib.Path(str(p_out) + ".second")),
                ]
            else:
                checks = [(o_out, p_out)]
            details: list[str] = []
            ok = True
            for o_path, p_path in checks:
                this_ok, this_detail = compare_reports(o_path, p_path,
                                                       expect_report)
                ok = ok and this_ok
                if not this_ok:
                    details.append(f"{o_path.name}: {this_detail}")
            detail = "; ".join(details) if details else "normalized reports identical"

            verdict = "pass"
            if o_exit != case["expect"] or p_exit != case["expect"]:
                # An exit-code disagreement is never a known difference: the
                # codes are the part of M4 that was measured exhaustively.
                verdict = "fail"
                detail = (f"exit: oracle={o_exit} product={p_exit} "
                          f"expected={case['expect']}; {detail}")
            elif not ok and case.get("known_difference"):
                verdict = "known_difference"
            elif not ok:
                verdict = "fail"

            res = CaseResult(case["name"], "script", o_exit, p_exit,
                             case["expect"], verdict, detail,
                             {"evidence": case["evidence"],
                              "script": case["script"],
                              "oracle_stderr": run.stderr.strip()[:200],
                              "product_stderr": p_err.strip()[:200]})
            results.append(res)
            mark = "ok  " if res.ok else "FAIL"
            print(f"  {mark} {case['name']:<38} oracle={o_exit:<4} "
                  f"product={p_exit:<4} {detail[:60]}")

    # ---- /qc cases ------------------------------------------------------
    if not args.script_only:
        for case in QC_CASES:
            if args.filter and args.filter not in case["name"]:
                continue
            if case["fixture"] in QC_FILES:
                left, right = (run_dir / "fixtures" / QC_FILES[case["fixture"]][0],
                               run_dir / "fixtures" / QC_FILES[case["fixture"]][1])
            else:
                L, R = build_fixture(run_dir, case["fixture"])
                left = L / next(iter(FIXTURES[case["fixture"]][0]))
                right = R / next(iter(FIXTURES[case["fixture"]][1]))

            o_exit = run_oracle_qc(case["kind"], left, right)
            p_exit = run_product_qc(case["kind"], left, right)
            verdict = "pass" if o_exit == p_exit == case["expect"] else "fail"
            detail = ("" if verdict == "pass" else
                      f"oracle={o_exit} product={p_exit} "
                      f"expected={case['expect']}")
            res = CaseResult(case["name"], "qc", o_exit, p_exit, case["expect"],
                             verdict, detail, {"evidence": case["evidence"]})
            results.append(res)
            mark = "ok  " if res.ok else "FAIL"
            print(f"  {mark} {case['name']:<38} oracle={o_exit:<4} "
                  f"product={p_exit:<4} {detail[:50]}")

    elapsed = time.perf_counter() - started

    # ---- summary --------------------------------------------------------
    passed = sum(1 for r in results if r.verdict == "pass")
    known = [r for r in results if r.verdict == "known_difference"]
    failures = [r for r in results if r.verdict == "fail"]
    print(f"\n{passed}/{len(results)} passed in {elapsed:.1f}s"
          + (f" ({len(known)} known difference(s))" if known else ""))
    by_verdict: dict[str, int] = {}
    for r in results:
        by_verdict[r.verdict] = by_verdict.get(r.verdict, 0) + 1
    for v in sorted(by_verdict):
        print(f"  {v}: {by_verdict[v]}")

    if known:
        print("\nknown differences (recorded, not hidden):")
        for r in known:
            print(f"  {r.name}: {r.detail[:110]}")

    if failures:
        print("\nfailures:")
        for r in failures:
            print(f"  {r.name}: {r.detail}")

    payload = {
        "run": run_name,
        "started": datetime.now(timezone.utc).isoformat(),
        "oracle": {"path": str(ORACLE), "version": inst.oracle_version,
                   "engine_sha256": inst.app_sha256,
                   "oracle_sha256": inst.oracle_sha256},
        "product": str(PRODUCT),
        "elapsed_s": round(elapsed, 1),
        "counts": {"total": len(results), "pass": passed,
                   "fail": len(failures), **{f"verdict_{k}": v
                                             for k, v in by_verdict.items()}},
        "results": [vars(r) for r in results],
    }
    (run_dir / "m4-gate.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'm4-gate.json'}")
    return 0 if not failures else 1


ORACLE: pathlib.Path = pathlib.Path()

if __name__ == "__main__":
    raise SystemExit(main())
