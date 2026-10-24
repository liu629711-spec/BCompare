#!/usr/bin/env python3
"""U4b probe -- isolate `version` and re-test the inert trio properly.

U4's first round confounded `version` with the timestamp criterion (patching a
PE resource updates mtime, so the row went `rtnewer` before version was even
consulted) and used a synthetic PE whose version resource BC may not parse.
This round:

  * copies a REAL system DLL (version.dll) that BC's version reader definitely
    understands, with the right side's VS_FIXEDFILEINFO fields patched, and
  * normalises BOTH sides' mtime to a fixed value (and probes size separately)
    so each criterion's own effect is the only variable.

Also re-tests owner/group/permissions with a *directory* ACL difference and a
system-owned source file, to confirm the Windows-inert finding is not an
artefact of file-level ACLs.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4b_version_isolation.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

FIXED_MTIME = 1_767_225_600  # 2026-01-01 00:00:00 UTC


def write_tree(root: pathlib.Path, files: dict[str, bytes], dirs=()) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def patch_version(path: pathlib.Path, version: str) -> None:
    data = bytearray(path.read_bytes())
    sig = struct.pack("<I", 0xFEEF04BD)
    i = data.find(sig)
    if i < 0:
        raise SystemExit(f"no VS_FIXEDFILEINFO in {path}")
    parts = [int(x) for x in version.split(".")]
    for k, part in enumerate(parts[:4]):
        struct.pack_into("<H", data, i + 8 + k * 4, part)
        struct.pack_into("<H", data, i + 16 + k * 4, part)
    path.write_bytes(bytes(data))


def stamp(path: pathlib.Path) -> None:
    os.utime(path, (FIXED_MTIME, FIXED_MTIME))


def stamp_tree(root: pathlib.Path) -> None:
    for p in sorted(root.rglob("*"), reverse=True):
        stamp(p)
    stamp(root)


def real_dll() -> bytes:
    p = pathlib.Path(r"C:\Windows\System32\version.dll")
    if not p.is_file():
        raise SystemExit("no C:\\Windows\\System32\\version.dll")
    return p.read_bytes()


CASES = [
    ("ver-real-equal", "version", "real dll, both mtimes fixed, identical bytes"),
    ("ver-real-differs", "version", "real dll, r patched to 9.9.9.9, mtimes fixed"),
    ("ver-real-differs-plain", "", "same pair with DEFAULT criteria (control)"),
    ("ver-real-differs-size-absorbs", "version", "patched AND r padded (size differs)"),
    ("ver-size-only", "size", "real dll, r patched (control for size token)"),
    ("ver-timestamp-only", "timestamp", "real dll, r patched, mtimes NOT fixed (control)"),
    ("perm-dir-acl", "permissions", "directory deny ACE on the right side"),
    ("owner-systemdir", "owner", "left copied from a SYSTEM-owned file"),
    ("group-systemdir", "group", "same, group token"),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4b-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    installs = inst_mod.discover()
    cur = installs["current"]
    if not cur.enabled:
        raise SystemExit(f"current install disabled: {cur.disabled_reason}")
    print(f"oracle : {cur.oracle_path} (engine {cur.oracle_version})")
    print(f"run dir: {run_dir}\n")

    dll = real_dll()
    records = []
    for name, criteria, desc in CASES:
        root = run_dir / "fixtures" / name
        left, right = root / "L", root / "R"
        if name.startswith("ver-"):
            write_tree(left, {"app.dll": dll})
            write_tree(right, {"app.dll": dll})
            if name in ("ver-real-differs", "ver-real-differs-plain",
                        "ver-size-only"):
                patch_version(right / "app.dll", "9.9.9.9")
            if name in ("ver-real-equal", "ver-real-differs",
                        "ver-real-differs-plain", "ver-size-only"):
                stamp_tree(left); stamp_tree(right)
            if name == "ver-real-differs-size-absorbs":
                patch_version(right / "app.dll", "9.9.9.9")
                with (right / "app.dll").open("ab") as f:
                    f.write(b"\x00" * 4096)
                stamp_tree(left); stamp_tree(right)
            if name == "ver-timestamp-only":
                patch_version(right / "app.dll", "9.9.9.9")
                stamp_tree(left)
                os.utime(right / "app.dll", (FIXED_MTIME + 7200, FIXED_MTIME + 7200))
                stamp(right)
        elif name == "perm-dir-acl":
            write_tree(left, {"x.txt": b"same"}, dirs=["sub"])
            write_tree(right, {"x.txt": b"same"}, dirs=["sub"])
            stamp_tree(left); stamp_tree(right)
            r = subprocess.run(["icacls", str(right / "sub"), "/deny", "*S-1-1-0:(R)"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  {name}: SKIP (deny ACE failed)")
                records.append({"probe": name, "skipped": "acl"})
                continue
        elif name in ("owner-systemdir", "group-systemdir"):
            src = pathlib.Path(r"C:\Windows\System32\version.dll")
            data = src.read_bytes()
            write_tree(left, {"x.txt": data})
            write_tree(right, {"x.txt": data})
            # Recreate the source's ownership by copying ACLs from it.
            subprocess.run(["icacls", str(right / "x.txt"), "/copy", str(src)],
                           capture_output=True, text=True)
            stamp_tree(left); stamp_tree(right)

        out = run_dir / "reports" / f"{name}.xml"
        lines = []
        if criteria:
            lines.append(f"criteria {criteria}")
        lines += [f'load "{left}" "{right}"', "expand all",
                  f'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "reports" / f"{name}.bcs", lines)
        run = orc.run(cur.oracle_path, script, left, right, out,
                      timeout=180.0, script_text="\n".join(lines))
        body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
        statuses = re.findall(r'<filecomp status="([a-z]+)">', body)
        sizes = re.findall(r"<size>([^<]*)</size>", body)
        records.append({"probe": name, "criteria": criteria, "desc": desc,
                        "exit": run.exit_code, "statuses": statuses, "sizes": sizes,
                        "report_bytes": len(body), "containment": run.containment})
        print(f"  {name:<30} exit={run.exit_code} statuses={statuses} sizes={sizes}")

    (run_dir / "u4b-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw results: {run_dir / 'u4b-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
