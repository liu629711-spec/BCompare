#!/usr/bin/env python3
"""U4k probe -- why does the generated fixture differ from the u4j pair?

The generated `versioned` fixture (both sides built by patching a real
version.dll) reports `same` for a 9.9.9.9-vs-1.0.0.0 pair, while u4j's
0x00090000-vs-0x000B0000 pair reports `rtnewer`.  The only differences are
(a) which version WORDS were written, and (b) that the fixture patched the
PRODUCT version too.

Candidates:
  H1 the ProductVersion write breaks the resource the Oracle reads;
  H2 the Oracle compares only some words;
  H3 the 1.0.0.0 side (all words written low) is malformed somehow.

This probe steps through variants from the working u4j shape to the fixture
shape, one change at a time, on the SAME base DLL with mtimes frozen.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4k_fixture_vs_u4j.py
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


def write_versions(path: pathlib.Path, fv, pv, write_pv: bool) -> None:
    data = bytearray(path.read_bytes())
    i = data.find(SIG)
    fms = (fv[0] << 16) | fv[1]
    fls = (fv[2] << 16) | fv[3]
    struct.pack_into("<I", data, i + 8, fms)
    struct.pack_into("<I", data, i + 12, fls)
    if write_pv:
        pms = (pv[0] << 16) | pv[1]
        pls = (pv[2] << 16) | pv[3]
        struct.pack_into("<I", data, i + 16, pms)
        struct.pack_into("<I", data, i + 20, pls)
    path.write_bytes(bytes(data))


def freeze(root: pathlib.Path) -> None:
    for p in sorted(root.rglob("*"), reverse=True):
        os.utime(p, (FIXED, FIXED))
    os.utime(root, (FIXED, FIXED))


# (name, left spec, right spec). A spec is (fv, pv, write_pv).
CASES = [
    ("msword-only", ((1, 0, 0, 0), (1, 0, 0, 0), False), ((9, 0, 0, 0), (9, 0, 0, 0), False)),
    ("full-fields", ((1, 0, 0, 0), (1, 0, 0, 0), False), ((9, 9, 9, 9), (9, 9, 9, 9), False)),
    ("with-product", ((1, 0, 0, 0), (1, 0, 0, 0), True), ((9, 9, 9, 9), (9, 9, 9, 9), True)),
    ("fixture-shape", ((1, 0, 0, 0), (1, 0, 0, 0), True), ((9, 9, 9, 9), (9, 9, 9, 9), True)),
    ("left-hi-only", ((9, 9, 9, 9), (9, 9, 9, 9), True), ((1, 0, 0, 0), (1, 0, 0, 0), True)),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4k-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    base = pathlib.Path(r"C:\Windows\System32\version.dll").read_bytes()
    records = []
    for name, lspec, rspec in CASES:
        root = run_dir / "fixtures" / name
        if root.exists():
            shutil.rmtree(root)
        L, R = root / "L", root / "R"
        L.mkdir(parents=True)
        R.mkdir(parents=True)
        (L / "a.dll").write_bytes(base)
        (R / "a.dll").write_bytes(base)
        write_versions(L / "a.dll", lspec[0], lspec[1], lspec[2])
        write_versions(R / "a.dll", rspec[0], rspec[1], rspec[2])
        freeze(L)
        freeze(R)

        out = run_dir / "reports" / f"{name}.xml"
        lines = ["criteria version", f'load "{L}" "{R}"', "expand all",
                 f'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "reports" / f"{name}.bcs", lines)
        run = orc.run(inst.oracle_path, script, L, R, out,
                      timeout=180.0, script_text="\n".join(lines))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        statuses = re.findall(r'<filecomp status="([a-z]+)">', body)
        records.append({"probe": name, "statuses": statuses})
        print(f"  {name:<16} statuses={statuses}")

    (run_dir / "u4k-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4k-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
