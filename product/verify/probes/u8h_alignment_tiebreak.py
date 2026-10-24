#!/usr/bin/env python3
"""U8h probe -- is the tie-break difference encoding-dependent, or pre-existing?

The U8 verification corpus has one failure, `err-lead-swallows-newline`. Its two
reports decode to **identical** lines:

    left  = [<?xml …GBK?>, ok, ?next]         (3 lines)
    right = [<?xml …UTF-8?>, ok, x, next]     (4 lines)

The only difference is the alignment of the tail:

    BC      : rightorphan x, then (?next vs next)
    product : (?next vs x), then rightorphan next

Both are one orphan plus one replacement, so the choice is a tie. A tie-break is
an alignment rule, and the alignment layer does not know the file was decoded
through a code page -- but "should not" is not "does not", and this project does
not promote reasoning to evidence.

So this probe asks the question directly, in plain text with no declaration and
no code page anywhere:

  * does BC break the tie the same way on ordinary `.txt` content?
  * does the product?

If both answer the same as in the encoding case, the difference is a pre-existing
alignment tie-break that the U8 corpus merely exposed. If they differ, something
in the decode path changed the alignment input and the failure is mine.

It also walks the neighbourhood, because a single point cannot distinguish "BC
always orphans the left line of the block" from "BC prefers the longer match":

    A: (left 3, right 4) tail is [P] vs [Q, R]        -- the measured shape
    B: the same shape with the tail lines swapped in content
    C: a 1-vs-2 tail where the pair is a prefix of the orphan
    D: a 1-vs-2 tail where the orphan is a prefix of the pair
    E: no common prefix lines at all (pure tail)
    F: the tail with two right lines before the pair
    G: the tail with two right lines after the pair

Each is chosen so the tie-break, if it is one, is the only thing that can differ.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u8h_alignment_tiebreak.py
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

#: The measured shape, in plain text. `head` differs so the first line is a
#: replacement, matching the encoding case's declaration-vs-declaration line.
COMMON_HEAD = ("alpha", "beta")

#: name -> (left lines after the head, right lines after the head, purpose)
TAILS: dict[str, tuple[list[str], list[str], str]] = {
    "measured-shape": (["?next"], ["x", "next"],
                       "the exact U8 failure shape, plain text"),
    "swapped-content": (["?tail"], ["y", "tail"],
                        "same shape, different words"),
    "pair-is-prefix": (["pre"], ["pre", "suffix"],
                       "the pair's text is a prefix of the second orphan"),
    "orphan-is-prefix": (["pre"], ["preX", "pre"],
                         "the orphan's text shares a prefix with the pair"),
    "pure-tail": (["tailA"], ["orphanB", "orphanC"],
                  "nothing in common at the tail at all"),
    "two-before": (["tail"], ["o1", "o2", "tail"],
                   "two right orphans before the pair"),
    "two-after": (["tail"], ["tail", "o1", "o2"],
                  "two right orphans after the pair"),
    "left-orphan-shape": (["tail", "lo"], ["tail2"],
                          "mirrored: a left orphan instead of a right one"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8h-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print("purpose : is the tail tie-break encoding-dependent?\n")

    records: list[dict] = []
    for tag, (ltail, rtail, purpose) in TAILS.items():
        ltext = "\n".join(list(COMMON_HEAD) + ltail) + "\n"
        rtext = "\n".join(["gamma"] + list(COMMON_HEAD) + rtail) + "\n"
        lp, rp = fx / f"{tag}-L.txt", fx / f"{tag}-R.txt"
        lp.write_text(ltext, encoding="utf-8", newline="")
        rp.write_text(rtext, encoding="utf-8", newline="")

        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = ""
        if run.report_exists and run.report_bytes:
            o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        p_out = run_dir / "reports" / f"{tag}.product.xml"
        proc = subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)],
                              capture_output=True, timeout=120)
        p_body = ""
        if p_out.exists():
            p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

        def shape(body: str) -> list[tuple[str, str, str]]:
            """(status, ltid, rtid) per linecomp, in report order."""
            out = []
            for m in re.finditer(r'<linecomp status="([a-z]+)">(.*?)</linecomp>',
                                 body, re.S):
                lt = re.search(r'ltid="(\d+)"', m.group(2))
                rt = re.search(r'rtid="(\d+)"', m.group(2))
                out.append((m.group(1), lt.group(1) if lt else "-",
                            rt.group(1) if rt else "-"))
            return out

        o_s, p_s = shape(o_body), shape(p_body)
        same = o_s == p_s
        records.append({"tag": tag, "purpose": purpose, "same": same,
                        "oracle": o_s, "product": p_s,
                        "left": ltext, "right": rtext,
                        "oracle_body": o_body, "product_body": p_body})
        mark = "OK  " if same else "DIFF"
        print(f"  {mark} {tag:<20} {purpose}")
        print(f"       oracle : {o_s}")
        if not same:
            print(f"       product: {p_s}")

    (run_dir / "u8h-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u8h-results.json'}")

    by = {r["tag"]: r for r in records}
    print("\n=== reading ===")
    m = by["measured-shape"]
    if m["same"]:
        print("  measured-shape AGREES in plain text -> the encoding case's "
              "difference is NOT encoding-dependent; it is an alignment "
              "behaviour the U8 corpus exposed.")
    else:
        print("  measured-shape DIFFERS in plain text too -> the tie-break is "
              "pre-existing and reproduces without any code page involved.")
    agree = sum(1 for r in records if r["same"])
    print(f"  {agree}/{len(records)} shapes agree in plain text")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
