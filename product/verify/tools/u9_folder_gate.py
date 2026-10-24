#!/usr/bin/env python3
"""U9/U10 gate -- the live-Oracle folder gate for the version mask and
`ignore-unimportant` scope.

Why a new gate rather than an edit of an old one
------------------------------------------------

`product/dir/fixtures/cases.json` is honest about its own provenance: its
expectations come from the reference model or from one archived Oracle artifact,
and it says so in `honesty_boundary` — "Neither is a measured BC parity claim."
So it cannot be evidence that the mask matches BC. Only a live Oracle run can,
and that is what this tool does.

What it covers
--------------

* The `versioned` tree pair, under `criteria version`, including the U9 mask rows
  (`masked.*` real PEs outside the gate, `included.vxd`/`included.386` inside it).
* The other criteria specs that touch the same code path, so the mask cannot fix
  `version` while breaking `size`/`timestamp`/`rules-based`.
* The U10 `ignore-unimportant` scope cases: structural rows (directories,
  one-sided files) under the modifier, and the folding combination.

Verdict
-------

For each case: run the Oracle and the product on the same trees with the same
script, normalize both reports, and require them to be **equal**. Exit codes must
also agree. A case that differs is a failure — the corpus rows are the ones U9/U10
measured, so a difference here is a real divergence, not a tolerance.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python tools/u9_folder_gate.py
    python tools/u9_folder_gate.py --list
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
VERIFY = REA / "product" / "verify"
sys.path.insert(0, str(VERIFY))

from harness import installs as inst_mod  # noqa: E402
from harness import normalize as norm_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
TREES = REA / "product" / "dir" / "fixtures" / "trees"
FIXED_MTIME = 1_767_225_600

#: (case name, tree pair, criteria line, why it is here)
CASES: list[tuple[str, str, str, str]] = [
    ("version-default-mask", "versioned", "criteria version",
     "the mask rows: masked.* must be `same`, included.vxd/.386 compared"),
    ("version-with-size", "versioned", "criteria version size",
     "the mask must not disturb the working token combination"),
    ("version-only-equal", "versioned", "criteria version",
     "control: equal-versions row must stay `same`"),
    ("size-default", "versioned", "criteria size",
     "size still works (the mask must not gate non-version criteria)"),
    ("timestamp-default", "versioned", "criteria timestamp",
     "timestamp still works"),
    ("rules-based", "rules-based", "criteria rules-based",
     "rules-based still works"),
    ("crc", "rules-based", "criteria crc",
     "crc still works"),
    ("default-pair", "versioned", "",
     "no criteria line: the default size+timestamp pair"),

    # --- U10: `ignore-unimportant` scope on structural rows ---
    ("iu-onesided", "iu-onesided", "ignore-unimportant",
     "one-sided file rows are not foldable; directory rows carry no status"),
    ("iu-onesided-default", "iu-onesided", "",
     "the same rows under the default pair (attribution control)"),
    ("iu-emptydirs", "iu-emptydirs", "ignore-unimportant",
     "empty / one-sided / nested directory rows"),
    ("iu-emptydirs-default", "iu-emptydirs", "",
     "the same directory rows under the default pair"),
    ("iu-foldable-alone", "iu-foldable", "ignore-unimportant",
     "the modifier alone names no comparison, so nothing folds"),
    ("iu-foldable-rb", "iu-foldable", "ignore-unimportant rules-based",
     "the combination that folds comment-only differences"),
    ("iu-foldable-rb-reversed", "iu-foldable", "rules-based ignore-unimportant",
     "token order must not matter"),
    ("iu-foldable-rb-only", "iu-foldable", "criteria rules-based",
     "rules-based alone, so folding is attributable"),
    ("iu-control-alone", "iu-control", "ignore-unimportant",
     "real content differences under the modifier alone"),
    ("iu-control-rb", "iu-control", "ignore-unimportant rules-based",
     "real content differences under the folding combination"),
]

#: U10's trees, built by this tool rather than committed as fixtures: they exist
#: to answer a scope question, and keeping them here makes the question and the
#: answer live in one file. `None` means "a directory".
IU_TREES: dict[str, dict[str, dict[str, object]]] = {
    "iu-onesided": {
        "L": {"only_left.txt": b"left only\r\n", "shared.txt": b"same\r\n"},
        "R": {"only_right.txt": b"right only\r\n", "shared.txt": b"same\r\n"},
    },
    "iu-emptydirs": {
        "L": {"empty_left": None, "empty_both": None, "nest": None,
              "nest/inner": None},
        "R": {"empty_right": None, "empty_both": None, "nest": None},
    },
    "iu-foldable": {
        "L": {"comment.c": b"int x; // old note\r\n",
              "real.c": b"int x = 1;\r\n",
              "sub/comment.c": b"// only a comment\r\n",
              "sub/real.c": b"int y = 2;\r\n",
              "same.c": b"int z;\r\n"},
        "R": {"comment.c": b"int x; // new note\r\n",
              "real.c": b"int x = 2;\r\n",
              "sub/comment.c": b"// a different comment\r\n",
              "sub/real.c": b"int y = 3;\r\n",
              "same.c": b"int z;\r\n"},
    },
    "iu-control": {
        "L": {"a.txt": b"alpha\r\n", "b.txt": b"gamma\r\n"},
        "R": {"a.txt": b"beta\r\n", "b.txt": b"gamma\r\n"},
    },
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--filter", default=None)
    args = ap.parse_args()

    if args.list:
        for name, tree, crit, why in CASES:
            print(f"  {name:<22} {tree:<14} {crit or '(default)':<22} {why}")
        return 0

    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u9-gate-%Y%m%dT%H%M%SZ"))
    (run_dir / "oracle").mkdir(parents=True, exist_ok=True)
    (run_dir / "product").mkdir(parents=True, exist_ok=True)
    # Work on copies so the committed fixtures are never touched by a run.
    work = run_dir / "trees"
    shutil.copytree(TREES, work)
    # Materialise the U10 trees, with the right side's directories a later mtime
    # so a structural row that compared timestamps would be visible.
    for tree, sides in IU_TREES.items():
        for side, entries in sides.items():
            root = work / tree / side
            root.mkdir(parents=True, exist_ok=True)
            for rel, content in entries.items():
                p = root / rel
                if content is None:
                    p.mkdir(parents=True, exist_ok=True)
                else:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(content)  # type: ignore[arg-type]
        for side, extra in (("L", 0), ("R", 7200)):
            root = work / tree / side
            if not root.exists():
                continue
            for p in sorted(root.rglob("*"), reverse=True):
                os.utime(p, (FIXED_MTIME + extra, FIXED_MTIME + extra))
            os.utime(root, (FIXED_MTIME + extra, FIXED_MTIME + extra))

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"product : {PRODUCT}")
    print(f"trees   : {work}\n")

    passed = failed = 0
    records: list[dict] = []
    for name, tree, crit, why in CASES:
        if args.filter and args.filter not in name:
            continue
        left, right = work / tree / "L", work / tree / "R"
        if not left.is_dir() or not right.is_dir():
            raise SystemExit(f"missing tree pair for {name}: {left} / {right}")

        # `criteria` MUST precede `load` (measured in the U4 series). The keyword
        # is added here when the case omits it, so the corpus can read naturally
        # (`ignore-unimportant rules-based`) without every entry repeating it.
        lines = []
        if crit:
            lines.append(crit if crit.startswith("criteria")
                         else f"criteria {crit}")
        lines += ['load "%1" "%2"', "expand all",
                  'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "oracle" / f"{name}.bcs", lines)

        o_out = run_dir / "oracle" / f"{name}.xml"
        run = orc.run(inst.oracle_path, script, str(left), str(right), o_out,
                      timeout=180.0, script_text="\n".join(lines))

        p_out = run_dir / "product" / f"{name}.xml"
        proc = subprocess.run(
            [str(PRODUCT), "@" + str(script), str(left), str(right), str(p_out)],
            capture_output=True, timeout=120)

        detail = ""
        ok = False
        o_ok = o_out.exists() and o_out.stat().st_size > 0
        p_ok = p_out.exists() and p_out.stat().st_size > 0
        if not o_ok or not p_ok:
            detail = f"missing report (oracle={o_ok} product={p_ok})"
        else:
            try:
                o_norm = norm_mod.normalize(
                    norm_mod.read_report(o_out), path=str(o_out)).text
                p_norm = norm_mod.normalize(
                    norm_mod.read_report(p_out), path=str(p_out)).text
                ok = o_norm == p_norm
                if not ok:
                    ol, pl = o_norm.splitlines(), p_norm.splitlines()
                    for i in range(max(len(ol), len(pl))):
                        a = ol[i] if i < len(ol) else "<none>"
                        b = pl[i] if i < len(pl) else "<none>"
                        if a != b:
                            detail = (f"line {i + 1}: oracle={a.strip()[:70]!r} "
                                      f"product={b.strip()[:70]!r}")
                            break
            except Exception as exc:  # noqa: BLE001 -- report, never hide
                detail = f"normalize/compare failed: {exc}"

        if ok and run.exit_code == proc.returncode:
            passed += 1
            mark = "OK  "
        else:
            failed += 1
            mark = "FAIL"
            if ok:
                detail = (f"exit: oracle={run.exit_code} "
                          f"product={proc.returncode}")

        records.append({"name": name, "tree": tree, "criteria": crit,
                        "why": why, "pass": ok,
                        "oracle_exit": run.exit_code,
                        "product_exit": proc.returncode, "detail": detail})
        print(f"  {mark} {name:<22} {crit or '(default)':<22} "
              f"oracle={run.exit_code:<4} product={proc.returncode:<4}"
              + (f"  {detail}" if detail else ""))

    print(f"\n{passed}/{passed + failed} passed, {failed} failed")
    (run_dir / "u9-gate.json").write_text(
        json.dumps({"oracle": {"path": str(inst.oracle_path),
                               "version": inst.oracle_version},
                    "product": str(PRODUCT),
                    "passed": passed, "failed": failed, "records": records},
                   ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"raw: {run_dir / 'u9-gate.json'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
