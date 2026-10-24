#!/usr/bin/env python3
"""U4c probe -- `version` criteria semantics in isolation.

U4b showed: with `criteria version` and mtimes fixed, two DLLs whose version
resource differs report `rtnewer` (right = 9.9.9.9 > left = original).  That is
NOT a plain same/different criterion.  This round pins the mechanics:

  1. direction          -- left higher -> `ltnewer`? equal -> `same`?
  2. replace vs add     -- with versions EQUAL, does a timestamp/size
                           difference still report newer/diff (additive), or
                           get ignored (replacing)?
  3. non-PE inputs      -- a .txt under `criteria version`.
  4. which version field-- file vs product version: patch only one group.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4c_version_semantics.py
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

FIXED = 1_767_225_600  # 2026-01-01 00:00:00Z


def fresh(root: pathlib.Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)


def patch(path: pathlib.Path, version: str, fields: str = "both") -> None:
    """`fields`: 'both' | 'file' | 'product'."""
    data = bytearray(path.read_bytes())
    i = data.find(struct.pack("<I", 0xFEEF04BD))
    if i < 0:
        raise SystemExit(f"no VS_FIXEDFILEINFO in {path}")
    parts = [int(x) for x in version.split(".")]
    for k, part in enumerate(parts[:4]):
        if fields in ("both", "file"):
            struct.pack_into("<H", data, i + 8 + k * 4, part)
        if fields in ("both", "product"):
            struct.pack_into("<H", data, i + 16 + k * 4, part)
    path.write_bytes(bytes(data))


def stamp(p: pathlib.Path, t: int = FIXED) -> None:
    os.utime(p, (t, t))


def read_version(path: pathlib.Path) -> str:
    data = path.read_bytes()
    i = data.find(struct.pack("<I", 0xFEEF04BD))
    words = struct.unpack_from("<8H", data, i + 8)
    fv = ".".join(str(w) for w in words[0:4])
    return fv


CASES = [
    # (name, criteria, build)
    ("ver-left-higher", "version", "l=9.9.9.9, r=orig"),
    ("ver-both-higher-right", "version", "l=9.9.9.9, r=10.0.0.0"),
    ("ver-equal-ts-differs", "version", "equal versions, r mtime +2h"),
    ("ver-equal-size-differs", "version", "equal versions, r padded 4096"),
    ("ver-equal-size-and-ts", "version", "equal versions, r padded + mtime +2h"),
    ("ver-less-than", "version", "l=9.9.9.9 vs r=9.9.9.8"),
    ("ver-txt-files", "version", "plain txt both sides, contents differ"),
    ("ver-file-only-field", "version", "only FILE version field patched on r"),
    ("ver-product-only-field", "version", "only PRODUCT version field patched on r"),
    ("size-default-control", "size", "equal versions, r padded (size token control)"),
    ("default-padded-control", "", "equal versions, r padded (default control)"),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4c-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    dll = pathlib.Path(r"C:\Windows\System32\version.dll").read_bytes()
    orig = read_version_from_bytes(dll) if False else None
    records = []
    for name, criteria, build in CASES:
        root = run_dir / "fixtures" / name
        left, right = root / "L", root / "R"
        fresh(root); (left).mkdir(); (right).mkdir()
        if name == "ver-txt-files":
            (left / "a.txt").write_bytes(b"alpha\n")
            (right / "a.txt").write_bytes(b"beta\n")
        else:
            (left / "app.dll").write_bytes(dll)
            (right / "app.dll").write_bytes(dll)
            if build == "l=9.9.9.9, r=orig":
                patch(left / "app.dll", "9.9.9.9")
            elif build == "l=9.9.9.9, r=10.0.0.0":
                patch(left / "app.dll", "9.9.9.9")
                patch(right / "app.dll", "10.0.0.0")
            elif build == "equal versions, r mtime +2h":
                stamp(right / "app.dll", FIXED + 7200)
            elif build == "equal versions, r padded 4096":
                with (right / "app.dll").open("ab") as f:
                    f.write(b"\x00" * 4096)
            elif build == "equal versions, r padded + mtime +2h":
                with (right / "app.dll").open("ab") as f:
                    f.write(b"\x00" * 4096)
                stamp(right / "app.dll", FIXED + 7200)
            elif build == "l=9.9.9.9 vs r=9.9.9.8":
                patch(left / "app.dll", "9.9.9.9")
                patch(right / "app.dll", "9.9.9.8")
            elif build == "only FILE version field patched on r":
                patch(right / "app.dll", "9.9.9.9", fields="file")
            elif build == "only PRODUCT version field patched on r":
                patch(right / "app.dll", "9.9.9.9", fields="product")
            elif build.startswith("equal versions") or "padded" in build:
                with (right / "app.dll").open("ab") as f:
                    f.write(b"\x00" * 4096)
            stamp(left / "app.dll"); stamp(right / "app.dll")
            stamp(left); stamp(right)

        out = run_dir / "reports" / f"{name}.xml"
        lines = []
        if criteria:
            lines.append(f"criteria {criteria}")
        lines += [f'load "{left}" "{right}"', "expand all",
                  f'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "reports" / f"{name}.bcs", lines)
        run = orc.run(inst.oracle_path, script, left, right, out,
                      timeout=180.0, script_text="\n".join(lines))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        statuses = re.findall(r'<filecomp status="([a-z]+)">', body)
        sizes = re.findall(r"<size>([^<]*)</size>", body)
        records.append({"probe": name, "criteria": criteria, "build": build,
                        "exit": run.exit_code, "statuses": statuses, "sizes": sizes})
        print(f"  {name:<28} crit={criteria or '(default)':<8} statuses={statuses} sizes={sizes}")

    (run_dir / "u4c-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4c-results.json'}")
    return 0


def read_version_from_bytes(data: bytes) -> str:
    i = data.find(struct.pack("<I", 0xFEEF04BD))
    words = struct.unpack_from("<8H", data, i + 8)
    return ".".join(str(w) for w in words[0:4])


if __name__ == "__main__":
    raise SystemExit(main())
