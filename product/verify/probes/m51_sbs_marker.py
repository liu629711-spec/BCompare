#!/usr/bin/env python3
"""M5.1 probe -- which rule draws the side-by-side gutter marker?

`mixed-side-by-side` is the official gate's one red item. BC's golden renders

    case diff   <> CASE DIFF      <- first row of the changed block: marked
    real diff 1    real diff 9    <- second row: field blanked
    real diff 2                   <- third row (left orphan): field blanked

while `orphans-side-by-side` (`only-left +-`) and `similar-side-by-side`
(`alpha <> ALPHA`) mark their single-row blocks. Two rules fit all five golden
reports, and the corpus cannot tell them apart:

  H1  the marker is drawn on the FIRST row of every block (same or not);
      later rows of the block get a blank field (what `identical-side-by-side`
      already shows for repeated `same` rows, and the product implements only
      for `same` blocks)
  H2  the marker is blanked on a non-first row only when the left cell fills
      the column ("real diff 1" is exactly the column width)

This probe builds shapes where the two rules diverge:

  short-nonfirst-diff   a/bbbb/xx/c vs a/X/Y/c   row 2 is a pair, short left
  short-nonfirst-same   aaaa/x/y/z vs itself      rows 2-4 same, short left
  orphan-second-short   a/bbbb/o1/c vs a/X/c      row 2 is a left orphan, short
  rtonly-second         a/bbbb/c vs a/X/yy/c      row 2 is a right orphan
  orphan-first-then-pair aaaa/bbbb/xy/c vs aaaa/X/Y/c
                        block starts with a filling orphan, then a short pair
  mixed                 the recorded golden shape, as the harness control

H1 predicts blank fields on every non-first row; H2 predicts markers wherever
the left cell is short. Single-row blocks are the control: both rules mark.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/m51_sbs_marker.py
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

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

#: name -> (left lines, right lines, purpose)
SHAPES: dict[str, tuple[list[str], list[str], str]] = {
    "short-nonfirst-diff": (["a", "bbbb", "xx", "c"], ["a", "X", "Y", "c"],
                            "pair on a non-first row with a short left cell"),
    "short-nonfirst-same": (["aaaa", "x", "y", "z"], ["aaaa", "x", "y", "z"],
                            "same rows 2-4 with short left cells"),
    "orphan-second-short": (["a", "bbbb", "o1", "c"], ["a", "X", "c"],
                            "left orphan on a non-first row, short left cell"),
    "rtonly-second": (["a", "bbbb", "c"], ["a", "X", "yy", "c"],
                      "right orphan on a non-first row (left cell empty)"),
    "orphan-first-then-pair": (["aaaa", "bbbb", "xy", "c"], ["aaaa", "X", "Y", "c"],
                               "block starts with a filling orphan, then a short pair"),
    "mixed": (["same line", "case diff", "real diff 1", "real diff 2", "tail"],
              ["same line", "CASE DIFF", "real diff 9", "tail"],
              "the recorded golden shape, as control"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m51-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print("purpose : which rule draws the side-by-side gutter marker?\n")

    records: list[dict] = []
    for tag, (ll, rl, purpose) in SHAPES.items():
        lp, rp = fx / f"{tag}-L.txt", fx / f"{tag}-R.txt"
        lp.write_text("\n".join(ll) + "\n", encoding="utf-8", newline="")
        rp.write_text("\n".join(rl) + "\n", encoding="utf-8", newline="")

        lines = ['text-report layout:side-by-side output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        o_out = run_dir / "reports" / f"{tag}.oracle.txt"
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = ""
        if run.report_exists and run.report_bytes:
            o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        p_out = run_dir / "reports" / f"{tag}.product.txt"
        proc = subprocess.run(
            [str(PRODUCT), str(lp), str(rp), str(p_out), "--layout=side-by-side"],
            capture_output=True, timeout=120)
        p_body = ""
        if p_out.exists():
            p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

        def body_rows(body: str) -> list[str]:
            """Content rows (no header, no separators), right-trimmed.

            The header is skipped structurally -- everything before the first
            separator line -- because the localized Oracle emits Chinese
            header labels (文本比较(T) etc.) that no label list can keep up
            with.
            """
            lines = body.replace("\r\n", "\n").split("\n")
            start = 0
            for i, line in enumerate(lines):
                if line and set(line) <= {"-"}:
                    start = i + 1
                    break
            rows = []
            for line in lines[start:]:
                if not line or set(line) <= {"-"}:
                    continue
                rows.append(line.rstrip())
            return rows

        o_rows, p_rows = body_rows(o_body), body_rows(p_body)
        same = o_rows == p_rows
        records.append({"tag": tag, "purpose": purpose, "same": same,
                        "oracle_rows": o_rows, "product_rows": p_rows,
                        "oracle_exit": run.exit_code,
                        "product_exit": proc.returncode,
                        "oracle_body": o_body, "product_body": p_body})
        mark = "OK  " if same else "DIFF"
        print(f"  {mark} {tag:<24} {purpose}")
        for r in o_rows:
            print(f"       oracle : {r!r}")
        if not same:
            for r in p_rows:
                print(f"       product: {r!r}")

    (run_dir / "m51-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'm51-results.json'}")

    agree = sum(1 for r in records if r["same"])
    print(f"\n{agree}/{len(records)} shapes agree")
    m = {r["tag"]: r for r in records}
    print("\n=== reading ===")
    diverging = [t for t in ("short-nonfirst-diff", "orphan-second-short",
                             "rtonly-second", "orphan-first-then-pair")
                 if t in m and not m[t]["same"]]
    if not diverging:
        print("  Every non-first row is blanked -> H1 (first row of each block"
              " carries the marker) is the rule; H2 refuted.")
    else:
        print(f"  Diverging on {diverging} -> the marker rule needs a finer"
              " model; inspect the raw rows above.")
    if "short-nonfirst-same" in m:
        print("  short-nonfirst-same control: product already blanks repeated"
              " same rows; oracle agreement confirms the position-based rule.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
