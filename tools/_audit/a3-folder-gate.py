#!/usr/bin/env python3
"""Serial live-Oracle gate for task A-3's folder fixture corpus.

Run by the project lead ONLY, and only when no other BCompare consumer is
active (single live-Oracle user rule). Every Oracle call goes through
``product/verify``'s ``harness.oracle`` -- the measured machinery from task
A-1: the Oracle always runs in place inside its install directory, inside a
Job Object, with a per-call timeout.

Per case in ``product/dir/fixtures/cases.json``:

* rejection cases (``expected_error`` set)
    run the Oracle script and record BC's own exit code next to the engine's
    committed expectation.  ``content`` / ``binary-content`` are OBSERVED to
    exit 106 (audit, 00-current-state.md §6) -- disagreement there is a gate
    failure.  Not-probed criteria (``version`` ...) are informational: what
    BC actually does upgrades those unknowns to observed evidence.
* ``layout:xml`` cases
    run the Oracle and compare against the engine's report at two levels:
    byte-identical (after removing the volatile ``created="..."``) and
    status-sequence equal.  Byte-identical is the target; status-equal with
    formatting differences is recorded as a partial, never silently passed.
* every other layout
    run the Oracle and ARCHIVE BC's output as newly observed evidence (BC's
    text folder layouts were unknown -- dir EVIDENCE.md U-M3-12).  No byte
    verdict is claimed for them.

Nothing is written next to the read-only fixtures: all outputs land in
``product/verify/runs/<run-name>/`` (``scripts/``, ``oracle/``, ``engine/``,
``gate-results.json``, ``REPORT.md``).

Usage:
    cd D:\\Rea\\product\\dir
    python D:\\Rea\\tools\\_audit\\a3-folder-gate.py [run-name]
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
sys.path.insert(0, str(REA / "product" / "dir" / "tools"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402
import compare_fixtures as cf  # noqa: E402

CREATED_RE = re.compile(rb' created="[^"]*"')
STATUS_RE = re.compile(rb'<(?:filecomp|foldercomp) status="([a-z]+)"')

#: Observed O-level anchor: these criteria make BC exit 106.
OBSERVED_REJECT_106 = {"content", "binary-content"}

#: Criteria the live Oracle ACCEPTS although the engine refuses them as
#: not-probed (FINDINGS F4). A rejection case for one of these is a documented
#: divergence, not a gate failure.
BC_ACCEPTS_DESPITE_ENGINE_REFUSAL = {
    "version", "owner", "group", "permissions", "ignore-unimportant",
}


def norm_created(b: bytes) -> bytes:
    return CREATED_RE.sub(b"", b)


def status_seq(b: bytes) -> list[str]:
    return [m.decode("ascii") for m in STATUS_RE.findall(b)]


def report_rows(b: bytes) -> list[tuple[str, str, str]]:
    """(kind, name path, status) for every row, in document order.

    Order-sensitive on purpose: the engine must reproduce the Oracle's row
    order (the gate's first run caught a whole class of divergence through it
    — the natural/collation sort).
    """
    import xml.etree.ElementTree as ET

    root = ET.fromstring(b.decode("utf-8-sig"))
    out: list[tuple[str, str, str]] = []

    def walk(el, prefix: str) -> None:
        for fc in el:
            if fc.tag == "foldercomp":
                lp = fc.findtext("ltpath") or ""
                name = lp.split("\\")[-1] if lp else "?"
                walk(fc, prefix + name + "/")
            elif fc.tag == "filecomp":
                lt, rt = fc.find("lt"), fc.find("rt")
                nm = (lt.findtext("name") if lt is not None else None) or (
                    rt.findtext("name") if rt is not None else "?")
                out.append(("file", prefix + nm, fc.get("status") or "?"))

    walk(root, "")
    return out


def first_diff(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n


def bc_script_lines(case: dict, left: str, right: str) -> tuple[list[str], str]:
    """The OBSERVED Oracle recipe, extended with the audit-proven criteria line.

    ``criteria <x>`` comes BEFORE ``load`` -- the form the audit's
    ``probe-dir-criteria.py`` measured against the live install. A case that
    exercises the CLI-flag form of an option (``extra.cli_flag``) contributes
    its equivalent criteria token, because the Oracle only knows the token
    form. Returns (script lines, effective criteria string).
    """
    crit = case["criteria"].strip()
    cli_flag = (case.get("extra") or {}).get("cli_flag")
    if cli_flag and cli_flag.startswith("--"):
        token = cli_flag[2:]
        if token and token not in crit.split():
            crit = f"{crit} {token}".strip()
    lines = []
    if crit:
        lines.append(f"criteria {crit}")
    lines += [
        f'load "{left}" "{right}"',
        "expand all",
        f'folder-report layout:{case["layout"]} output-to:"%3"',
    ]
    return lines, crit


def run_engine(case: dict, left: str, right: str, gate: pathlib.Path):
    """Run the A-3 engine once on this case; capture raw stdout bytes."""
    argv = [
        str(cf.BINARY),
        "--criteria", case["criteria"],
        "--layout", case["layout"],
        "--tz-offset", cf.TZ_OFFSET,
        "--print-exit-code",
    ]
    cli_flag = (case.get("extra") or {}).get("cli_flag")
    if cli_flag:
        argv.append(cli_flag)
    argv += [left, right]
    proc = subprocess.run(argv, capture_output=True)  # bytes: no newline translation
    out = gate / "engine" / f"{case['id']}.out"
    out.write_bytes(proc.stdout)
    err = proc.stderr.decode("utf-8", errors="replace").strip()
    return proc.returncode, err, out


def main() -> int:
    run_name = (sys.argv[1] if len(sys.argv) > 1 else
                datetime.now(timezone.utc).strftime("A3-folder-gate-%Y%m%dT%H%M%SZ"))
    gate = REA / "product" / "verify" / "runs" / run_name
    for sub in ("scripts", "oracle", "engine"):
        (gate / sub).mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    bcomp = cur.oracle_path
    print(f"oracle : {bcomp}  ({cur.oracle_version}, locale={cur.locale})")
    print(f"run dir: {gate}")

    manifest = json.loads((cf.FIXTURES / "cases.json").read_text(encoding="utf-8"))
    cases = manifest["cases"]
    print(f"cases  : {len(cases)}\n")

    # Step 0 -- corpus freshness + engine vs its own committed expectations.
    print("== step 0: engine self-check (compare_fixtures.py, no Oracle) ==")
    proc = subprocess.run(
        [sys.executable, "tools/compare_fixtures.py",
         "--json", str(gate / "engine-selfcheck.json")],
        cwd=str(cf.DIR_CRATE), capture_output=True, text=True,
    )
    tail = "\n".join(proc.stdout.strip().splitlines()[-4:])
    print(tail)
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
        raise SystemExit("engine self-check FAILED; aborting the gate")
    print()

    results = []
    for case in cases:
        cid = case["id"]
        left, right, _ = cf.paths_for(case["pair"])
        lines, bc_crit = bc_script_lines(case, left, right)
        script = orc.write_script(gate / "scripts" / f"{cid}.bcs", lines)
        out = gate / "oracle" / f"{cid}.out"
        run = orc.run(bcomp, script, left, right, out,
                      timeout=180.0, script_text="\n".join(lines))

        rec = {
            "id": cid, "pair": case["pair"], "criteria": case["criteria"],
            "bc_criteria": bc_crit,
            "layout": case["layout"], "evidence": case["evidence"],
            "expected_exit": case["expected_exit"],
            "expected_error": case["expected_error"],
            "bc_exit": run.exit_code, "bc_report_bytes": run.report_bytes,
            "containment": run.containment, "tree_killed": run.tree_killed,
            "timed_out": run.timed_out, "elapsed_s": run.elapsed_s,
            "class": None, "byte_identical": None, "rows_equal": None,
            "agree": None, "note": "",
        }

        if case["expected_error"] is not None:
            rec["class"] = "rejection"
            crit_stripped = case["criteria"].strip()
            if crit_stripped in BC_ACCEPTS_DESPITE_ENGINE_REFUSAL:
                # FINDINGS F4: BC accepts these; the engine's not-probed
                # refusal is a documented divergence pending implementation.
                rec["agree"] = None
                rec["note"] = (
                    f"documented divergence: BC accepts {crit_stripped!r} "
                    f"(exit {run.exit_code}, {run.report_bytes}B report) while "
                    "the engine refuses it as not-probed")
            else:
                rec["agree"] = run.exit_code == case["expected_exit"]
                hard = (crit_stripped in OBSERVED_REJECT_106
                        and case["evidence"] == "observed")
                rec["hard"] = hard
                if not rec["agree"]:
                    rec["note"] = (f"BC exit {run.exit_code} vs engine expectation "
                                   f"{case['expected_exit']}")
                    if run.report_bytes:
                        rec["note"] += f"; BC still produced a {run.report_bytes}-byte report"
        elif case["layout"] == "xml":
            rec["class"] = "xml-parity"
            eng_exit, eng_err, eng_path = run_engine(case, left, right, gate)
            rec["engine_exit"] = eng_exit
            bc_b = out.read_bytes() if out.exists() else b""
            eng_b = eng_path.read_bytes() if eng_path.exists() else b""
            rec["engine_report_bytes"] = len(eng_b)
            rec["byte_identical"] = bool(bc_b) and bool(eng_b) and norm_created(bc_b) == norm_created(eng_b)
            try:
                bc_rows = report_rows(bc_b) if bc_b else None
                eng_rows = report_rows(eng_b) if eng_b else None
            except Exception as exc:  # noqa: BLE001 - record, don't crash the gate
                bc_rows = eng_rows = None
                rec["note"] = f"row parse failed: {exc}"
            rec["rows_equal"] = bool(bc_rows) and bc_rows == eng_rows
            if rec["byte_identical"]:
                rec["agree"] = True
            elif rec["rows_equal"]:
                rec["agree"] = None
                pos = first_diff(norm_created(bc_b), norm_created(eng_b))
                rec["note"] = (f"rows equal but bytes differ at offset {pos}; "
                               f"bc={len(bc_b)}B engine={len(eng_b)}B")
            elif bc_rows is not None and eng_rows is not None:
                rec["agree"] = False
                bc_only = [r for r in bc_rows if r not in eng_rows][:4]
                eng_only = [r for r in eng_rows if r not in bc_rows][:4]
                rec["note"] = (f"rows differ: bc-only={bc_only} engine-only={eng_only}")
            else:
                rec["agree"] = False
                rec["note"] = "a report could not be parsed into rows"
        else:
            rec["class"] = "layout-evidence"
            rec["agree"] = None
            if run.exit_code != 0:
                rec["note"] = (f"BC exit {run.exit_code} for layout "
                               f"{case['layout']!r} ({orc.exit_meaning(run.exit_code)})")
            else:
                rec["note"] = f"BC produced a {run.report_bytes}-byte report; archived"

        tag = {True: "PASS", False: "FAIL", None: "info"}[rec["agree"]]
        hard_tag = " [HARD]" if rec.get("hard") and not rec["agree"] else ""
        print(f"  {tag:<4} {rec['class']:<15} {cid:<34} "
              f"bc_exit={run.exit_code:<4} {rec['note']}{hard_tag}")
        results.append(rec)

    hard_fail = [r for r in results if r["agree"] is False and r.get("hard")]
    hard_fail += [r for r in results if r["class"] == "xml-parity" and r["agree"] is False]
    n_pass = sum(1 for r in results if r["agree"] is True)
    n_info = sum(1 for r in results if r["agree"] is None)
    n_fail = sum(1 for r in results if r["agree"] is False)

    (gate / "gate-results.json").write_text(
        json.dumps({"run": run_name, "oracle": bcomp, "oracle_version": cur.oracle_version,
                    "results": results}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print("\n" + "=" * 78)
    print(f"TOTAL {len(results)}  pass={n_pass}  info={n_info}  fail={n_fail}")
    for r in hard_fail:
        print(f"  HARD-FAIL {r['id']}: {r['note']}")
    print(f"results: {gate / 'gate-results.json'}")
    print("=" * 78)
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
