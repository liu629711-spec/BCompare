#!/usr/bin/env python3
"""U4f probe -- replace-vs-append for version/owner/group/permissions and the
`ignore-unimportant` scope.

U4e showed the inert trio and `version` REPLACE the default size+timestamp
pair (sizes differed yet the row stayed `same`/directional).  What is not yet
probed is whether a LATER size/timestamp token re-activates (the `attrib:`
pattern) and what `ignore-unimportant` does to size-only differences and to
rules-based whitespace folds.

Cases:
  1. `version size`   equal FileVersion, sizes differ  -> size active?
  2. `version timestamp` equal FileVersion, mtime +2h  -> timestamp active?
  3. `owner size`     sizes differ                     -> size active?
  4. `ignore-unimportant` (alone) sizes differ         -> row status?
  5. `ignore-unimportant rules-based` .c whitespace-only diff -> folded?
  6. `ignore-unimportant rules-based` .c real diff     -> stays diff?
  7. PE vs txt both directions under `version`
  8. `version rules-based` equal versions, comment-only diff -> rules-based active?

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4f_combos.py
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


def fresh(root: pathlib.Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)


def stamp_all(root: pathlib.Path) -> None:
    for p in sorted(root.rglob("*"), reverse=True):
        os.utime(p, (FIXED, FIXED))
    os.utime(root, (FIXED, FIXED))


def set_fileversion_ms_low(path: pathlib.Path, lo: int) -> None:
    """Write `lo` into the LOW word of dwFileVersionMS only (lo != original)."""
    data = bytearray(path.read_bytes())
    i = data.find(struct.pack("<I", 0xFEEF04BD))
    if i < 0:
        raise SystemExit("no VS_FIXEDFILEINFO")
    struct.pack_into("<H", data, i + 8, lo)
    path.write_bytes(bytes(data))


CASES = [
    ("f-version-plus-size", "version size", "dll equal versions, r padded 2048"),
    ("f-version-plus-timestamp", "version timestamp", "dll equal versions, r mtime +2h"),
    ("f-owner-plus-size", "owner size", "txt sizes 10 vs 2058"),
    ("f-iu-alone-size", "ignore-unimportant", "txt sizes 10 vs 2058"),
    ("f-iu-rb-ws", "ignore-unimportant rules-based", "c file whitespace-only diff"),
    ("f-iu-rb-real", "ignore-unimportant rules-based", "c file identifier diff"),
    ("f-version-pe-left", "version", "pe left, txt right"),
    ("f-version-pe-right", "version", "txt left, pe right"),
    ("f-version-rb-comment", "version rules-based", "dll equal versions; c-file comment diff control"),
    ("f-rb-comment-higher-vers", "version rules-based", "dll r FileVersion higher; c comment diff present too"),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4f-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    dll = pathlib.Path(r"C:\Windows\System32\version.dll").read_bytes()
    # original FileVersionMS low word (== 0 for 10.0.x)
    i0 = dll.find(struct.pack("<I", 0xFEEF04BD))
    orig_lo = struct.unpack_from("<H", dll, i0 + 8)[0]
    print(f"original FileVersionMS low word = {orig_lo}")

    records = []
    for name, criteria, build in CASES:
        root = run_dir / "fixtures" / name
        L, R = root / "L", root / "R"
        fresh(root); L.mkdir(); R.mkdir()
        if "dll" in build:
            (L / "app.dll").write_bytes(dll)
            (R / "app.dll").write_bytes(dll)
            if "r padded" in build:
                with (R / "app.dll").open("ab") as f:
                    f.write(b"\x00" * 2048)
            if "r mtime +2h" in build:
                os.utime(R / "app.dll", (FIXED + 7200, FIXED + 7200))
            if "r FileVersion higher" in build:
                set_fileversion_ms_low(R / "app.dll", orig_lo + 1)
            if "c comment diff" in build or "c-file" in build:
                (L / "t.c").write_bytes(b"int x; // old\n")
                (R / "t.c").write_bytes(b"int x; // new\n")
        elif "pe left" in build:
            (L / "app.dll").write_bytes(dll)
            (R / "app.dll").write_bytes(b"not a pe at all\n")
        elif "pe right" in build:
            (L / "app.dll").write_bytes(b"not a pe at all\n")
            (R / "app.dll").write_bytes(dll)
        elif "txt sizes" in build:
            (L / "a.bin").write_bytes(b"0123456789")
            (R / "a.bin").write_bytes(b"0123456789" + b"\x00" * 2048)
        elif "whitespace-only" in build:
            (L / "t.c").write_bytes(b"int  x;\n")
            (R / "t.c").write_bytes(b"int x;\n")
        elif "identifier diff" in build:
            (L / "t.c").write_bytes(b"int x;\n")
            (R / "t.c").write_bytes(b"int y;\n")
        stamp_all(L); stamp_all(R)

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
        statuses = re.findall(r'<(?:file|folder)comp status="([a-z]+)">', body)
        records.append({"probe": name, "criteria": criteria, "build": build,
                        "exit": run.exit_code, "statuses": statuses})
        print(f"  {name:<26} crit={criteria:<28} statuses={statuses}")

    (run_dir / "u4f-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4f-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
