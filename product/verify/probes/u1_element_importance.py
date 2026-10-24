#!/usr/bin/env python3
"""U1 probe -- which token classes make a changed line IMPORTANT (task A-4).

The audit's last I-level core claim (`product/docs/02-version-and-evidence.md`
§4.2, U1: "syntax element index 6/9 = Directive/Operator forced important")
names an internal element index that no CLI observation can see directly.
What the CLI *can* observe is the behaviour that claim exists to predict: for
each token class, is a line that differs ONLY in that class judged

    different   (important -- survives options:ignore-unimportant)
    similar     (unimportant -- folded to same by ignore-unimportant)

Method: minimal single-line C pairs (syntax-aware format, one pair per token
class), run through the live Oracle as ``text-report layout:xml`` in two
modes (default, ``options:ignore-unimportant``).  Every Oracle call goes
through ``harness.oracle`` (in-place cwd, Job Object, timeout) -- the A-1
machinery.  Raw outputs land in ``product/verify/runs/u1-probe-<ts>/``; the
interpreted table is printed and written to ``U1-FINDINGS.md`` next to this
script.  The script owns nothing else and regenerates its fixtures each run.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u1_element_importance.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

#: (probe name, left line, right line) -- .c files, so BC applies the C/C++
#: format's tokenizer.  One token class differs per pair.
PAIRS = [
    ("directive-include", "#include <stdio.h>", "#include <stdlib.h>"),
    ("operator", "int s = a + b;", "int s = a - b;"),
    ("identifier", "int alpha1;", "int alpha2;"),
    ("number", "int x = 10;", "int x = 20;"),
    ("string", 'char *m = "abc";', 'char *m = "abd";'),
    ("keyword", "unsigned int x;", "signed int x;"),
    ("comment", "// alpha", "// beta"),
    ("case-identifier", "int Alpha;", "int alpha;"),
    ("whitespace-internal", "int  x;", "int x;"),
    ("whitespace-trailing", "int x;   ", "int x;"),
    ("control-identical", "int same;", "int same;"),
]

MODES = [None, "ignore-unimportant"]

STATUS_RE = re.compile(r'<linecomp status="([a-z]+)"')


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u1-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")
    print(f"run dir: {run_dir}\n")

    records = []
    for name, left_line, right_line in PAIRS:
        left = run_dir / "fixtures" / f"{name}-L.c"
        right = run_dir / "fixtures" / f"{name}-R.c"
        left.write_text(left_line + "\n", encoding="utf-8")
        right.write_text(right_line + "\n", encoding="utf-8")
        for mode in MODES:
            tag = name if mode is None else f"{name}+iu"
            out = run_dir / "reports" / f"{tag}.xml"
            script = orc.write_script(
                run_dir / "reports" / f"{tag}.bcs",
                [orc.text_script("xml", mode)])
            run = orc.run(cur.oracle_path, script, left, right, out,
                          timeout=120.0, script_text=orc.text_script("xml", mode))
            statuses = []
            if run.report_exists:
                statuses = STATUS_RE.findall(
                    out.read_bytes().decode("utf-8-sig", errors="replace"))
            records.append({
                "probe": name, "mode": mode or "default", "tag": tag,
                "left": left_line, "right": right_line,
                "exit": run.exit_code, "statuses": statuses,
                "containment": run.containment,
            })
            print(f"  {tag:<28} exit={run.exit_code} statuses={statuses}")

    # ---- interpret ----
    by_probe: dict[str, dict[str, list[str]]] = {}
    for r in records:
        by_probe.setdefault(r["probe"], {})[r["mode"]] = r["statuses"]

    print("\n=== U1 observed importance table (.c, live Oracle) ===")
    print(f"{'token class':<20} {'default':<12} {'ignore-unimportant':<20} verdict")
    for name, _, _ in PAIRS:
        d = by_probe[name].get("default", [])
        iu = by_probe[name].get("ignore-unimportant", [])
        ds = ",".join(d) or "(none)"
        is_ = ",".join(iu) or "(none)"
        if "different" in iu:
            verdict = "IMPORTANT (survives ignore-unimportant)"
        elif iu and all(s == "same" for s in iu) and d and "similar" in d:
            verdict = "unimportant (folded to same)"
        elif d and "different" in d:
            verdict = "IMPORTANT (already different by default)"
        elif d and "similar" in d:
            verdict = "unimportant (similar by default)"
        else:
            verdict = "no line difference observed"
        print(f"{name:<20} {ds:<12} {is_:<20} {verdict}")

    (run_dir / "u1-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw results: {run_dir / 'u1-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
