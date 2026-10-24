#!/usr/bin/env python3
"""U4d probe -- size formatting, zero-byte files, mixed version, folder
ignore-unimportant semantics.

Open questions after U4/U4b/U4c:

  * `<size>55,192</size>` -- thousands comma.  Locale-dependent?  Run the same
    fixture on the English reference install.  Zero-byte file: `<size/>` or
    `<size>0</size>`?  Big directory subtree sums: comma too?
  * `version` with one side lacking version info (PE vs txt renamed .exe).
  * Folder `ignore-unimportant`: which one-sided rows fold?  An empty
    directory vs missing (U4 saw a foldercomp with NO status attribute and no
    rt side under ignore-unimportant) -- what does that row look like WITHOUT
    the token, and what about one-sided non-empty dirs and one-sided files?

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4d_sizes_and_folders.py
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


def fresh(root: pathlib.Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)


def stamp_all(root: pathlib.Path) -> None:
    for p in sorted(root.rglob("*"), reverse=True):
        os.utime(p, (FIXED, FIXED))
    os.utime(root, (FIXED, FIXED))


CASES = [
    ("size-big", "", "6017-byte file both sides (comma?)"),
    ("size-zero", "", "0-byte file both sides (<size/>?)"),
    ("size-dir-big", "", "subtree total 5000+ (dir comma?)"),
    ("version-pe-vs-txt", "version", "PE left, same bytes renamed .exe? no: txt right"),
    ("iu-empty-dir-onesided", "ignore-unimportant", "emptydir left only"),
    ("plain-empty-dir-onesided", "", "emptydir left only (control)"),
    ("iu-nonempty-dir-onesided", "ignore-unimportant", "dir with a file left only"),
    ("iu-file-onesided", "ignore-unimportant", "file left only"),
    ("iu-empty-dirs-both", "ignore-unimportant", "emptydir both sides, mtimes differ"),
    ("iu-nested-empty", "ignore-unimportant", "empty dir inside a dir, left only"),
]


def build(name: str, root: pathlib.Path) -> None:
    L, R = root / "L", root / "R"
    fresh(root); L.mkdir(); R.mkdir()
    if name == "size-big":
        (L / "big.bin").write_bytes(b"x" * 6017)
        (R / "big.bin").write_bytes(b"x" * 6017)
    elif name == "size-zero":
        (L / "empty.bin").write_bytes(b"")
        (R / "empty.bin").write_bytes(b"")
    elif name == "size-dir-big":
        for side in (L, R):
            (side / "sub").mkdir()
            (side / "sub" / "a.bin").write_bytes(b"y" * 5000)
    elif name == "version-pe-vs-txt":
        dll = pathlib.Path(r"C:\Windows\System32\version.dll").read_bytes()
        (L / "app.dll").write_bytes(dll)
        (R / "app.dll").write_bytes(dll[:2048])  # not a PE
    elif name == "iu-empty-dir-onesided":
        (L / "emptydir").mkdir()
    elif name == "plain-empty-dir-onesided":
        (L / "emptydir").mkdir()
    elif name == "iu-nonempty-dir-onesided":
        (L / "d").mkdir(); (L / "d" / "f.txt").write_bytes(b"z")
    elif name == "iu-file-onesided":
        (L / "only.txt").write_bytes(b"z")
    elif name == "iu-empty-dirs-both":
        (L / "e").mkdir(); (R / "e").mkdir()
        os.utime(L / "e", (FIXED, FIXED))
        os.utime(R / "e", (FIXED + 7200, FIXED + 7200))
    elif name == "iu-nested-empty":
        (L / "outer").mkdir(); (L / "outer" / "inner").mkdir()
    stamp_all(L); stamp_all(R)


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4d-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    installs = inst_mod.discover()
    cur, ref = installs["current"], installs["reference"]
    if not cur.enabled:
        raise SystemExit(cur.disabled_reason)
    print(f"current   : {cur.oracle_path} ({cur.oracle_version})")
    print(f"reference : {ref.oracle_path} ({ref.oracle_version})" if ref.enabled else "reference: disabled")

    records = []
    for name, criteria, desc in CASES:
        root = run_dir / "fixtures" / name
        build(name, root)
        L, R = root / "L", root / "R"
        installs_to_run = [("current", cur)]
        if name == "size-big" and ref.enabled:
            installs_to_run.append(("reference", ref))
        for label, inst in installs_to_run:
            out = run_dir / "reports" / f"{name}-{label}.xml"
            lines = []
            if criteria:
                lines.append(f"criteria {criteria}")
            lines += [f'load "{L}" "{R}"', "expand all",
                      f'folder-report layout:xml output-to:"%3"']
            script = orc.write_script(run_dir / "reports" / f"{name}-{label}.bcs", lines)
            run = orc.run(inst.oracle_path, script, L, R, out,
                          timeout=180.0, script_text="\n".join(lines))
            body = out.read_bytes().decode("utf-8-sig", errors="replace") if run.report_exists else ""
            statuses = re.findall(r'<(?:file|folder)comp(?: status="([a-z]+)")?>', body)
            sizes = re.findall(r"<size>([^<]*)</size>|<size/>", body)
            foldercomp_no_status = len(re.findall(r"<foldercomp>\s*\n\s*<(?:lt|rt)>", body))
            records.append({"probe": name, "install": label, "criteria": criteria,
                            "exit": run.exit_code, "bytes": len(body),
                            "statuses": statuses, "sizes": sizes,
                            "foldercomp_without_status": foldercomp_no_status})
            print(f"  {name:<28} {label:<9} exit={run.exit_code} statuses={statuses} sizes={sizes} nostatus={foldercomp_no_status}")

    (run_dir / "u4d-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4d-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
