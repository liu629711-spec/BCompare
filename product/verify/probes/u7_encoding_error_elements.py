#!/usr/bin/env python3
"""U7 probe -- the `<errorN>` element when the RIGHT side (or both) cannot decode.

The golden anchor `enc-latin1` has an invalid byte on the LEFT only, and BC
writes exactly one element:

    <error1>File Encoding Error (Line 1)</error1>

The product's writer has always emitted the **same** tag name on both sides
(`error1` for left, `error1` for right), because that is what a single
left-side observation supports.  But BC's own naming everywhere else in the
report is side-numbered (`filename1`/`filename2`), so `<error2>` for the right
side is the natural guess — and a guess is not good enough for a report the
harness compares byte-for-byte.

This probe measures all three states:

  1. left invalid only   (already known: one `<error1>`)
  2. right invalid only  (unobserved: `<error1>` or `<error2>`?)
  3. both invalid        (unobserved: how many elements, which names, what order?)
  4. a multi-line file whose SECOND line is the invalid one, so the line number
     inside the element is exercised rather than assumed

It also records the invalid-byte case with the file's bytes ASCII on one side,
to separate "cannot decode" from "decodes differently".

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u7_encoding_error_elements.py
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

#: name -> (left bytes, right bytes).  `\xe9` is a lone Latin-1 e-acute, invalid
#: in UTF-8; the right side is its correct UTF-8 spelling.
CASES: dict[str, tuple[bytes, bytes]] = {
    "left-invalid":  (b"caf\xe9\n", b"caf\xc3\xa9\n"),
    "right-invalid": (b"caf\xc3\xa9\n", b"caf\xe9\n"),
    "both-invalid":  (b"caf\xe9\n", b"caf\xe8\n"),
    "second-line":   (b"ok\naf\xe9\n", b"ok\naf\xc3\xa9\n"),
    "left-invalid-second-line": (b"ok\naf\xe9\n", b"ok\naf\xe9\n"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u7-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"product : {PRODUCT}\n")

    records: list[dict] = []
    for tag, (lb, rb) in CASES.items():
        lp, rp = fx / f"{tag}-L.txt", fx / f"{tag}-R.txt"
        lp.write_bytes(lb)
        rp.write_bytes(rb)

        # --- Oracle ---
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = ""
        if run.report_exists and run.report_bytes:
            o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        # --- product ---
        p_out = run_dir / "reports" / f"{tag}.product.xml"
        proc = subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)],
                              capture_output=True, timeout=120)
        p_body = ""
        if p_out.exists():
            p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

        o_errs = re.findall(r"<(error\d)>(.*?)</error\d>", o_body)
        p_errs = re.findall(r"<(error\d)>(.*?)</error\d>", p_body)
        o_statuses = re.findall(r'<linecomp status="([a-z]+)"', o_body)
        p_statuses = re.findall(r'<linecomp status="([a-z]+)"', p_body)

        agree = o_errs == p_errs and o_statuses == p_statuses
        records.append({
            "tag": tag, "left_hex": lb.hex(), "right_hex": rb.hex(),
            "oracle_exit": run.exit_code,
            "oracle_errors": o_errs, "product_errors": p_errs,
            "oracle_statuses": o_statuses, "product_statuses": p_statuses,
            "agree": agree,
            "oracle_body": o_body, "product_body": p_body,
        })
        mark = "OK  " if agree else "DIFF"
        print(f"  {mark} {tag:<26} oracle={o_errs}")
        if not agree:
            print(f"       {'':<26} product={p_errs}  statuses {p_statuses} vs {o_statuses}")

    (run_dir / "u7-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u7-results.json'}")

    # Show the raw element region of the interesting cases, so the exact bytes
    # are recorded rather than a summary of them.
    for r in records:
        if r["tag"] in ("right-invalid", "both-invalid", "second-line") and not r["agree"]:
            print(f"\n--- oracle, {r['tag']} (element region) ---")
            for line in r["oracle_body"].splitlines():
                if "error" in line or "linecomp" in line:
                    print("   ", repr(line))
            print(f"--- product, {r['tag']} (element region) ---")
            for line in r["product_body"].splitlines():
                if "error" in line or "linecomp" in line:
                    print("   ", repr(line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
