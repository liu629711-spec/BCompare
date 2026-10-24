#!/usr/bin/env python3
"""U2b probe -- orphan status semantics + ignore-unimportant pairing (M2).

U2 found that a one-sided line whose content is entirely unimportant (a
comment) is reported ``leftsimilar``/``rightsimilar`` -- not ``leftorphan`` --
and that under ``ignore-unimportant`` such a line folds to ``same`` while
REUSING another line's rtid.  Neither is in the M1 model, and one existing
anchor (``al-empty-left``: empty file vs one code line -> ``rightorphan``)
shows empty lines do NOT get the similar-orphan treatment.  This probe pins
the rule before M2 wires it:

  * which one-sided lines are ``leftsimilar`` (comment only? blank? a line
    whose important part is non-empty?), in lead/mid/trail position
  * the right-side mirror
  * what ``ignore-unimportant`` attaches to one-sided unimportant lines
    (which rtid, reused or not) and whether comment-vs-code folds

Method identical to U1/U2: minimal pairs through the live Oracle, serial, two
modes.  Raw outputs land in ``product/verify/runs/u2b-probe-<ts>/``.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u2b_orphan_semantics.py
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

#: (probe name, extension, left lines, right lines)
PAIRS = [
    # ---- which one-sided lines are leftsimilar? -------------------------
    ("orphan-comment-trailing", "c",
     ["int a;", "int b;", "// c"], ["int x;"]),
    ("orphan-comment-lead", "c",
     ["// c", "int b;"], ["int x;"]),
    ("orphan-comment-mid", "c",
     ["int a;", "// c", "int b;"], ["int x;", "int y;"]),
    ("orphan-two-comments", "c",
     ["// a", "// b"], ["int x;"]),
    ("orphan-right-comment", "c",
     ["int x;"], ["int y;", "// c"]),
    ("orphan-ws-line", "c",
     ["   ", "int x;"], ["int x;"]),
    ("orphan-empty-line", "c",
     ["int x;", ""], ["int x;"]),
    ("orphan-mixed-trailing-comment", "c",
     ["int a;", "x = 1; // c"], ["int a;"]),
    ("orphan-comment-inside-replace", "c",
     ["// a", "int b;"], ["int x;", "int y;"]),
    # ---- ignore-unimportant attachment model -----------------------------
    ("iu-comment-after-code", "c",
     ["int x;", "// a"], ["int x;"]),
    ("iu-comment-before-code", "c",
     ["// a", "int x;"], ["int x;"]),
    ("iu-three-comments-one", "c",
     ["// a", "// b", "// c"], ["// z"]),
    ("iu-comment-vs-code", "c",
     ["// note"], ["x;"]),
    ("iu-empty-vs-code", "c",
     [""], ["int x;"]),
    ("iu-swap-trailing-comment", "c",
     ["int a;", "x = 1; // one"],
     ["x = 1; // two", "int a;"]),
    ("iu-one-comment-none", "c",
     ["// a"], ["int x;"]),
]

MODES = [None, "ignore-unimportant"]

STATUS_RE = re.compile(r'<linecomp status="([a-z]+)"')
ROW_RE = re.compile(r'<text([^>]*)>(.*?)</text>', re.S)


def rows(xml_text: str) -> list[str]:
    """Compact per-linecomp summary: status + the text elements."""
    out = []
    for m in re.finditer(r'<linecomp status="([a-z]+)">(.*?)</linecomp>', xml_text, re.S):
        status, body = m.group(1), m.group(2)
        texts = ["%s>%s" % (" ".join(a.split()), t) for a, t in ROW_RE.findall(body)]
        out.append(f"{status}: " + " | ".join(texts))
    return out


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u2b-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")
    print(f"run dir: {run_dir}\n")

    records = []
    for name, ext, left_lines, right_lines in PAIRS:
        left = run_dir / "fixtures" / f"{name}-L.{ext}"
        right = run_dir / "fixtures" / f"{name}-R.{ext}"
        left.write_text("\n".join(left_lines) + "\n", encoding="utf-8")
        right.write_text("\n".join(right_lines) + "\n", encoding="utf-8")
        for mode in MODES:
            tag = name if mode is None else f"{name}+iu"
            out = run_dir / "reports" / f"{tag}.xml"
            script = orc.write_script(
                run_dir / "reports" / f"{tag}.bcs",
                [orc.text_script("xml", mode)])
            run = orc.run(cur.oracle_path, script, left, right, out,
                          timeout=120.0, script_text=orc.text_script("xml", mode))
            statuses = []
            row_summary: list[str] = []
            if run.report_exists:
                body = out.read_bytes().decode("utf-8-sig", errors="replace")
                statuses = STATUS_RE.findall(body)
                row_summary = rows(body)
            records.append({
                "probe": name, "ext": ext, "mode": mode or "default",
                "tag": tag,
                "left": left_lines, "right": right_lines,
                "exit": run.exit_code, "statuses": statuses,
                "rows": row_summary,
                "containment": run.containment,
            })
            print(f"  {tag:<36} exit={run.exit_code} statuses={statuses}")
            for r in row_summary:
                print(f"      {r}")

    (run_dir / "u2b-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw results: {run_dir / 'u2b-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
