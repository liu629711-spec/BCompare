"""Run orchestration and aggregation.

The runner executes eight suites:

* ``anchor`` -- the text anchors, ``text-report layout:xml`` per anchor
  with the anchor's own ``options:`` recovered from the golden manifest.
* ``layout`` -- the text-layout reports, ``text-report layout:<layout>``.
* ``table`` -- the CSV goldens under ``verify/table``, ``data-report``
  script-vs-script (M6.4; the product is invoked with the identical line).
* ``hex`` -- the binary goldens under ``verify/hex``, ``hex-report``
  script-vs-script (M7; the product is invoked with the identical line).
* ``pic`` -- the image goldens under ``verify/pic``, ``picture-report``
  script-vs-script (M9; the product is invoked with the identical line).
* ``reg`` -- the .reg goldens under ``verify/reg``, ``registry-report``
  script-vs-script (M11; the product is invoked with the identical line,
  and the Chinese install's re-run corroborates the norm-5 label folds).
* ``folder`` -- the folder fixtures through the documented
  ``load`` -> ``expand all`` -> ``folder-report`` recipe.

Two *subjects* can be exercised:

* ``oracle``    -- a real Beyond Compare install (the authority).
* ``candidate`` -- a CLI via :mod:`harness.candidate` (the product seam; today
  only the old prototype is wired).

Each subject is run and reported **separately**.  Results from different
versions are never merged into a single number: every result carries
``oracle_version`` and the report groups by it.

Failure taxonomy is strict: an error, a missing output, a timeout, an
unparseable report and a skipped test are all distinct verdicts and are never
counted as passes.
"""

from __future__ import annotations

import fnmatch
import pathlib
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable

from . import candidate as cand_mod
from . import installs as installs_mod
from . import manifests as man_mod
from . import normalize as norm_mod
from . import oracle as oracle_mod
from .taxonomy import (
    TestResult, Verdict, OracleError, NormalizerRefusal, summarize,
)

#: The one tree the harness is allowed to write to by default.
#: The guard is an **allow-list**: a target must live under a writable root,
#: and it is refused if it falls in any protected tree below. Reversing the
#: default (permit-unless-listed) is what makes a newly created directory under
#: the workspace safe by construction rather than safe-by-remembering.
DEFAULT_WRITABLE_ROOT = pathlib.Path(r"D:\Rea\product\verify\runs")

#: Trees the harness must never write to.  Defence in depth behind the
#: allow-list: even a mis-configured results root cannot reach them.
#: Covers every asset the A-1 task statement protects.
READ_ONLY_ROOTS = (
    pathlib.Path(r"D:\Rea\verify"),          # golden data + fixtures
    pathlib.Path(r"D:\Rea\clone"),           # old Rust prototype
    pathlib.Path(r"D:\Rea\extracted"),       # reverse-engineering evidence
    pathlib.Path(r"D:\Rea\specs"),           # unit specs
    pathlib.Path(r"D:\Rea\tools"),           # includes tools\_audit\ and tools\bc-*.py
    pathlib.Path(r"D:\Rea\ghidra-project"),  # persistent analysis DB
    pathlib.Path(r"D:\Rea\help"),            # official documentation
    pathlib.Path(r"D:\Rea\rea-snapshot"),    # workspace snapshot
    pathlib.Path(r"D:\Rea\product\docs"),    # audit documents
    pathlib.Path(r"D:\BCompare"),            # Oracle install -- must run in place
    pathlib.Path(r"D:\bc-official"),         # reference install
)

#: Individual protected files, as glob patterns matched against the resolved
#: path.  A pattern (not just the 6 known names) so a newly written
#: ``report-*.md`` is protected without anyone remembering to update a list.
READ_ONLY_FILE_PATTERNS = (
    r"D:\Rea\report-*.md",
)

#: ``product\verify`` is the harness's own source tree; only its ``runs``
#: subdirectory may be written.  This stops a mis-set results root from
#: overwriting harness code or tests.
HARNESS_SOURCE_ROOT = pathlib.Path(r"D:\Rea\product\verify")


def _is_under(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def assert_writable(target: pathlib.Path,
                    *, allowed_roots: tuple[pathlib.Path, ...] = ()) -> None:
    """Refuse to write anywhere except a permitted results tree.

    Enforced as an **allow-list inversion**, in this order:

    1. the target must resolve under a writable root -- either one of
       ``allowed_roots`` when the caller supplies them, or
       :data:`DEFAULT_WRITABLE_ROOT` otherwise;
    2. it must not fall inside any :data:`READ_ONLY_ROOTS` tree;
    3. it must not match :data:`READ_ONLY_FILE_PATTERNS`;
    4. inside ``product\\verify`` only ``runs\\`` may be written, so the harness
       cannot overwrite its own source.

    Rule 1 is what makes this an allow-list: anything outside the results tree
    is refused, including directories that do not exist yet and therefore could
    not have been enumerated in a deny-list. Rules 2-4 are extra protection in
    case the configured results root is itself somewhere it should not be.

    Raises:
        RuntimeError: with a message naming which rule refused the target.
    """
    t = pathlib.Path(target).resolve()

    roots = tuple(allowed_roots) if allowed_roots else (DEFAULT_WRITABLE_ROOT,)

    # Rule 1 -- allow-list. Checked first so an unknown/new directory outside
    # the results tree is refused even though no deny-list mentions it.
    if not any(_is_under(t, pathlib.Path(r).resolve()) for r in roots):
        allowed = ", ".join(str(pathlib.Path(r).resolve()) for r in roots)
        raise RuntimeError(
            f"refusing to write outside the writable results tree: {t} "
            f"(allowed roots: {allowed})")

    # Rule 2 -- protected trees (also catches a results root set to one).
    for ro in READ_ONLY_ROOTS:
        if _is_under(t, ro.resolve()):
            raise RuntimeError(
                f"refusing to write inside read-only asset tree: {t} "
                f"(protected: {ro})")

    # Rule 3 -- protected individual files.
    t_str = str(t)
    for pattern in READ_ONLY_FILE_PATTERNS:
        if fnmatch.fnmatch(t_str, pattern):
            raise RuntimeError(f"refusing to write read-only file: {t}")

    # Rule 4 -- the harness's own source tree.
    src = HARNESS_SOURCE_ROOT.resolve()
    if _is_under(t, src) and not _is_under(t, DEFAULT_WRITABLE_ROOT.resolve()):
        raise RuntimeError(
            f"refusing to write inside the harness source tree: {t} "
            f"(only {DEFAULT_WRITABLE_ROOT} is writable)")


@dataclass
class RunConfig:
    results_dir: pathlib.Path
    installs: dict[str, installs_mod.InstallIdentity]
    candidates: dict[str, cand_mod.CandidateAdapter]
    timeout: float = 180.0
    suites: tuple[str, ...] = ("anchor", "layout", "table", "hex", "pic", "reg", "ver", "folder")
    oracle_keys: tuple[str, ...] = ("current",)
    candidate_keys: tuple[str, ...] = ()
    include_reference_labels: bool = True
    keep_scripts: bool = True

    def out(self, *parts: str) -> pathlib.Path:
        """Resolve a path under this run's results directory, guarded.

        The configured ``results_dir`` is passed as the allowed root, so the
        guard enforces "writes stay inside *this run's* directory" -- a tighter
        statement than the module default.  Rules 2-4 still apply, so a
        ``results_dir`` deliberately pointed at, say, ``verify\\golden`` is
        refused rather than honoured.
        """
        p = self.results_dir.joinpath(*parts)
        assert_writable(p, allowed_roots=(self.results_dir,))
        return p


class Runner:
    def __init__(self, cfg: RunConfig, log: Callable[[str], None] = print):
        self.cfg = cfg
        self.log = log
        self.results: list[TestResult] = []
        self.notes: list[str] = []
        self.scripts_dir = cfg.out("scripts")
        self.raw_dir = cfg.out("raw")
        self.norm_dir = cfg.out("normalized")
        for d in (self.scripts_dir, self.raw_dir, self.norm_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _record(self, r: TestResult) -> TestResult:
        self.results.append(r)
        return r

    def _save_normalized(self, name: str, text: str) -> str:
        p = self.norm_dir / f"{name}.txt"
        p.write_text(text, encoding="utf-8")
        return str(p)

    # ------------------------------------------------------------------
    # Oracle suites
    # ------------------------------------------------------------------
    def run_anchors(self, install_key: str) -> list[TestResult]:
        inst = self.cfg.installs[install_key]
        anchors = man_mod.load_anchors()
        out: list[TestResult] = []
        self.log(f"--- anchors [{install_key}] {inst.app_version or '?'} "
                 f"({len(anchors)} cases)")

        for a in anchors:
            base = TestResult(
                test_id=a.name,
                suite="anchor",
                verdict=Verdict.NOT_RUN,
                subject="oracle",
                oracle_version=inst.app_version,
                oracle_path=inst.oracle_path,
                left=str(a.left),
                right=str(a.right),
                golden_report=str(a.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"unit": a.unit, "note": a.note,
                           "options": a.options or "",
                           "golden_statuses": a.statuses,
                           "golden_exit_code": a.golden_exit_code,
                           "install_key": install_key,
                           "locale": inst.locale},
            )

            missing = a.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {a.name:<26} {base.detail}")
                continue

            script_text = oracle_mod.text_script("xml", a.options)
            sp = oracle_mod.write_script(self.scripts_dir / f"anchor-{install_key}-{a.name}.txt",
                                         [script_text])
            outp = self.raw_dir / f"anchor-{install_key}-{a.name}.xml"
            base.command = [str(inst.oracle_path), "/silent", f"@{sp}",
                            str(a.left), str(a.right), str(outp)]
            base.script_text = script_text
            base.raw_report = str(outp)

            try:
                run = oracle_mod.run(inst.oracle_path, sp, str(a.left), str(a.right),
                                     outp, timeout=self.cfg.timeout, script_text=script_text)
            except OracleError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"oracle failed to run: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {a.name:<26} {exc}")
                continue

            base.exit_code = run.exit_code
            base.elapsed_s = run.elapsed_s
            base.artifacts["containment"] = run.containment
            base.artifacts["tree_killed"] = run.tree_killed

            verdict, detail, parsed = self._judge_xml(base, a, run)
            base.verdict = verdict
            base.detail = detail
            base.parsed = parsed
            out.append(self._record(base))
            self.log(f"  {verdict.value:<14} {a.name:<26} {detail}")
        return out

    def _judge_xml(self, base: TestResult, a: man_mod.AnchorCase,
                   run: oracle_mod.OracleRun):
        if run.timed_out:
            return Verdict.TIMEOUT, f"oracle exceeded {self.cfg.timeout}s", None
        if run.exit_code != 0:
            return (Verdict.ERROR,
                    f"exit {run.exit_code} ({oracle_mod.exit_meaning(run.exit_code)})",
                    None)
        if not run.report_exists or run.report_bytes == 0:
            return Verdict.MISSING_OUTPUT, "exit 0 but no report was written", None

        got_raw = norm_mod.read_report(run.report_path)
        want_raw = norm_mod.read_report(a.golden_report)

        try:
            got = norm_mod.normalize_xml(got_raw)
            want = norm_mod.normalize_xml(want_raw)
        except NormalizerRefusal as exc:
            return (Verdict.UNPARSEABLE,
                    f"normalizer refused ({exc.reason}): {exc.detail}", None)

        base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
        base.normalized_report = self._save_normalized(
            f"anchor-{base.artifacts['install_key']}-{a.name}", got.text)

        got_statuses = man_mod.statuses_from_xml(got_raw)
        status_match = got_statuses == a.statuses
        struct_match = got.structure == want.structure

        parsed = {
            "statuses": got_statuses,
            "status_sequence_matches_golden": status_match,
            "normalized_structure_matches_golden": struct_match,
        }
        base.expected = {"statuses": a.statuses}
        if struct_match:
            return Verdict.PASS, f"statuses ok ({len(got_statuses)}), normalized structure ok", parsed
        if status_match:
            return (Verdict.FAIL,
                    "status sequence matches golden but normalized structure differs "
                    "(label/normalizer gap -- see normalized report)", parsed)
        return (Verdict.FAIL,
                f"status sequence differs: got {got_statuses} want {a.statuses}", parsed)

    def run_layouts(self, install_key: str) -> list[TestResult]:
        inst = self.cfg.installs[install_key]
        cases = man_mod.load_layouts()
        out: list[TestResult] = []
        self.log(f"--- layouts [{install_key}] {inst.app_version or '?'} "
                 f"({len(cases)} cases)")

        for c in cases:
            base = TestResult(
                test_id=c.name,
                suite="layout",
                verdict=Verdict.NOT_RUN,
                subject="oracle",
                oracle_version=inst.app_version,
                oracle_path=inst.oracle_path,
                left=str(c.left),
                right=str(c.right),
                golden_report=str(c.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"layout": c.layout, "case": c.case,
                           "golden_bytes": c.golden_bytes,
                           "golden_exit_code": c.golden_exit_code,
                           "install_key": install_key, "locale": inst.locale},
            )
            missing = c.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {c.name:<28} {base.detail}")
                continue

            script_text = oracle_mod.text_script(c.layout)
            sp = oracle_mod.write_script(self.scripts_dir / f"layout-{install_key}-{c.name}.txt",
                                         [script_text])
            outp = self.raw_dir / f"layout-{install_key}-{c.name}.txt"
            base.command = [str(inst.oracle_path), "/silent", f"@{sp}",
                            str(c.left), str(c.right), str(outp)]
            base.script_text = script_text
            base.raw_report = str(outp)

            try:
                run = oracle_mod.run(inst.oracle_path, sp, str(c.left), str(c.right),
                                     outp, timeout=self.cfg.timeout, script_text=script_text)
            except OracleError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"oracle failed to run: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {c.name:<28} {exc}")
                continue

            base.exit_code = run.exit_code
            base.elapsed_s = run.elapsed_s
            base.artifacts["containment"] = run.containment
            base.artifacts["tree_killed"] = run.tree_killed

            if run.timed_out:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"oracle exceeded {self.cfg.timeout}s"
            elif run.exit_code != 0:
                base.verdict = Verdict.ERROR
                base.detail = f"exit {run.exit_code} ({oracle_mod.exit_meaning(run.exit_code)})"
            elif not run.report_exists or run.report_bytes == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "exit 0 but no report was written"
            else:
                got_raw = norm_mod.read_report(run.report_path)
                want_raw = norm_mod.read_report(c.golden_report)
                try:
                    got = norm_mod.normalize_text(got_raw)
                    want = norm_mod.normalize_text(want_raw)
                except NormalizerRefusal as exc:
                    base.verdict = Verdict.UNPARSEABLE
                    base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
                else:
                    base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                    base.normalized_report = self._save_normalized(
                        f"layout-{install_key}-{c.name}", got.text)
                    same = got.structure == want.structure
                    # Raw (pre-normalization) agreement is recorded separately
                    # so a report can show how much of a match comes from the
                    # comparison engine versus from the normalizer.
                    base.parsed = {
                        "line_count": len(got.structure or ()),
                        "normalized_matches_golden": same,
                        "raw_bytes_equal_golden": got_raw == want_raw,
                        "raw_equal_after_volatile_only":
                            _strip_volatile_only(got_raw) == _strip_volatile_only(want_raw),
                    }
                    base.expected = {"line_count": len(want.structure or ())}
                    if same:
                        base.verdict = Verdict.PASS
                        base.detail = f"{len(got.structure or ())} normalized lines match"
                    else:
                        base.verdict = Verdict.FAIL
                        base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {c.name:<28} {base.detail}")
        return out

    def run_tables(self, install_key: str) -> list[TestResult]:
        """M6.4 table suite: the CSV goldens under ``verify/table/``, run
        with the identical ``data-report`` script the product is invoked
        with, compared line-wise after label/time/path normalization
        (the layouts-suite mechanism; docs/13 §1 decision 1)."""
        inst = self.cfg.installs[install_key]
        cases = man_mod.load_table_cases()
        out: list[TestResult] = []
        self.log(f"--- tables [{install_key}] {inst.app_version or '?'} "
                 f"({len(cases)} cases)")

        for c in cases:
            base = TestResult(
                test_id=c.name,
                suite="table",
                verdict=Verdict.NOT_RUN,
                subject="oracle",
                oracle_version=inst.app_version,
                oracle_path=inst.oracle_path,
                left=str(c.left),
                right=str(c.right),
                golden_report=str(c.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"layout": c.layout, "ext": c.ext, "note": c.note,
                           "golden_bytes": c.golden_bytes,
                           "golden_exit_code": c.golden_exit_code,
                           "install_key": install_key, "locale": inst.locale},
            )
            missing = c.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {c.name:<30} {base.detail}")
                continue

            script_text = oracle_mod.table_script(c.layout, c.title)
            sp = oracle_mod.write_script(
                self.scripts_dir / f"table-{install_key}-{c.name}.txt", [script_text])
            outp = self.raw_dir / f"table-{install_key}-{c.name}.txt"
            base.command = [str(inst.oracle_path), "/silent", f"@{sp}",
                            str(c.left), str(c.right), str(outp)]
            base.script_text = script_text
            base.raw_report = str(outp)

            try:
                run = oracle_mod.run(inst.oracle_path, sp, str(c.left), str(c.right),
                                     outp, timeout=self.cfg.timeout, script_text=script_text)
            except OracleError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"oracle failed to run: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {c.name:<30} {exc}")
                continue

            base.exit_code = run.exit_code
            base.elapsed_s = run.elapsed_s
            base.artifacts["containment"] = run.containment
            base.artifacts["tree_killed"] = run.tree_killed

            if run.timed_out:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"oracle exceeded {self.cfg.timeout}s"
            elif run.exit_code != 0:
                base.verdict = Verdict.ERROR
                base.detail = f"exit {run.exit_code} ({oracle_mod.exit_meaning(run.exit_code)})"
            elif not run.report_exists or run.report_bytes == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "exit 0 but no report was written"
            else:
                got_raw = norm_mod.read_report(run.report_path)
                want_raw = norm_mod.read_report(c.golden_report)
                try:
                    got = norm_mod.normalize_text(got_raw)
                    want = norm_mod.normalize_text(want_raw)
                except NormalizerRefusal as exc:
                    base.verdict = Verdict.UNPARSEABLE
                    base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
                else:
                    base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                    base.normalized_report = self._save_normalized(
                        f"table-{install_key}-{c.name}", got.text)
                    same = got.structure == want.structure
                    base.parsed = {
                        "line_count": len(got.structure or ()),
                        "normalized_matches_golden": same,
                        "raw_bytes_equal_golden": got_raw == want_raw,
                    }
                    base.expected = {"line_count": len(want.structure or ())}
                    if same:
                        base.verdict = Verdict.PASS
                        base.detail = f"{len(got.structure or ())} normalized lines match"
                    else:
                        base.verdict = Verdict.FAIL
                        base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {c.name:<30} {base.detail}")
        return out

    def run_candidate_tables(self, cand_key: str) -> list[TestResult]:
        """Candidate table suite: script-vs-script against the golden.

        The candidate must accept the SAME ``data-report`` line the Oracle
        gets (``supports_table``); the archived golden -- produced by the
        Oracle from the same fixture paths that are passed here -- is the
        truth. This turns the golden tree into the recurring product gate
        docs/13 §4.9 decision 3 promised (replay scripts were the one-off
        bring-up check; the gate is the permanent one)."""
        c = self.cfg.candidates[cand_key]
        cases = man_mod.load_table_cases()
        out: list[TestResult] = []
        self.log(f"--- tables [candidate:{cand_key}] {c.label}")

        for cs in cases:
            base = TestResult(
                test_id=cs.name, suite="table", verdict=Verdict.NOT_RUN,
                subject="candidate", oracle_path=c.path,
                left=str(cs.left), right=str(cs.right),
                golden_report=str(cs.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"candidate_key": cand_key, "candidate_label": c.label,
                           "is_product": c.is_product,
                           "candidate_version": c.version,
                           "layout": cs.layout, "ext": cs.ext},
            )
            if not c.available or not c.supports_table:
                base.verdict = Verdict.NOT_RUN
                base.detail = ("candidate not available" if not c.available
                               else "candidate does not script-invoke data-report")
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue
            missing = cs.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue

            script_text = oracle_mod.table_script(cs.layout, cs.title)
            sp = oracle_mod.write_script(
                self.scripts_dir / f"cand-table-{cand_key}-{cs.name}.txt", [script_text])
            outp = self.raw_dir / f"cand-table-{cand_key}-{cs.name}.txt"
            cmd = c.script_command(script=str(sp), left=str(cs.left),
                                   right=str(cs.right), output=str(outp))
            base.command = cmd
            base.script_text = script_text
            started = time.perf_counter()
            try:
                cp = subprocess.run(cmd, capture_output=True, timeout=self.cfg.timeout,
                                    cwd=str(pathlib.Path(c.path).parent))
            except subprocess.TimeoutExpired:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"candidate exceeded {self.cfg.timeout}s"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  timeout {cs.name:<30}")
                continue
            except OSError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"candidate could not start: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            base.elapsed_s = round(time.perf_counter() - started, 3)
            base.exit_code = cp.returncode
            base.raw_report = str(outp)

            if cp.returncode != 0:
                base.verdict = Verdict.ERROR
                base.detail = (f"candidate exit {cp.returncode}: "
                               f"{cp.stderr.decode('utf-8', errors='replace')[:200]}")
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            if not outp.exists() or outp.stat().st_size == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "candidate exit 0 but wrote no report"
                out.append(self._record(base))
                self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
                continue

            got_raw = norm_mod.read_report(outp)
            want_raw = norm_mod.read_report(cs.golden_report)
            try:
                got = norm_mod.normalize_text(got_raw)
                want = norm_mod.normalize_text(want_raw)
            except NormalizerRefusal as exc:
                base.verdict = Verdict.UNPARSEABLE
                base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
            else:
                base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                base.normalized_report = self._save_normalized(
                    f"cand-table-{cand_key}-{cs.name}", got.text)
                same = got.structure == want.structure
                base.parsed = {"normalized_matches_golden": same,
                               "line_count": len(got.structure or ())}
                base.expected = {"line_count": len(want.structure or ())}
                if same:
                    base.verdict = Verdict.PASS
                    base.detail = "normalized table matches golden"
                else:
                    base.verdict = Verdict.FAIL
                    base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
        return out

    def run_hexes(self, install_key: str) -> list[TestResult]:
        """M7 hex suite: the binary goldens under ``verify/hex/``, run with
        the identical ``hex-report`` script, compared line-wise after
        label/time/path normalization (docs/14)."""
        inst = self.cfg.installs[install_key]
        cases = man_mod.load_hex_cases()
        out: list[TestResult] = []
        self.log(f"--- hex [{install_key}] {inst.app_version or '?'} "
                 f"({len(cases)} cases)")

        for c in cases:
            base = TestResult(
                test_id=c.name,
                suite="hex",
                verdict=Verdict.NOT_RUN,
                subject="oracle",
                oracle_version=inst.app_version,
                oracle_path=inst.oracle_path,
                left=str(c.left),
                right=str(c.right),
                golden_report=str(c.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"layout": c.layout, "note": c.note,
                           "golden_bytes": c.golden_bytes,
                           "golden_exit_code": c.golden_exit_code,
                           "install_key": install_key, "locale": inst.locale},
            )
            missing = c.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {c.name:<30} {base.detail}")
                continue

            script_text = oracle_mod.hex_script(c.layout, c.title)
            sp = oracle_mod.write_script(
                self.scripts_dir / f"hex-{install_key}-{c.name}.txt", [script_text])
            outp = self.raw_dir / f"hex-{install_key}-{c.name}.txt"
            base.command = [str(inst.oracle_path), "/silent", f"@{sp}",
                            str(c.left), str(c.right), str(outp)]
            base.script_text = script_text
            base.raw_report = str(outp)

            try:
                run = oracle_mod.run(inst.oracle_path, sp, str(c.left), str(c.right),
                                     outp, timeout=self.cfg.timeout,
                                     script_text=script_text)
            except OracleError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"oracle failed to run: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {c.name:<30} {exc}")
                continue

            base.exit_code = run.exit_code
            base.elapsed_s = run.elapsed_s
            base.artifacts["containment"] = run.containment
            base.artifacts["tree_killed"] = run.tree_killed

            if run.timed_out:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"oracle exceeded {self.cfg.timeout}s"
            elif run.exit_code != 0:
                base.verdict = Verdict.ERROR
                base.detail = f"exit {run.exit_code} ({oracle_mod.exit_meaning(run.exit_code)})"
            elif not run.report_exists or run.report_bytes == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "exit 0 but no report was written"
            else:
                got_raw = norm_mod.read_report(run.report_path)
                want_raw = norm_mod.read_report(c.golden_report)
                try:
                    got = norm_mod.normalize_text(got_raw)
                    want = norm_mod.normalize_text(want_raw)
                except NormalizerRefusal as exc:
                    base.verdict = Verdict.UNPARSEABLE
                    base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
                else:
                    base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                    base.normalized_report = self._save_normalized(
                        f"hex-{install_key}-{c.name}", got.text)
                    same = got.structure == want.structure
                    base.parsed = {
                        "line_count": len(got.structure or ()),
                        "normalized_matches_golden": same,
                        "raw_bytes_equal_golden": got_raw == want_raw,
                    }
                    base.expected = {"line_count": len(want.structure or ())}
                    if same:
                        base.verdict = Verdict.PASS
                        base.detail = f"{len(got.structure or ())} normalized lines match"
                    else:
                        base.verdict = Verdict.FAIL
                        base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {c.name:<30} {base.detail}")
        return out

    def run_candidate_hexes(self, cand_key: str) -> list[TestResult]:
        """Candidate hex suite: script-vs-script against the golden.

        The candidate must accept the SAME ``hex-report`` line the Oracle
        gets (``supports_hex``); the archived golden is the truth."""
        c = self.cfg.candidates[cand_key]
        cases = man_mod.load_hex_cases()
        out: list[TestResult] = []
        self.log(f"--- hex [candidate:{cand_key}] {c.label}")

        for cs in cases:
            base = TestResult(
                test_id=cs.name, suite="hex", verdict=Verdict.NOT_RUN,
                subject="candidate", oracle_path=c.path,
                left=str(cs.left), right=str(cs.right),
                golden_report=str(cs.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"candidate_key": cand_key, "candidate_label": c.label,
                           "is_product": c.is_product,
                           "candidate_version": c.version,
                           "layout": cs.layout},
            )
            if not c.available or not c.supports_hex:
                base.verdict = Verdict.NOT_RUN
                base.detail = ("candidate not available" if not c.available
                               else "candidate does not script-invoke hex-report")
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue
            missing = cs.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue

            script_text = oracle_mod.hex_script(cs.layout, cs.title)
            sp = oracle_mod.write_script(
                self.scripts_dir / f"cand-hex-{cand_key}-{cs.name}.txt", [script_text])
            outp = self.raw_dir / f"cand-hex-{cand_key}-{cs.name}.txt"
            cmd = c.script_command(script=str(sp), left=str(cs.left),
                                   right=str(cs.right), output=str(outp))
            base.command = cmd
            base.script_text = script_text
            started = time.perf_counter()
            try:
                cp = subprocess.run(cmd, capture_output=True, timeout=self.cfg.timeout,
                                    cwd=str(pathlib.Path(c.path).parent))
            except subprocess.TimeoutExpired:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"candidate exceeded {self.cfg.timeout}s"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  timeout {cs.name:<30}")
                continue
            except OSError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"candidate could not start: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            base.elapsed_s = round(time.perf_counter() - started, 3)
            base.exit_code = cp.returncode
            base.raw_report = str(outp)

            if cp.returncode != 0:
                base.verdict = Verdict.ERROR
                base.detail = (f"candidate exit {cp.returncode}: "
                               f"{cp.stderr.decode('utf-8', errors='replace')[:200]}")
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            if not outp.exists() or outp.stat().st_size == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "candidate exit 0 but wrote no report"
                out.append(self._record(base))
                self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
                continue

            got_raw = norm_mod.read_report(outp)
            want_raw = norm_mod.read_report(cs.golden_report)
            try:
                got = norm_mod.normalize_text(got_raw)
                want = norm_mod.normalize_text(want_raw)
            except NormalizerRefusal as exc:
                base.verdict = Verdict.UNPARSEABLE
                base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
            else:
                base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                base.normalized_report = self._save_normalized(
                    f"cand-hex-{cand_key}-{cs.name}", got.text)
                same = got.structure == want.structure
                base.parsed = {"normalized_matches_golden": same,
                               "line_count": len(got.structure or ())}
                base.expected = {"line_count": len(want.structure or ())}
                if same:
                    base.verdict = Verdict.PASS
                    base.detail = "normalized hex matches golden"
                else:
                    base.verdict = Verdict.FAIL
                    base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
        return out

    def run_pics(self, install_key: str) -> list[TestResult]:
        """M9 picture suite: the image goldens under ``verify/pic/``, run with
        the identical ``picture-report`` script line the probes measured,
        compared line-wise after label/time/path normalization (docs/16,
        norm-4)."""
        inst = self.cfg.installs[install_key]
        cases = man_mod.load_pic_cases()
        out: list[TestResult] = []
        self.log(f"--- pic [{install_key}] {inst.app_version or '?'} "
                 f"({len(cases)} cases)")

        for c in cases:
            base = TestResult(
                test_id=c.name,
                suite="pic",
                verdict=Verdict.NOT_RUN,
                subject="oracle",
                oracle_version=inst.app_version,
                oracle_path=inst.oracle_path,
                left=str(c.left) if c.left else "",
                right=str(c.right) if c.right else "",
                golden_report=str(c.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"layout": c.layout, "note": c.note,
                           "script": c.script,
                           "golden_bytes": c.golden_bytes,
                           "golden_exit_code": c.golden_exit_code,
                           "install_key": install_key, "locale": inst.locale},
            )
            missing = c.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {c.name:<30} {base.detail}")
                continue

            sp = oracle_mod.write_script(
                self.scripts_dir / f"pic-{install_key}-{c.name}.txt", [c.script])
            outp = self.raw_dir / f"pic-{install_key}-{c.name}.txt"
            lp = str(c.left) if c.left else ""
            rp = str(c.right) if c.right else ""
            base.command = [str(inst.oracle_path), "/silent", f"@{sp}",
                            lp, rp, str(outp)]
            base.script_text = c.script
            base.raw_report = str(outp)

            try:
                run = oracle_mod.run(inst.oracle_path, sp, lp, rp,
                                     outp, timeout=self.cfg.timeout,
                                     script_text=c.script)
            except OracleError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"oracle failed to run: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {c.name:<30} {exc}")
                continue

            base.exit_code = run.exit_code
            base.elapsed_s = run.elapsed_s
            base.artifacts["containment"] = run.containment
            base.artifacts["tree_killed"] = run.tree_killed

            if run.timed_out:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"oracle exceeded {self.cfg.timeout}s"
            elif run.exit_code != 0:
                base.verdict = Verdict.ERROR
                base.detail = f"exit {run.exit_code} ({oracle_mod.exit_meaning(run.exit_code)})"
            elif not run.report_exists or run.report_bytes == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "exit 0 but no report was written"
            else:
                got_raw = norm_mod.read_report(run.report_path)
                want_raw = norm_mod.read_report(c.golden_report)
                try:
                    got = norm_mod.normalize_text(got_raw)
                    want = norm_mod.normalize_text(want_raw)
                except NormalizerRefusal as exc:
                    base.verdict = Verdict.UNPARSEABLE
                    base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
                else:
                    base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                    base.normalized_report = self._save_normalized(
                        f"pic-{install_key}-{c.name}", got.text)
                    same = got.structure == want.structure
                    base.parsed = {
                        "line_count": len(got.structure or ()),
                        "normalized_matches_golden": same,
                        "raw_bytes_equal_golden": got_raw == want_raw,
                    }
                    base.expected = {"line_count": len(want.structure or ())}
                    if same:
                        base.verdict = Verdict.PASS
                        base.detail = f"{len(got.structure or ())} normalized lines match"
                    else:
                        base.verdict = Verdict.FAIL
                        base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {c.name:<30} {base.detail}")
        return out

    def run_regs(self, install_key: str) -> list[TestResult]:
        """M11 registry suite: the .reg goldens under ``verify/reg/``, run
        with the identical ``registry-report`` script line the probes
        measured, compared line-wise after label/time/path normalization
        (docs/17, norm-5).

        The goldens are authored from the REFERENCE (English) install, so
        the current (Chinese) install's re-run matches them only AFTER
        norm-5 folds the Chinese labels -- which is exactly the corroboration
        this suite exists to perform (the same "labels" argument as the
        m83k-m83m picture cells, now inside the channel suite itself).
        """
        inst = self.cfg.installs[install_key]
        cases = man_mod.load_reg_cases()
        out: list[TestResult] = []
        self.log(f"--- reg [{install_key}] {inst.app_version or '?'} "
                 f"({len(cases)} cases)")

        for c in cases:
            base = TestResult(
                test_id=c.name,
                suite="reg",
                verdict=Verdict.NOT_RUN,
                subject="oracle",
                oracle_version=inst.app_version,
                oracle_path=inst.oracle_path,
                left=str(c.left) if c.left else "",
                right=str(c.right) if c.right else "",
                golden_report=str(c.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"layout": c.layout, "note": c.note,
                           "script": c.script,
                           "golden_bytes": c.golden_bytes,
                           "golden_exit_code": c.golden_exit_code,
                           "install_key": install_key, "locale": inst.locale},
            )
            missing = c.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {c.name:<30} {base.detail}")
                continue

            sp = oracle_mod.write_script(
                self.scripts_dir / f"reg-{install_key}-{c.name}.txt", [c.script])
            outp = self.raw_dir / f"reg-{install_key}-{c.name}.txt"
            lp = str(c.left) if c.left else ""
            rp = str(c.right) if c.right else ""
            base.command = [str(inst.oracle_path), "/silent", f"@{sp}",
                            lp, rp, str(outp)]
            base.script_text = c.script
            base.raw_report = str(outp)

            try:
                run = oracle_mod.run(inst.oracle_path, sp, lp, rp,
                                     outp, timeout=self.cfg.timeout,
                                     script_text=c.script)
            except OracleError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"oracle failed to run: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {c.name:<30} {exc}")
                continue

            base.exit_code = run.exit_code
            base.elapsed_s = run.elapsed_s
            base.artifacts["containment"] = run.containment
            base.artifacts["tree_killed"] = run.tree_killed

            if run.timed_out:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"oracle exceeded {self.cfg.timeout}s"
            elif run.exit_code != 0:
                base.verdict = Verdict.ERROR
                base.detail = f"exit {run.exit_code} ({oracle_mod.exit_meaning(run.exit_code)})"
            elif not run.report_exists or run.report_bytes == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "exit 0 but no report was written"
            else:
                got_raw = norm_mod.read_report(run.report_path)
                want_raw = norm_mod.read_report(c.golden_report)
                try:
                    got = norm_mod.normalize_text(got_raw)
                    want = norm_mod.normalize_text(want_raw)
                except NormalizerRefusal as exc:
                    base.verdict = Verdict.UNPARSEABLE
                    base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
                else:
                    base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                    base.normalized_report = self._save_normalized(
                        f"reg-{install_key}-{c.name}", got.text)
                    same = got.structure == want.structure
                    base.parsed = {
                        "line_count": len(got.structure or ()),
                        "normalized_matches_golden": same,
                        "raw_bytes_equal_golden": got_raw == want_raw,
                    }
                    base.expected = {"line_count": len(want.structure or ())}
                    if same:
                        base.verdict = Verdict.PASS
                        base.detail = f"{len(got.structure or ())} normalized lines match"
                    else:
                        base.verdict = Verdict.FAIL
                        base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {c.name:<30} {base.detail}")
        return out

    def run_vers(self, install_key: str) -> list[TestResult]:
        """M112 version suite: the ver goldens under ``verify/ver/``, run
        with the identical ``version-report`` script line the probes
        measured, compared line-wise after label/time/path normalization
        (docs/18, norm-6).

        The goldens are authored from the REFERENCE (English) install, so
        the current (Chinese) install's re-run matches them only AFTER
        norm-6 folds the Chinese labels -- the same "labels" corroboration
        as the reg suite (docs/17).  The `Data` size row is the recorded
        U-ver-1 residual: norm-6 folds a size-only difference on that row
        and the rest must match byte-for-byte.
        """
        inst = self.cfg.installs[install_key]
        cases = man_mod.load_ver_cases()
        out: list[TestResult] = []
        self.log(f"--- ver [{install_key}] {inst.app_version or '?'} "
                 f"({len(cases)} cases)")

        for c in cases:
            base = TestResult(
                test_id=c.name,
                suite="ver",
                verdict=Verdict.NOT_RUN,
                subject="oracle",
                oracle_version=inst.app_version,
                oracle_path=inst.oracle_path,
                left=str(c.left) if c.left else "",
                right=str(c.right) if c.right else "",
                golden_report=str(c.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"layout": c.layout, "note": c.note,
                           "script": c.script,
                           "golden_bytes": c.golden_bytes,
                           "golden_exit_code": c.golden_exit_code,
                           "install_key": install_key, "locale": inst.locale},
            )
            missing = c.missing()
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {c.name:<30} {base.detail}")
                continue

            sp = oracle_mod.write_script(
                self.scripts_dir / f"ver-{install_key}-{c.name}.txt", [c.script])
            outp = self.raw_dir / f"ver-{install_key}-{c.name}.txt"
            lp = str(c.left) if c.left else ""
            rp = str(c.right) if c.right else ""
            base.command = [str(inst.oracle_path), "/silent", f"@{sp}",
                            lp, rp, str(outp)]
            base.script_text = c.script
            base.raw_report = str(outp)

            try:
                run = oracle_mod.run(inst.oracle_path, sp, lp, rp,
                                     outp, timeout=self.cfg.timeout,
                                     script_text=c.script)
            except OracleError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"oracle failed to run: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {c.name:<30} {exc}")
                continue

            base.exit_code = run.exit_code
            base.elapsed_s = run.elapsed_s
            base.artifacts["containment"] = run.containment
            base.artifacts["tree_killed"] = run.tree_killed

            if run.timed_out:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"oracle exceeded {self.cfg.timeout}s"
            elif run.exit_code != 0:
                base.verdict = Verdict.ERROR
                base.detail = f"exit {run.exit_code} ({oracle_mod.exit_meaning(run.exit_code)})"
            elif not run.report_exists or run.report_bytes == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "exit 0 but no report was written"
            else:
                got_raw = norm_mod.read_report(run.report_path)
                want_raw = norm_mod.read_report(c.golden_report)
                try:
                    got = norm_mod.normalize_text(got_raw)
                    want = norm_mod.normalize_text(want_raw)
                except NormalizerRefusal as exc:
                    base.verdict = Verdict.UNPARSEABLE
                    base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
                else:
                    base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                    base.normalized_report = self._save_normalized(
                        f"ver-{install_key}-{c.name}", got.text)
                    same = got.structure == want.structure
                    base.parsed = {
                        "line_count": len(got.structure or ()),
                        "normalized_matches_golden": same,
                        "raw_bytes_equal_golden": got_raw == want_raw,
                    }
                    base.expected = {"line_count": len(want.structure or ())}
                    if same:
                        base.verdict = Verdict.PASS
                        base.detail = f"{len(got.structure or ())} normalized lines match"
                    else:
                        base.verdict = Verdict.FAIL
                        base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {c.name:<30} {base.detail}")
        return out

    def run_candidate_pics(self, cand_key: str) -> list[TestResult]:
        """Candidate picture suite: script-vs-script against the golden.

        The candidate must accept the SAME ``picture-report`` line the Oracle
        gets (``supports_pic``); the archived golden is the truth. The zero-
        file cells take NO comparison arguments -- ``pic_script_command``
        passes the case's file list verbatim, which is why the left/right
        positions are not hardcoded here (docs/16 P8/O5)."""
        c = self.cfg.candidates[cand_key]
        cases = man_mod.load_pic_cases()
        out: list[TestResult] = []
        self.log(f"--- pic [candidate:{cand_key}] {c.label}")

        for cs in cases:
            base = TestResult(
                test_id=cs.name, suite="pic", verdict=Verdict.NOT_RUN,
                subject="candidate", oracle_path=c.path,
                left=str(cs.left) if cs.left else "",
                right=str(cs.right) if cs.right else "",
                golden_report=str(cs.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"candidate_key": cand_key, "candidate_label": c.label,
                           "is_product": c.is_product,
                           "candidate_version": c.version,
                           "layout": cs.layout},
            )
            if not c.available or not c.supports_pic:
                base.verdict = Verdict.NOT_RUN
                base.detail = ("candidate not available" if not c.available
                               else "candidate does not script-invoke picture-report")
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue
            missing = cs.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue

            sp = oracle_mod.write_script(
                self.scripts_dir / f"cand-pic-{cand_key}-{cs.name}.txt", [cs.script])
            outp = self.raw_dir / f"cand-pic-{cand_key}-{cs.name}.txt"
            # ALWAYS three positional slots, like the Oracle call: the
            # zero-file shell goldens got "" for left/right in the probe
            # (the script references only %3), so the candidate must see
            # empty strings too -- dropping them would shift %3 off the
            # output path (P8/O5).
            files = [str(cs.left) if cs.left else "",
                     str(cs.right) if cs.right else ""]
            cmd = c.pic_script_command(script=str(sp), files=files,
                                       output=str(outp))
            base.command = cmd
            base.script_text = cs.script
            started = time.perf_counter()
            try:
                cp = subprocess.run(cmd, capture_output=True, timeout=self.cfg.timeout,
                                    cwd=str(pathlib.Path(c.path).parent))
            except subprocess.TimeoutExpired:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"candidate exceeded {self.cfg.timeout}s"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  timeout {cs.name:<30}")
                continue
            except OSError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"candidate could not start: {exc}"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            base.elapsed_s = round(time.perf_counter() - started, 3)
            base.exit_code = cp.returncode
            base.raw_report = str(outp)

            if cp.returncode != 0:
                base.verdict = Verdict.ERROR
                base.detail = (f"candidate exit {cp.returncode}: "
                               f"{cp.stderr.decode('utf-8', errors='replace')[:200]}")
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            if not outp.exists() or outp.stat().st_size == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "candidate exit 0 but wrote no report"
                out.append(self._record(base))
                self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
                continue

            got_raw = norm_mod.read_report(outp)
            want_raw = norm_mod.read_report(cs.golden_report)
            try:
                got = norm_mod.normalize_text(got_raw)
                want = norm_mod.normalize_text(want_raw)
            except NormalizerRefusal as exc:
                base.verdict = Verdict.UNPARSEABLE
                base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
            else:
                base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                base.normalized_report = self._save_normalized(
                    f"cand-pic-{cand_key}-{cs.name}", got.text)
                same = got.structure == want.structure
                base.parsed = {"normalized_matches_golden": same,
                               "line_count": len(got.structure or ())}
                base.expected = {"line_count": len(want.structure or ())}
                if same:
                    base.verdict = Verdict.PASS
                    base.detail = "normalized picture matches golden"
                else:
                    base.verdict = Verdict.FAIL
                    base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
        return out

    def run_candidate_regs(self, cand_key: str) -> list[TestResult]:
        """Candidate registry suite: script-vs-script against the golden.

        The candidate must accept the SAME ``registry-report`` line the Oracle
        gets (``supports_reg``); the archived golden is the truth.  The
        goldens are the English (reference-install) form, which is exactly
        what the product renders (the dir/pic/hex precedent), so this is a
        byte-level comparison of the product's frame + table, not a folded
        one -- the folding is the ORACLE suite's job when it re-runs the
        Chinese install."""
        c = self.cfg.candidates[cand_key]
        cases = man_mod.load_reg_cases()
        out: list[TestResult] = []
        self.log(f"--- reg [candidate:{cand_key}] {c.label}")

        for cs in cases:
            base = TestResult(
                test_id=cs.name, suite="reg", verdict=Verdict.NOT_RUN,
                subject="candidate", oracle_path=c.path,
                left=str(cs.left) if cs.left else "",
                right=str(cs.right) if cs.right else "",
                golden_report=str(cs.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"candidate_key": cand_key, "candidate_label": c.label,
                           "is_product": c.is_product,
                           "candidate_version": c.version,
                           "layout": cs.layout},
            )
            if not c.available or not c.supports_reg:
                base.verdict = Verdict.NOT_RUN
                base.detail = ("candidate not available" if not c.available
                               else "candidate does not script-invoke registry-report")
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue
            missing = cs.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue

            sp = oracle_mod.write_script(
                self.scripts_dir / f"cand-reg-{cand_key}-{cs.name}.txt", [cs.script])
            outp = self.raw_dir / f"cand-reg-{cand_key}-{cs.name}.txt"
            # ALWAYS two positional slots, like the Oracle call: a zero-file
            # cell's script references only %3, and dropping the arguments
            # would shift %3 off the output path (the picture P8/O5 lesson).
            files = [str(cs.left) if cs.left else "",
                     str(cs.right) if cs.right else ""]
            cmd = c.pic_script_command(script=str(sp), files=files,
                                       output=str(outp))
            base.command = cmd
            base.script_text = cs.script
            started = time.perf_counter()
            try:
                cp = subprocess.run(cmd, capture_output=True, timeout=self.cfg.timeout,
                                    cwd=str(pathlib.Path(c.path).parent))
            except subprocess.TimeoutExpired:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"candidate exceeded {self.cfg.timeout}s"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  timeout {cs.name:<30}")
                continue
            except OSError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"candidate could not start: {exc}"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            base.elapsed_s = round(time.perf_counter() - started, 3)
            base.exit_code = cp.returncode
            base.raw_report = str(outp)

            if cp.returncode != 0:
                base.verdict = Verdict.ERROR
                base.detail = (f"candidate exit {cp.returncode}: "
                               f"{cp.stderr.decode('utf-8', errors='replace')[:200]}")
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            if not outp.exists() or outp.stat().st_size == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "candidate exit 0 but wrote no report"
                out.append(self._record(base))
                self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
                continue

            got_raw = norm_mod.read_report(outp)
            want_raw = norm_mod.read_report(cs.golden_report)
            try:
                got = norm_mod.normalize_text(got_raw)
                want = norm_mod.normalize_text(want_raw)
            except NormalizerRefusal as exc:
                base.verdict = Verdict.UNPARSEABLE
                base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
            else:
                base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                base.normalized_report = self._save_normalized(
                    f"cand-reg-{cand_key}-{cs.name}", got.text)
                same = got.structure == want.structure
                base.parsed = {"normalized_matches_golden": same,
                               "line_count": len(got.structure or ())}
                base.expected = {"line_count": len(want.structure or ())}
                if same:
                    base.verdict = Verdict.PASS
                    base.detail = "normalized registry matches golden"
                else:
                    base.verdict = Verdict.FAIL
                    base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
        return out

    def run_candidate_vers(self, cand_key: str) -> list[TestResult]:
        """Candidate version suite: script-vs-script against the golden.

        The candidate must accept the SAME ``version-report`` line the Oracle
        gets (``supports_ver``); the archived golden is the truth.  The
        goldens are the English (reference-install) form, which is exactly
        what the product renders, so this is a byte-level comparison of the
        product's frame + table.  The `Data` size row is the recorded U-ver-1
        residual: norm-6 folds a size-only difference on that row."""
        c = self.cfg.candidates[cand_key]
        cases = man_mod.load_ver_cases()
        out: list[TestResult] = []
        self.log(f"--- ver [candidate:{cand_key}] {c.label}")

        for cs in cases:
            base = TestResult(
                test_id=cs.name, suite="ver", verdict=Verdict.NOT_RUN,
                subject="candidate", oracle_path=c.path,
                left=str(cs.left) if cs.left else "",
                right=str(cs.right) if cs.right else "",
                golden_report=str(cs.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"candidate_key": cand_key, "candidate_label": c.label,
                           "is_product": c.is_product,
                           "candidate_version": c.version,
                           "layout": cs.layout},
            )
            if not c.available or not c.supports_ver:
                base.verdict = Verdict.NOT_RUN
                base.detail = ("candidate not available" if not c.available
                               else "candidate does not script-invoke version-report")
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue
            missing = cs.missing()
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<30} {base.detail}")
                continue

            sp = oracle_mod.write_script(
                self.scripts_dir / f"cand-ver-{cand_key}-{cs.name}.txt", [cs.script])
            outp = self.raw_dir / f"cand-ver-{cand_key}-{cs.name}.txt"
            # ALWAYS two positional slots, like the Oracle call (the picture
            # P8/O5 lesson): a zero-file cell's script references only %3.
            files = [str(cs.left) if cs.left else "",
                     str(cs.right) if cs.right else ""]
            cmd = c.pic_script_command(script=str(sp), files=files,
                                       output=str(outp))
            base.command = cmd
            base.script_text = cs.script
            started = time.perf_counter()
            try:
                cp = subprocess.run(cmd, capture_output=True, timeout=self.cfg.timeout,
                                    cwd=str(pathlib.Path(c.path).parent))
            except subprocess.TimeoutExpired:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"candidate exceeded {self.cfg.timeout}s"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  timeout {cs.name:<30}")
                continue
            except OSError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"candidate could not start: {exc}"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            base.elapsed_s = round(time.perf_counter() - started, 3)
            base.exit_code = cp.returncode
            base.raw_report = str(outp)

            if cp.returncode != 0:
                base.verdict = Verdict.ERROR
                base.detail = (f"candidate exit {cp.returncode}: "
                               f"{cp.stderr.decode('utf-8', errors='replace')[:200]}")
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<30} {base.detail}")
                continue
            if not outp.exists() or outp.stat().st_size == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "candidate exit 0 but wrote no report"
                out.append(self._record(base))
                self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
                continue

            got_raw = norm_mod.read_report(outp)
            want_raw = norm_mod.read_report(cs.golden_report)
            try:
                got = norm_mod.normalize_text(got_raw)
                want = norm_mod.normalize_text(want_raw)
            except NormalizerRefusal as exc:
                base.verdict = Verdict.UNPARSEABLE
                base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
            else:
                base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                base.normalized_report = self._save_normalized(
                    f"cand-ver-{cand_key}-{cs.name}", got.text)
                same = got.structure == want.structure
                base.parsed = {
                    "line_count": len(got.structure or ()),
                    "normalized_matches_golden": same,
                    "raw_bytes_equal_golden": got_raw == want_raw,
                }
                base.expected = {"line_count": len(want.structure or ())}
                if same:
                    base.verdict = Verdict.PASS
                    base.detail = f"{len(got.structure or ())} normalized lines match"
                else:
                    base.verdict = Verdict.FAIL
                    base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {cs.name:<30} {base.detail}")
        return out

    def run_folder(self, install_key: str) -> list[TestResult]:
        inst = self.cfg.installs[install_key]
        cases = man_mod.load_folder_cases()
        out: list[TestResult] = []
        self.log(f"--- folder [{install_key}] {inst.app_version or '?'} "
                 f"({len(cases)} case(s))")

        for c in cases:
            base = TestResult(
                test_id=f"{c.name}-xml",
                suite="folder",
                verdict=Verdict.NOT_RUN,
                subject="oracle",
                oracle_version=inst.app_version,
                oracle_path=inst.oracle_path,
                left=str(c.left),
                right=str(c.right),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={
                    "install_key": install_key, "locale": inst.locale,
                    "recipe": "load -> expand all -> folder-report layout:xml",
                    "stored_report_manifest": str(c.stored_report_manifest or ""),
                    "stored_manifest_entries": c.stored_manifest_entries,
                },
            )
            missing = c.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {base.test_id:<20} {base.detail}")
                continue

            sp = oracle_mod.write_script(
                self.scripts_dir / f"folder-{install_key}-{c.name}.txt",
                list(oracle_mod.FOLDER_SCRIPT_LINES))
            outp = self.raw_dir / f"folder-{install_key}-{c.name}.xml"
            base.script_text = "\n".join(oracle_mod.FOLDER_SCRIPT_LINES)
            base.command = [str(inst.oracle_path), "/silent", f"@{sp}",
                            str(c.left), str(c.right), str(outp)]
            base.raw_report = str(outp)

            try:
                run = oracle_mod.run(inst.oracle_path, sp, str(c.left), str(c.right),
                                     outp, timeout=self.cfg.timeout, script_text=base.script_text)
            except OracleError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"oracle failed to run: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {base.test_id:<20} {exc}")
                continue

            base.exit_code = run.exit_code
            base.elapsed_s = run.elapsed_s
            base.artifacts["containment"] = run.containment
            base.artifacts["tree_killed"] = run.tree_killed

            if run.timed_out:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"oracle exceeded {self.cfg.timeout}s"
            elif run.exit_code != 0:
                base.verdict = Verdict.ERROR
                base.detail = (f"exit {run.exit_code} "
                               f"({oracle_mod.exit_meaning(run.exit_code)})")
            elif not run.report_exists or run.report_bytes == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "exit 0 but no report was written"
            else:
                got_raw = norm_mod.read_report(run.report_path)
                try:
                    got = norm_mod.normalize_xml(got_raw)
                except NormalizerRefusal as exc:
                    base.verdict = Verdict.UNPARSEABLE
                    base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
                else:
                    base.rules_applied = sorted(set(got.rules_applied))
                    base.normalized_report = self._save_normalized(
                        f"folder-{install_key}-{c.name}", got.text)
                    filecomp = [(t, a) for (t, a) in got.structure
                                if t == "filecomp"]
                    base.parsed = {
                        "filecomp_count": len(filecomp),
                        "filecomp_statuses": [dict(a).get("status") for _, a in filecomp],
                        "report_bytes": run.report_bytes,
                    }
                    # The documented recipe is verified when the Oracle exits 0
                    # AND the report is a structurally valid folder report that
                    # the normalizer accepts.  There is no golden folder report
                    # to compare against (the stored one is the broken run), so
                    # this is a recipe/coverage check, NOT a compatibility claim.
                    base.verdict = Verdict.PASS
                    base.detail = (f"recipe ok, exit 0, {run.report_bytes} bytes, "
                                   f"{len(filecomp)} filecomp entries parsed")
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {base.test_id:<20} {base.detail}")
        return out

    # ------------------------------------------------------------------
    # Candidate suites
    # ------------------------------------------------------------------
    def run_candidate_anchors(self, cand_key: str) -> list[TestResult]:
        """Run the candidate CLI over the anchors and compare to golden.

        The candidate emits its report on stdout (prototype behaviour) or to a
        file; both are handled via the adapter config.  The comparison is
        candidate-vs-golden, i.e. a compatibility measurement of the candidate,
        never a statement about the Oracle.
        """
        c = self.cfg.candidates[cand_key]
        anchors = man_mod.load_anchors()
        out: list[TestResult] = []
        self.log(f"--- anchors [candidate:{cand_key}] {c.label}")

        for a in anchors:
            base = TestResult(
                test_id=a.name, suite="anchor", verdict=Verdict.NOT_RUN,
                subject="candidate", oracle_version="", oracle_path=c.path,
                left=str(a.left), right=str(a.right),
                golden_report=str(a.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"candidate_key": cand_key,
                           "candidate_label": c.label,
                           "is_product": c.is_product,
                           "candidate_version": c.version,
                           "golden_statuses": a.statuses},
            )
            if not c.available:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"candidate not available at {c.path}"
                out.append(self._record(base))
                self.log(f"  not_run {a.name:<26} {base.detail}")
                continue
            missing = a.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {a.name:<26} {base.detail}")
                continue

            outp = self.raw_dir / f"cand-{cand_key}-{a.name}.xml"
            cmd = c.command(left=str(a.left), right=str(a.right), output=str(outp),
                            options=a.options)
            base.command = cmd
            started = time.perf_counter()
            try:
                cp = subprocess.run(cmd, capture_output=True, timeout=self.cfg.timeout,
                                    cwd=str(pathlib.Path(c.path).parent))
            except subprocess.TimeoutExpired:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"candidate exceeded {self.cfg.timeout}s"
                base.elapsed_s = round(time.perf_counter() - started, 3)
                out.append(self._record(base))
                self.log(f"  timeout {a.name:<26}")
                continue
            except OSError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"candidate could not start: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {a.name:<26} {base.detail}")
                continue
            base.elapsed_s = round(time.perf_counter() - started, 3)
            base.exit_code = cp.returncode

            if cp.returncode != 0:
                base.verdict = Verdict.ERROR
                base.detail = (f"candidate exit {cp.returncode}: "
                               f"{cp.stderr.decode('utf-8', errors='replace')[:200]}")
                out.append(self._record(base))
                self.log(f"  error   {a.name:<26} {base.detail}")
                continue

            if c.report_on_stdout:
                text = cp.stdout.decode("utf-8", errors="replace")
                outp.write_text(text, encoding="utf-8")
            else:
                text = norm_mod.read_report(outp) if outp.exists() else ""

            base.raw_report = str(outp)
            if not text.strip():
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "candidate produced no report"
            else:
                got_statuses = man_mod.statuses_from_xml(text)
                base.parsed = {"statuses": got_statuses}
                base.expected = {"statuses": a.statuses}
                if got_statuses == a.statuses:
                    base.verdict = Verdict.PASS
                    base.detail = f"statuses match ({len(got_statuses)})"
                else:
                    base.verdict = Verdict.FAIL
                    base.detail = f"statuses differ: got {got_statuses} want {a.statuses}"
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {a.name:<26} {base.detail}")
        return out

    def run_candidate_layouts(self, cand_key: str) -> list[TestResult]:
        c = self.cfg.candidates[cand_key]
        cases = man_mod.load_layouts()
        out: list[TestResult] = []
        self.log(f"--- layouts [candidate:{cand_key}] {c.label}")

        for cs in cases:
            base = TestResult(
                test_id=cs.name, suite="layout", verdict=Verdict.NOT_RUN,
                subject="candidate", oracle_path=c.path,
                left=str(cs.left), right=str(cs.right),
                golden_report=str(cs.golden_report),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"candidate_key": cand_key, "candidate_label": c.label,
                           "is_product": c.is_product,
                           "candidate_version": c.version, "layout": cs.layout},
            )
            if not c.available:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"candidate not available at {c.path}"
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<28} {base.detail}")
                continue
            missing = cs.missing
            if missing:
                base.verdict = Verdict.NOT_RUN
                base.detail = f"fixture missing: {missing}"
                out.append(self._record(base))
                self.log(f"  not_run {cs.name:<28} {base.detail}")
                continue

            outp = self.raw_dir / f"cand-{cand_key}-{cs.name}.txt"
            cmd = c.command(left=str(cs.left), right=str(cs.right), output=str(outp),
                            layout=cs.layout)
            base.command = cmd
            started = time.perf_counter()
            try:
                cp = subprocess.run(cmd, capture_output=True, timeout=self.cfg.timeout,
                                    cwd=str(pathlib.Path(c.path).parent))
            except subprocess.TimeoutExpired:
                base.verdict = Verdict.TIMEOUT
                base.detail = f"candidate exceeded {self.cfg.timeout}s"
                out.append(self._record(base))
                self.log(f"  timeout {cs.name:<28}")
                continue
            except OSError as exc:
                base.verdict = Verdict.ERROR
                base.detail = f"candidate could not start: {exc}"
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<28} {base.detail}")
                continue
            base.elapsed_s = round(time.perf_counter() - started, 3)
            base.exit_code = cp.returncode

            if cp.returncode != 0:
                base.verdict = Verdict.ERROR
                base.detail = (f"candidate exit {cp.returncode}: "
                               f"{cp.stderr.decode('utf-8', errors='replace')[:200]}")
                out.append(self._record(base))
                self.log(f"  error   {cs.name:<28} {base.detail}")
                continue

            text = (cp.stdout.decode("utf-8", errors="replace") if c.report_on_stdout
                    else (norm_mod.read_report(outp)
                          if outp.exists() else ""))
            if c.report_on_stdout:
                outp.write_text(text, encoding="utf-8")
            base.raw_report = str(outp)

            if not text.strip():
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "candidate produced no report"
            else:
                want_raw = norm_mod.read_report(cs.golden_report)
                try:
                    got = norm_mod.normalize_text(text)
                    want = norm_mod.normalize_text(want_raw)
                except NormalizerRefusal as exc:
                    base.verdict = Verdict.UNPARSEABLE
                    base.detail = f"normalizer refused ({exc.reason}): {exc.detail}"
                else:
                    base.rules_applied = sorted(set(got.rules_applied + want.rules_applied))
                    base.normalized_report = self._save_normalized(
                        f"cand-{cand_key}-{cs.name}", got.text)
                    same = got.structure == want.structure
                    base.parsed = {"normalized_matches_golden": same}
                    if same:
                        base.verdict = Verdict.PASS
                        base.detail = "normalized layout matches golden"
                    else:
                        base.verdict = Verdict.FAIL
                        base.detail = _first_line_diff(got.structure, want.structure)
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {cs.name:<28} {base.detail}")
        return out

    # ------------------------------------------------------------------
    # reference-label corroboration
    # ------------------------------------------------------------------
    def run_reference_corroboration(self) -> list[TestResult]:
        """Re-derive the label pairs against the reference install.

        This is what makes the label table *observed* rather than *asserted*:
        the same fixtures are run on the reference install and the resulting
        English text is compared with the Chinese text the current install
        produced, after normalisation both must land on the same string.
        """
        if not self.cfg.include_reference_labels:
            return []
        ref = self.cfg.installs.get("reference")
        if ref is None or not ref.enabled:
            r = TestResult(test_id="label-pairs-corrob", suite="labels",
                           verdict=Verdict.NOT_RUN, subject="oracle",
                           detail="reference install unavailable")
            self._record(r)
            return [r]
        out: list[TestResult] = []
        self.log("--- label corroboration [reference install]")
        for c in man_mod.load_layouts():
            if c.missing:
                continue
            sp = oracle_mod.write_script(
                self.scripts_dir / f"ref-{c.name}.txt", [oracle_mod.text_script(c.layout)])
            outp = self.raw_dir / f"ref-{c.name}.txt"
            try:
                run = oracle_mod.run(ref.oracle_path, sp, str(c.left), str(c.right),
                                     outp, timeout=self.cfg.timeout)
            except OracleError as exc:
                out.append(self._record(TestResult(
                    test_id=f"ref-{c.name}", suite="labels", verdict=Verdict.ERROR,
                    subject="oracle", oracle_version=ref.app_version,
                    oracle_path=ref.oracle_path, detail=str(exc))))
                continue
            base = TestResult(
                test_id=f"ref-{c.name}", suite="labels", verdict=Verdict.NOT_RUN,
                subject="oracle", oracle_version=ref.app_version,
                oracle_path=ref.oracle_path, left=str(c.left), right=str(c.right),
                exit_code=run.exit_code, elapsed_s=run.elapsed_s,
                command=run.command, raw_report=str(outp),
                normalizer_ruleset=norm_mod.RULESET_VERSION,
                artifacts={"install_key": "reference", "locale": ref.locale,
                           "layout": c.layout,
                           "containment": run.containment,
                           "tree_killed": run.tree_killed},
            )
            if run.timed_out:
                base.verdict = Verdict.TIMEOUT
                base.detail = "reference oracle timed out"
            elif run.exit_code != 0:
                base.verdict = Verdict.ERROR
                base.detail = f"exit {run.exit_code}"
            elif not run.report_exists or run.report_bytes == 0:
                base.verdict = Verdict.MISSING_OUTPUT
                base.detail = "no report written"
            else:
                ref_raw = norm_mod.read_report(outp)
                cur_raw_path = self.raw_dir / f"layout-current-{c.name}.txt"
                cur_raw = (norm_mod.read_report(cur_raw_path)
                           if cur_raw_path.exists() else None)
                if cur_raw is None:
                    base.verdict = Verdict.NOT_RUN
                    base.detail = "current-install report absent; run layouts first"
                else:
                    try:
                        a = norm_mod.normalize_text(cur_raw)
                        b = norm_mod.normalize_text(ref_raw)
                    except NormalizerRefusal as exc:
                        base.verdict = Verdict.UNPARSEABLE
                        base.detail = f"{exc.reason}: {exc.detail}"
                    else:
                        same = a.structure == b.structure
                        base.parsed = {"normalized_equal_across_locales": same,
                                       "lines": len(a.structure or ())}
                        if same:
                            base.verdict = Verdict.PASS
                            base.detail = ("zh and en reports normalise to the same "
                                           "string; label mapping corroborated")
                        else:
                            base.verdict = Verdict.FAIL
                            base.detail = ("normalised zh/en reports differ -- label "
                                           "table incomplete: "
                                           + _first_line_diff(a.structure, b.structure))
            out.append(self._record(base))
            self.log(f"  {base.verdict.value:<14} {base.test_id:<28} {base.detail}")
        return out


def _first_line_diff(a, b) -> str:
    a = list(a or ())
    b = list(b or ())
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else "<none>"
        y = b[i] if i < len(b) else "<none>"
        if x != y:
            return f"line {i}: got {x!r} want {y!r}"
    return "no line differs (equal)"


#: Matches the ``Produced: <timestamp>`` line in either language.  Used only to
#: produce the "how much of the match is the engine" figure; it is NOT a
#: comparison rule (comparison uses the versioned rules in ``normalize``).
#: The colon differs by language -- ASCII ``:`` in English output, fullwidth
#: ``：`` in the Chinese repack -- so both must be accepted.
_VOLATILE_TIME_RE = re.compile(
    r"^(?:Produced|已产生)[:：]? ?\d{4}/\d\d/\d\d \d{1,2}:\d\d:\d\d$")


def _strip_volatile_only(text: str) -> str:
    """Text with ONLY the volatile timestamp line blanked.

    This deliberately does not apply the label table: it answers "did the raw
    bytes agree apart from the wall clock", which is the stricter question the
    run report wants to show next to the normalized figure.
    """
    return "\n".join("" if _VOLATILE_TIME_RE.match(ln) else ln
                     for ln in text.splitlines())
