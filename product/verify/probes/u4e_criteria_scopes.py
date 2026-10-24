#!/usr/bin/env python3
"""U4e probe -- replace-vs-add for the inert trio, version combos, and the real
scope of folder `ignore-unimportant`.

Open after U4d:

  * do owner/group/permissions REPLACE the default size+timestamp (probe:
    equal files, differing SIZE, with the token)?
  * `version size` on equal-version different-size files: is size active?
  * `attrib:h version` combined.
  * folder `ignore-unimportant`: does it fold a `rules-based` FILE row whose
    only differences are unimportant (comments/whitespace), and what does the
    row look like without the token?

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4e_criteria_scopes.py
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


#: (name, criteria, left spec, right spec).  Specs: dict name->bytes, or a
#: special marker "pad2048" meaning append 2048 zero bytes to the left file.
CASES = [
    ("perm-size-differs", "permissions", {"a.bin": b"0123456789"}, {"a.bin": b"0123456789" + b"\x00" * 2048}),
    ("owner-size-differs", "owner", {"a.bin": b"0123456789"}, {"a.bin": b"0123456789" + b"\x00" * 2048}),
    ("group-size-differs", "group", {"a.bin": b"0123456789"}, {"a.bin": b"0123456789" + b"\x00" * 2048}),
    ("version-size-equal-vers", "version size", {"a.dll": b"PLAINBYTES"}, {"a.dll": b"PLAINBYTES"}),
    ("attrib-h-plus-version", "attrib:h version", {"a.dll": b"PLAINBYTES"}, {"a.dll": b"PLAINBYTES"}),
    ("rb-comment-only", "rules-based", {"t.c": b"int x; // old\n"}, {"t.c": b"int x; // new\n"}),
    ("rb-comment-only-iu", "rules-based ignore-unimportant", {"t.c": b"int x; // old\n"}, {"t.c": b"int x; // new\n"}),
    ("rb-real-diff-iu", "rules-based ignore-unimportant", {"t.c": b"int x = 1;\n"}, {"t.c": b"int x = 2;\n"}),
    ("rb-identical-iu", "rules-based ignore-unimportant", {"t.c": b"int x;\n"}, {"t.c": b"int x;\n"}),
    ("rb-comment-size-equal-ts-equal", "rules-based", {"t.c": b"int x; // old\n"}, {"t.c": b"int x; // new\n"}),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4e-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    records = []
    for name, criteria, lspec, rspec in CASES:
        root = run_dir / "fixtures" / name
        L, R = root / "L", root / "R"
        fresh(root); L.mkdir(); R.mkdir()
        for side, spec in ((L, lspec), (R, rspec)):
            for rel, data in spec.items():
                (side / rel).write_bytes(data)
        if name == "attrib-h-plus-version":
            # Left file hidden, right not: attributes must show up if attrib
            # is still active alongside version.
            import subprocess
            subprocess.run(["attrib", "+h", str(L / "a.dll")], capture_output=True)
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
        statuses = re.findall(r'<filecomp status="([a-z]+)">', body)
        sizes = re.findall(r"<size>([^<]*)</size>", body)
        records.append({"probe": name, "criteria": criteria, "exit": run.exit_code,
                        "statuses": statuses, "sizes": sizes, "bytes": len(body)})
        print(f"  {name:<30} exit={run.exit_code} statuses={statuses} sizes={sizes}")

    (run_dir / "u4e-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4e-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
