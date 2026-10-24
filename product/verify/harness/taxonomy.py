"""Result taxonomy for the verification harness.

Verdicts are deliberately disjoint.  ``ERROR``/``MISSING_OUTPUT``/``TIMEOUT``/
``UNPARSEABLE``/``NOT_RUN`` are *never* counted as passes, and the aggregator in
``runner`` refuses to fold them into ``pass``.

Precedence when several conditions hold at once (highest first):

1. ``TIMEOUT``          -- the Oracle (or candidate) exceeded its deadline.
2. ``ERROR``            -- the process could not be run at all, or the Oracle
                           reported a non-zero exit status that is not a
                           comparable-report outcome (104/105/106/107...).
3. ``MISSING_OUTPUT``   -- exit was 0 but the expected report file is absent or
                           zero bytes.
4. ``UNPARSEABLE``      -- the report exists but the normalizer / parser refused
                           it (unknown tags, malformed XML, body-change in a
                           header-only rule, ...).  This is the
                           "needs-normalizer-update" signal.
5. ``PASS`` / ``FAIL``  -- both sides parsed and were compared.
6. ``NOT_RUN``          -- the test was skipped before execution (e.g. fixture
                           missing, or the version was disabled by policy).
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field, asdict
from typing import Any


class Verdict(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    MISSING_OUTPUT = "missing_output"
    TIMEOUT = "timeout"
    UNPARSEABLE = "unparseable"
    NOT_RUN = "not_run"


#: Verdicts that must never be aggregated into a pass count.
NON_PASS_VERDICTS = (
    Verdict.FAIL,
    Verdict.ERROR,
    Verdict.MISSING_OUTPUT,
    Verdict.TIMEOUT,
    Verdict.UNPARSEABLE,
    Verdict.NOT_RUN,
)

#: Verdicts that mean "the test executed and produced a comparable outcome".
COMPARED_VERDICTS = (Verdict.PASS, Verdict.FAIL)


class OracleError(RuntimeError):
    """The Oracle process itself failed in a way the harness must surface."""

    def __init__(self, message: str, *, exit_code: int | None = None,
                 command: list[str] | None = None, stderr: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.command = command or []
        self.stderr = stderr


class NormalizerRefusal(RuntimeError):
    """A normalization rule refused to handle the input.

    Raised instead of guessing.  Carries a machine-readable ``reason`` so the
    run report can point at the exact rule that needs updating.
    """

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass
class TestResult:
    """One executed (or deliberately skipped) test.

    Every field the task statement requires is present: test id, fixture paths,
    Oracle version + path, full command line, exit code, elapsed time, raw
    report path, parsed result, normalizer rule-set version, verdict.
    """

    test_id: str
    suite: str                       # "anchor" | "layout" | "folder"
    verdict: Verdict

    #: Tells pytest this dataclass is not a test class to collect.
    __test__ = False

    # subject under test
    subject: str = "oracle"          # "oracle" | "candidate"
    oracle_version: str = ""
    oracle_path: str = ""
    command: list[str] = field(default_factory=list)
    script_text: str = ""

    # fixtures
    left: str = ""
    right: str = ""
    golden_report: str = ""

    # execution
    exit_code: int | None = None
    elapsed_s: float = 0.0
    raw_report: str = ""             # path to the (pre-normalization) report
    normalized_report: str = ""      # path to the post-normalization report

    # comparison
    parsed: Any = None               # normalized comparison key / structure
    expected: Any = None
    normalizer_ruleset: str = ""
    rules_applied: list[str] = field(default_factory=list)
    detail: str = ""
    known_difference: str = ""       # non-empty => documented divergence
    artifacts: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


def summarize(results: list[TestResult]) -> dict[str, Any]:
    """Aggregate verdicts.  Non-pass verdicts are always broken out."""
    counts = {v.value: 0 for v in Verdict}
    for r in results:
        counts[r.verdict.value] += 1
    total = len(results)
    passed = counts[Verdict.PASS.value]
    return {
        "total": total,
        "pass": passed,
        "fail": counts[Verdict.FAIL.value],
        "error": counts[Verdict.ERROR.value],
        "missing_output": counts[Verdict.MISSING_OUTPUT.value],
        "timeout": counts[Verdict.TIMEOUT.value],
        "unparseable": counts[Verdict.UNPARSEABLE.value],
        "not_run": counts[Verdict.NOT_RUN.value],
        # "compared" = executed far enough to produce a judgement
        "compared": passed + counts[Verdict.FAIL.value],
        "pass_rate_of_compared": (
            round(passed / (passed + counts[Verdict.FAIL.value]), 4)
            if (passed + counts[Verdict.FAIL.value]) else None
        ),
        "pass_rate_of_total": round(passed / total, 4) if total else None,
    }


def summarize_by(results: list[TestResult], key) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[TestResult]] = {}
    for r in results:
        buckets.setdefault(key(r), []).append(r)
    return {k: summarize(v) for k, v in sorted(buckets.items())}


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=False)
