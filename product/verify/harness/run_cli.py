#!/usr/bin/env python3
"""Unified verification runner for ReaCompare (task A-1 / M0).

Examples
--------
Full run, current install only (the project target), 45 anchors + 30 layouts +
folder recipe::

    python -m harness.run_cli

Full run including the reference install (English 5.2.6.32774) so label
pairs are corroborated rather than asserted, and the old prototype candidate::

    python -m harness.run_cli --install current --install reference --candidate bcx-prototype

Identity only, no Oracle calls::

    python -m harness.run_cli --identity-only

Anchor suite only, no candidate, output to a named run directory::

    python -m harness.run_cli --suite anchor --run-name anchors-only
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

if __package__ in (None, ""):                       # allow `python run_cli.py`
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from harness import (candidate as cand_mod, installs as inst_mod,
                         normalize as norm_mod, report as rep_mod,
                         runner as run_mod)
    from harness import HARNESS_VERSION
else:
    from . import (candidate as cand_mod, installs as inst_mod,
                   normalize as norm_mod, report as rep_mod, runner as run_mod)
    from . import HARNESS_VERSION

DEFAULT_RESULTS_ROOT = pathlib.Path(r"D:\Rea\product\verify\runs")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m harness.run_cli",
        description="ReaCompare unified Oracle verification runner (A-1 / M0).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--install", action="append", default=None,
                   choices=["current", "reference"],
                   help="Oracle install to exercise (repeatable). Default: current.")
    p.add_argument("--candidate", action="append", default=None,
                   help="Candidate adapter key to exercise (repeatable). "
                        "Available: bcx-prototype, reacmp. Default: none.")
    p.add_argument("--suite", action="append", default=None,
                   choices=["anchor", "layout", "table", "hex", "pic", "reg", "ver", "folder", "labels"],
                   help="Suite to run (repeatable). Default: all.")
    p.add_argument("--run-name", default=None,
                   help="Name for this run directory under product/verify/runs/. "
                        "Default: UTC timestamp.")
    p.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT),
                   help="Where run directories are created.")
    p.add_argument("--timeout", type=float, default=180.0,
                   help="Per-invocation timeout in seconds (default 180).")
    p.add_argument("--no-reference-labels", action="store_true",
                   help="Skip the cross-locale label corroboration suite.")
    p.add_argument("--identity-only", action="store_true",
                   help="Print install/candidate identity and exit without running.")
    p.add_argument("--json-only", action="store_true",
                   help="Print only the JSON payload path, not the summary.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    install_keys = args.install or ["current"]
    suites = tuple(args.suite) if args.suite else ("anchor", "layout", "table", "hex", "pic", "reg", "ver", "folder", "labels")

    installs = {k: v for k, v in inst_mod.discover().items() if k in install_keys}
    candidates = cand_mod.load_candidates()
    if args.candidate:
        wanted = set(args.candidate)
        unknown = wanted - set(candidates)
        if unknown:
            print(f"error: unknown candidate key(s): {sorted(unknown)}", file=sys.stderr)
            print(cand_mod.candidate_report(candidates), file=sys.stderr)
            return 2
        candidates = {k: v for k, v in candidates.items() if k in wanted}
    else:
        candidates = {}

    if args.identity_only:
        print(inst_mod.identity_report(installs))
        print(cand_mod.candidate_report(candidates or cand_mod.load_candidates()))
        return 0

    started = datetime.now(timezone.utc)
    run_name = args.run_name or started.strftime("%Y%m%dT%H%M%SZ")
    results_dir = pathlib.Path(args.results_root) / run_name
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("ReaCompare unified Oracle harness (A-1 / M0)")
    print(f"harness={HARNESS_VERSION}  normalizer={norm_mod.RULESET_VERSION}")
    print(f"run dir: {results_dir}")
    print("=" * 78)
    print(inst_mod.identity_report(installs))
    if candidates:
        print(cand_mod.candidate_report(candidates))

    cfg = run_mod.RunConfig(
        results_dir=results_dir,
        installs=installs,
        candidates=candidates,
        timeout=args.timeout,
        suites=suites,
        oracle_keys=tuple(installs),
        candidate_keys=tuple(candidates),
        include_reference_labels=(not args.no_reference_labels),
    )
    runner = run_mod.Runner(cfg)

    notes: list[str] = []
    notes.append(
        "Suite counts are per (install x fixture), so the same fixture set "
        "appears once per install exercised. `folder/oracle = 2` is ONE folder "
        "fixture pair run on TWO installs -- it is not two folder fixtures. "
        "`labels/oracle = 30` is the 30 layouts re-run on the reference install "
        "solely to corroborate the Chinese->English label table.")
    if len(installs) > 1:
        notes.append(
            "Two installs were exercised. Their numbers are reported separately "
            "in `by_version_and_subject` and are never summed into one figure.")
    for key, inst in installs.items():
        if not inst.enabled:
            notes.append(f"install `{key}` disabled: {inst.disabled_reason}")
            continue
        if inst.locale == "zh":
            notes.append(
                f"install `{key}` is a Chinese-localized repack; report labels are "
                f"Chinese and are mapped to English by normalizer rule-set "
                f"{norm_mod.RULESET_VERSION}. Only observed label pairs are mapped.")
        try:
            if "anchor" in suites:
                runner.run_anchors(key)
            if "layout" in suites:
                runner.run_layouts(key)
            if "table" in suites:
                runner.run_tables(key)
            if "hex" in suites:
                runner.run_hexes(key)
            if "pic" in suites:
                runner.run_pics(key)
            if "reg" in suites:
                runner.run_regs(key)
            if "ver" in suites:
                runner.run_vers(key)
            if "folder" in suites:
                runner.run_folder(key)
            if "labels" in suites and key == "current":
                runner.run_reference_corroboration()
        except Exception as exc:                      # licensing etc. -> stop this install
            notes.append(f"install `{key}` aborted: {type(exc).__name__}: {exc}")
            print(f"!! install `{key}` aborted: {type(exc).__name__}: {exc}")

    for ck in cfg.candidate_keys:
        c = candidates[ck]
        if not c.available:
            notes.append(f"candidate `{ck}` not available at `{c.path}`; "
                         f"its cases are recorded as not_run.")
            continue
        if not c.is_product:
            notes.append(
                f"candidate `{ck}` is the OLD PROTOTYPE (`{c.path}`), not the "
                f"product. Its numbers describe the prototype only.")
        if c.report_on_stdout:
            notes.append(f"candidate `{ck}` emits its report on stdout; the harness "
                         f"captures it to the raw-report path for audit.")
        if c.text_script_unsupported:
            notes.append(f"candidate `{ck}` does not implement the BC text-report "
                         f"script interface; the adapter calls its own CLI, so the "
                         f"comparison is candidate-CLI-vs-golden, not "
                         f"script-vs-script.")
        if c.folder_unsupported:
            notes.append(f"candidate `{ck}` has no folder comparison; folder "
                         f"coverage for it is out of scope for this task.")
        try:
            if "anchor" in suites:
                runner.run_candidate_anchors(ck)
            if "layout" in suites:
                runner.run_candidate_layouts(ck)
            if "table" in suites:
                runner.run_candidate_tables(ck)
            if "hex" in suites:
                runner.run_candidate_hexes(ck)
            if "pic" in suites:
                runner.run_candidate_pics(ck)
            if "reg" in suites:
                runner.run_candidate_regs(ck)
            if "ver" in suites:
                runner.run_candidate_vers(ck)
        except Exception as exc:
            notes.append(f"candidate `{ck}` aborted: {type(exc).__name__}: {exc}")
            print(f"!! candidate `{ck}` aborted: {type(exc).__name__}: {exc}")

    # Mark documented known differences on the affected candidate results.
    for r in runner.results:
        if r.test_id in rep_mod.KNOWN_DIFFERENCES and r.verdict.value == "fail":
            r.known_difference = rep_mod.KNOWN_DIFFERENCES[r.test_id]

    finished = datetime.now(timezone.utc)

    commands = {
        "identity only (no Oracle calls)":
            "cd D:\\Rea\\product\\verify && python -m harness.run_cli --identity-only",
        "this run":
            "cd D:\\Rea\\product\\verify && " + _reproduce_cmd(args),
        "unit tests (harness suite)":
            "cd D:\\Rea && python -m pytest product/verify/tests -q -p no:cacheprovider",
        "from the repo root without cd":
            "cd D:\\Rea && python -c \"import sys; sys.path.insert(0,r'D:\\Rea\\product\\verify'); "
            "from harness import run_cli; raise SystemExit(run_cli.main(['--install','current']))\"",
    }
    payload = rep_mod.build_payload(
        started=started, finished=finished,
        harness_version=HARNESS_VERSION, ruleset_version=norm_mod.RULESET_VERSION,
        installs={k: v.to_json() for k, v in installs.items()},
        candidates={k: v.to_json() for k, v in candidates.items()},
        results=runner.results, notes=notes, commands=commands,
        results_dir=str(results_dir),
    )
    rep_mod.write_json(payload, results_dir / "report.json")
    rep_mod.write_markdown(payload, results_dir / "REPORT.md")
    inst_mod.write_identity(installs, results_dir / "install-identity.json")

    t = payload["totals"]
    print()
    print("=" * 78)
    print(f"TOTAL {t['total']}  pass={t['pass']}  fail={t['fail']}  "
          f"error={t['error']}  missing_output={t['missing_output']}  "
          f"timeout={t['timeout']}  unparseable={t['unparseable']}  "
          f"not_run={t['not_run']}")
    for k, s in payload["by_suite_subject"].items():
        print(f"  {k:<22} total={s['total']:<4} pass={s['pass']:<4} fail={s['fail']:<4} "
              f"error={s['error']:<4} other={s['missing_output'] + s['timeout'] + s['unparseable'] + s['not_run']}")
    print(f"report: {results_dir / 'REPORT.md'}")
    print(f"json  : {results_dir / 'report.json'}")
    print("=" * 78)

    if not args.json_only:
        for f in payload["non_pass"]:
            print(f"  NON-PASS {f['verdict']:<14} {f['test_id']:<28} {f['detail'][:110]}")

    # Exit code: non-zero when anything executed but did not pass, so CI and the
    # project lead's own re-run can gate on it.  not_run alone does not fail.
    hard = (t["fail"] + t["error"] + t["missing_output"] + t["timeout"]
            + t["unparseable"])
    return 1 if hard else 0


def _reproduce_cmd(args) -> str:
    parts = ["python -m harness.run_cli"]
    for k in (args.install or ["current"]):
        parts.append(f"--install {k}")
    for k in (args.candidate or []):
        parts.append(f"--candidate {k}")
    for s in (args.suite or []):
        parts.append(f"--suite {s}")
    if args.run_name:
        parts.append(f"--run-name {args.run_name}")
    return " ".join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
