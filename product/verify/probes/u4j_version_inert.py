#!/usr/bin/env python3
"""U4j probe -- is `version` actually active, or inert like the POSIX trio?

Serial-05's gate reports are ambiguous and contradict the earlier u4b/u4c runs:

  * u4b `ver-real-differs` reported `rtnewer` for a patched real DLL -- but the
    patch changed the file's mtime, and the timestamp criterion was ALSO active
    at that point, so `rtnewer` may have come from the mtime, not the version.
  * serial-05 `crit-version-equal` reports `same` for pairs whose versions
    differ AND whose sizes differ (88 vs 96, 88 vs 17, 88 vs 4,184) -- with
    mtimes normalised, nothing at all differs.
  * serial-05 `crit-version-size` reports `diff` only for the rows whose SIZES
    differ.

Hypothesis: `version` is inert on Windows (like owner/group/permissions) and
every `ltnewer`/`rtnewer` seen earlier was the timestamp criterion firing.

This probe isolates it with mtimes held FIXED on both sides (and directories'
mtimes too), varying only the version resource:

  1. equal versions, equal size, fixed mtime       -> expect same either way
  2. different versions, equal size, fixed mtime   -> `same` proves inert
  3. different versions, differing size, fixed mtime -> `diff` only if version
     is inert and the size token is the one comparing

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4j_version_inert.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import struct
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

FIXED = 1_767_225_600
SIG = (0xFEEF04BD).to_bytes(4, "little")


def patch(path: pathlib.Path, ms: int) -> None:
    data = bytearray(path.read_bytes())
    i = data.find(SIG)
    struct.pack_into("<I", data, i + 8, ms)
    struct.pack_into("<I", data, i + 16, ms)
    path.write_bytes(bytes(data))


def freeze(root: pathlib.Path) -> None:
    for p in sorted(root.rglob("*"), reverse=True):
        os.utime(p, (FIXED, FIXED))
    os.utime(root, (FIXED, FIXED))


CASES = [
    ("v-equal", "version", 0, 0),
    ("v-differs", "version", 0, 1),
    ("v-differs-size", "version size", 0, 1),
    ("v-differs-plus-pad", "version", 0, 1),
    ("control-timestamp", "timestamp", 0, 1),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4j-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    base = pathlib.Path(r"C:\Windows\System32\version.dll").read_bytes()
    # The real version of version.dll is 10.0.26100.1150 -> FileVersionMS=0x000A0000.
    records = []
    for name, criteria, lpatch, rpatch in CASES:
        root = run_dir / "fixtures" / name
        if root.exists():
            shutil.rmtree(root)
        L, R = root / "L", root / "R"
        L.mkdir(parents=True)
        R.mkdir(parents=True)
        (L / "a.dll").write_bytes(base)
        (R / "a.dll").write_bytes(base)
        if lpatch:
            patch(L / "a.dll", 0x0009_0000)
        if rpatch:
            patch(R / "a.dll", 0x000B_0000)
        if name == "v-differs-plus-pad":
            with (R / "a.dll").open("ab") as f:
                f.write(b"\x00" * 4096)
        freeze(L)
        freeze(R)

        out = run_dir / "reports" / f"{name}.xml"
        lines = []
        if criteria:
            lines.append(f"criteria {criteria}")
        lines += [f'load "{L}" "{R}"', "expand all",
                  f'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "reports" / f"{name}.bcs", lines)
        run = orc.run(inst.oracle_path, script, L, R, out,
                      timeout=180.0, script_text="\n".join(lines))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        statuses = re.findall(r'<filecomp status="([a-z]+)">', body)
        sizes = re.findall(r"<size>([^<]*)</size>", body)
        records.append({"probe": name, "criteria": criteria,
                        "left_ms": hex(0x0009_0000 if lpatch else 0x000A_0000),
                        "right_ms": hex(0x000B_0000 if rpatch else 0x000A_0000),
                        "statuses": statuses, "sizes": sizes})
        print(f"  {name:<20} crit={criteria:<12} statuses={statuses} sizes={sizes}")

    (run_dir / "u4j-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4j-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
