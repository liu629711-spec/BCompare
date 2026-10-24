#!/usr/bin/env python3
"""U6 probe -- the /qc rules mapping for one-sided and folded lines.

The M4 gate exposed that the product's `/qc` mapping was too strict: it treated
"every group is literally `same`" as the only way to reach code 12, but the
Oracle returns 12 for a pair whose only difference is an unimportant one — the
report path calls those groups `similar`, not `same`.  That much is settled by
the six cells already measured in u5b/u5k.

What is NOT settled is where the boundary sits for the three statuses the
report path can also produce:

  * a `leftsimilar` / `rightsimilar` row (a one-sided line whose content is
    entirely unimportant — see U2-FINDINGS)
  * a `leftorphan` / `rightorphan` row (a one-sided line with real content)
  * an extra **blank** line on one side

Each of those could plausibly be "similar" (12) or "rules-based differences"
(13), and the choice changes the product's exit code for a whole class of
inputs.  This probe measures them.

Control cells are included so the probe is self-checking: a pair with an
important in-line change must be 13, and a pair that differs only in trailing
whitespace must be 12 (both already measured; if they moved, something is wrong
with the probe's fixtures rather than with the model).

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u6_qc_orphans.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

#: The Oracle is invoked exactly as in u5b: bare argv, /silent, inside the job
#: object.  ``/qc`` needs no script, so ``oracle.run`` (which hard-codes the
#: script recipe) is not usable here.
def run_qc(oracle: pathlib.Path, kind: str | None,
           left: pathlib.Path, right: pathlib.Path) -> int:
    flag = f"/qc={kind}" if kind else "/qc"
    cmd = [str(oracle), "/silent", flag, str(left), str(right)]
    with orc.ProcessTree() as tree:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(oracle.parent),
            creationflags=orc._CREATE_SUSPENDED if tree.enabled else 0,
        )
        tree.assign(proc)
        if tree.enabled:
            orc._resume(proc)
        try:
            proc.communicate(timeout=120)
            return proc.returncode
        except subprocess.TimeoutExpired:
            tree.kill_tree()
            proc.kill()
            try:
                proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            return -1


PAIRS: dict[str, tuple[str, str]] = {
    # ---- controls (already measured; they must not move) ----------------
    "control-identical":        ("x = 1\n", "x = 1\n"),
    "control-trailing-ws":      ("x = 1   \n", "x = 1\n"),
    "control-important-change": ("x = 1\n", "x = 2\n"),
    "control-comment-change":   ("x = 1  # one\n", "x = 1  # two\n"),
    # ---- one-sided COMMENT lines (entirely unimportant content) --------
    "extra-comment-left":       ("// note\nint a;\n", "int a;\n"),
    "extra-comment-right":      ("int a;\n", "// note\nint a;\n"),
    "extra-comment-both":       ("int a;\n// L\n", "// R\nint a;\n"),
    # ---- one-sided IMPORTANT lines -------------------------------------
    "extra-code-left":          ("int b;\nint a;\n", "int a;\n"),
    "extra-code-right":         ("int a;\n", "int b;\nint a;\n"),
    # ---- one-sided BLANK lines -----------------------------------------
    "extra-blank-left":         ("int a;\n\nint b;\n", "int a;\nint b;\n"),
    "extra-blank-right":        ("int a;\nint b;\n", "int a;\n\nint b;\n"),
    # ---- mixed: an unimportant extra line AND an important change -------
    "mixed-comment-and-code":   ("// note\nint a;\n", "int a;\nint b;\n"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u6-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records: list[dict] = []
    for name, (lb, rb) in PAIRS.items():
        # A `.c` extension for the code/comment pairs so the C grammar applies;
        # the whitespace controls work in any grammar.
        ext = "c" if "code" in name or "comment" in name or "blank" in name else "txt"
        lp = fx / f"{name}-L.{ext}"
        rp = fx / f"{name}-R.{ext}"
        lp.write_bytes(lb.encode())
        rp.write_bytes(rb.encode())

        qc = run_qc(pathlib.Path(inst.oracle_path), None, lp, rp)
        # The report path for the same pair, so the /qc code can be read against
        # the statuses the report actually emits.
        out = run_dir / "reports" / f"{name}.xml"
        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{name}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = out.read_bytes().decode("utf-8-sig", errors="replace")
        import re
        statuses = re.findall(r'<linecomp status="([a-z]+)"', body)

        records.append({"tag": name, "ext": ext, "left": lb, "right": rb,
                        "qc_rules_exit": qc, "report_statuses": statuses,
                        "report_bytes": run.report_bytes})
        print(f"  {name:<26} /qc={qc:<3} report={statuses}")

    (run_dir / "u6-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u6-results.json'}")

    # ---- the model the probe is testing ---------------------------------
    print("\nmodel check: code 12 iff every group is same/similar/one-sided-"
          "unimportant; 13 iff any important difference")
    for r in records:
        st = r["report_statuses"]
        unimportant = {"same", "similar", "leftsimilar", "rightsimilar"}
        predict12 = bool(st) and all(s in unimportant for s in st)
        predicted = 12 if predict12 else 13
        mark = "ok " if predicted == r["qc_rules_exit"] else "MISMATCH"
        print(f"  {mark} {r['tag']:<26} predicted={predicted} "
              f"observed={r['qc_rules_exit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
