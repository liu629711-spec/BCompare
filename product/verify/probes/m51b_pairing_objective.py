#!/usr/bin/env python3
"""M5.1b probe -- the closeness pairing objective and all-tie geometry.

Round 1 (`m51_sbs_marker.py`) found that on unequal all-zero blocks BC pairs
the LAST left line for L-heavy sections (`o1` with `X`) but the FIRST right
line for R-heavy ones (`bbbb` with `X`). It also showed BC preferring a
count-2 identity zip over the product's score-1 single pair on
`short-nonfirst-diff`, which refutes case-insensitive closeness scores
regardless of objective order. Open questions this round settles, via XML
`ltid`/`rtid` pairings (the raw truth, no rendering involved):

  Q1 objective order -- `score-vs-count`: L=[a,zz,abc,c] R=[a,abcX,qq,c].
     The abc/abcX pair scores 3 with 1 pair; the zip scores 0 with 2 pairs.
     (score,count) picks the pair; (count,score) picks the zip.
  Q2 all-tie geometry -- 2v1/1v2 reruns plus 3v1/1v3/3v2/2v3/2v2 and a
     duplicate-content 2v1. If BC zips from the bottom when |L|>|R| and from
     the top when |R|>|L|, that pins the tie rule; anything else means the
     linear-Myers decomposition drives the pairing and needs pseudocode.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m51b_pairing_objective.py
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

#: name -> (left lines, right lines, purpose). All plain .txt with `a`/`c`
#: anchors so the middle is one clean section.
SHAPES: dict[str, tuple[list[str], list[str], str]] = {
    "tie-2v1": (["a", "bbbb", "o1", "c"], ["a", "X", "c"],
                "round-1 rerun: which left line pairs the single right?"),
    "tie-1v2": (["a", "bbbb", "c"], ["a", "X", "yy", "c"],
                "round-1 rerun: which right line pairs the single left?"),
    "tie-3v1": (["a", "p", "q", "r", "c"], ["a", "X", "c"],
                "3 left vs 1 right, all zero"),
    "tie-1v3": (["a", "X", "c"], ["a", "p", "q", "r", "c"],
                "1 left vs 3 right, all zero"),
    "tie-3v2": (["a", "p", "q", "r", "c"], ["a", "X", "Y", "c"],
                "3 left vs 2 right, all zero"),
    "tie-2v3": (["a", "p", "q", "c"], ["a", "X", "Y", "Z", "c"],
                "2 left vs 3 right, all zero"),
    "tie-2v2": (["a", "p", "q", "c"], ["a", "X", "Y", "c"],
                "2 vs 2 control: identity zip expected"),
    "tie-dup": (["a", "dup", "dup", "c"], ["a", "X", "c"],
                "2v1 with duplicate content: first or second `dup`?"),
    "score-vs-count": (["a", "zz", "abc", "c"], ["a", "abcX", "qq", "c"],
                       "abc/abcX scores 3 with 1 pair vs zip 0 with 2 pairs"),
    "cs-check": (["a", "bbbb", "xx", "c"], ["a", "X", "Y", "c"],
                 "round-1 short-nonfirst-diff via XML: zip confirms case-sensitive scores"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m51b-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print("purpose : closeness objective order + all-tie pairing geometry\n")

    records: list[dict] = []
    for tag, (ll, rl, purpose) in SHAPES.items():
        lp, rp = fx / f"{tag}-L.txt", fx / f"{tag}-R.txt"
        lp.write_text("\n".join(ll) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(rl) + "\n", encoding="utf-8", newline="")

        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace") \
            if run.report_exists and run.report_bytes else ""

        p_out = run_dir / "reports" / f"{tag}.product.xml"
        subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)],
                       capture_output=True, timeout=120)
        p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace") \
            if p_out.exists() else ""

        def pairing(body: str) -> list[tuple[str, str, str]]:
            """(status, ltid, rtid) per linecomp; ids are 1-based file lines."""
            out = []
            for m in re.finditer(r'<linecomp status="(\w+)">(.*?)</linecomp>',
                                 body, re.S):
                lt = re.search(r'ltid="(-?\d+)"', m.group(2))
                rt = re.search(r'rtid="(-?\d+)"', m.group(2))
                out.append((m.group(1),
                            lt.group(1) if lt else "-",
                            rt.group(1) if rt else "-"))
            return out

        o_p, p_p = pairing(o_body), pairing(p_body)
        same = o_p == p_p
        records.append({"tag": tag, "purpose": purpose, "same": same,
                        "oracle": o_p, "product": p_p,
                        "oracle_exit": run.exit_code,
                        "oracle_body": o_body, "product_body": p_body})
        mark = "OK  " if same else "DIFF"
        print(f"  {mark} {tag:<15} {purpose}")
        print(f"       oracle : {o_p}")
        if not same:
            print(f"       product: {p_p}")

    (run_dir / "m51b-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'm51b-results.json'}")

    by = {r["tag"]: r for r in records}
    print("\n=== reading ===")
    svc = by.get("score-vs-count")
    if svc:
        paired = [x for x in svc["oracle"] if x[0] in ("different", "similar")]
        if len(paired) == 3:
            print("  Q1: BC kept the zip (2 pairs, score 0) -> objective is"
                  " (COUNT, score); the 3-score pair lost to count.")
        elif len(paired) == 2 and any(x[1] == "3" for x in paired):
            print("  Q1: BC took the abc/abcX pair (1 pair, score 3) ->"
                  " objective is (score, COUNT); count never beats score.")
        else:
            print(f"  Q1: unrecognised pairing {svc['oracle']} -- inspect raw.")
    ties = [t for t in ("tie-2v1", "tie-1v2", "tie-3v1", "tie-1v3",
                        "tie-3v2", "tie-2v3", "tie-dup") if t in by]
    for t in ties:
        print(f"  Q2 {t}: {by[t]['oracle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
