#!/usr/bin/env python3
"""U4i probe -- does ANY criteria token reset the criterion set?

U4h showed `criteria ignore-unimportant` alone reports `same` for rows whose
sizes and timestamps differ, i.e. the default size+timestamp pair was NOT in
force.  Two competing models:

  A. **Reset** -- the `criteria` command CLEARS the criterion set, then adds
     what the tokens name. With no content token, nothing is compared.
  B. **Modifier-only trap** -- only `ignore-unimportant` behaves this way.

This probe distinguishes them by naming each modifier-ish token alone on a pair
whose size and timestamp both differ:

  * `timezone:ignore`
  * `follow-symlinks`
  * `attrib:z`   (already observed `same` for a timestamp-newer file, F5)
  * `ignore-unimportant`
  * and the empty criteria (control: must be the default pair)

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4i_token_reset.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

FIXED = 1_767_225_600
CASES = [
    ("control-default", ""),
    ("tz-ignore-alone", "timezone:ignore"),
    ("follow-symlinks-alone", "follow-symlinks"),
    ("attrib-z-alone", "attrib:z"),
    ("ignore-unimportant-alone", "ignore-unimportant"),
    ("timestamp-alone", "timestamp"),
    ("size-alone", "size"),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4i-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    root = run_dir / "fixtures" / "pair"
    L, R = root / "L", root / "R"
    if root.exists():
        shutil.rmtree(root)
    L.mkdir(parents=True)
    R.mkdir(parents=True)
    # Size differs AND the right side is 2 hours newer: both quick tests fire.
    (L / "a.bin").write_bytes(b"0123456789")
    (R / "a.bin").write_bytes(b"0123456789" + b"\x00" * 2048)
    os.utime(L / "a.bin", (FIXED, FIXED))
    os.utime(R / "a.bin", (FIXED + 7200, FIXED + 7200))
    os.utime(L, (FIXED, FIXED))
    os.utime(R, (FIXED, FIXED))

    records = []
    for tag, criteria in CASES:
        out = run_dir / "reports" / f"{tag}.xml"
        lines = []
        if criteria:
            lines.append(f"criteria {criteria}")
        lines += [f'load "{L}" "{R}"', "expand all",
                  f'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, L, R, out,
                      timeout=180.0, script_text="\n".join(lines))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        statuses = re.findall(r'<filecomp status="([a-z]+)">', body)
        records.append({"tag": tag, "criteria": criteria, "exit": run.exit_code,
                        "statuses": statuses})
        print(f"  {tag:<26} crit={criteria or '(default)':<22} statuses={statuses}")

    (run_dir / "u4i-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4i-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
