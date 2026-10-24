#!/usr/bin/env python3
"""U10 probe -- folder `ignore-unimportant` on directory and one-sided rows.

`product/docs/08-folder-criteria.md` §已知差异 4 records this as observed but
unanchored:

> 文件夹 `ignore-unimportant` 对**目录行/单侧行**的影响已在 u4d 观察（结构行不受
> 影响），但未建锚点——如需覆盖可加一组 `iu-*` 用例。

An observation without an anchor cannot fail, so it cannot protect anything. This
probe turns it into a comparison: the same trees under `ignore-unimportant`, run
through the Oracle and the product, with the two reports required to match.

It also asks the questions u4d left open, because a structural row's handling of
a *content* modifier is the part most likely to be wrong:

A. **One-sided rows.**  A file present on one side only cannot be "unimportant"
   — there is nothing to compare it against. Measured in u4d as `ltonly`; this
   probe confirms it and checks the product agrees.

B. **Empty directories.**  Left-only, right-only, and both-sides-empty with
   differing mtimes. Under the default pair an mtime difference would show; under
   `ignore-unimportant` alone nothing is compared, so all should be `same` — but
   a directory has no content, so the modifier has nothing to fold either.

C. **`ignore-unimportant rules-based`** — the combination that actually folds.
   A tree with comment-only (foldable) and real (not foldable) differences,
   including a **directory** whose only difference is a foldable file, to see
   whether a directory row's status is derived from its children.

D. **The default pair as a control**, so a `same` reading cannot be attributed to
   the modifier when the default would say `same` anyway.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u10_folder_iu_scope.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import normalize as norm_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
FIXED_MTIME = 1_767_225_600


def freeze(root: pathlib.Path, offsets: dict[str, int] | None = None) -> None:
    """Pin mtimes so a timestamp difference cannot be mistaken for a content one."""
    offsets = offsets or {}
    for p in sorted(root.rglob("*"), reverse=True):
        rel = p.relative_to(root).as_posix()
        t = FIXED_MTIME + offsets.get(rel, 0)
        os.utime(p, (t, t))
    os.utime(root, (FIXED_MTIME, FIXED_MTIME))


#: tree name -> {side: {relative path: contents or None for a directory}}
TREES: dict[str, dict[str, dict[str, object]]] = {
    # A: one-sided rows.
    "onesided": {
        "L": {"only_left.txt": b"left only\r\n",
              "shared.txt": b"same\r\n"},
        "R": {"only_right.txt": b"right only\r\n",
              "shared.txt": b"same\r\n"},
    },
    # B: empty directories, including one-sided and nested.
    "emptydirs": {
        "L": {"empty_left": None, "empty_both": None,
              "nest": None, "nest/inner": None},
        "R": {"empty_right": None, "empty_both": None,
              "nest": None},
    },
    # C: foldable vs real content differences, including inside a directory.
    "foldable": {
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
    # D: control -- content differs in ways that are plain, not unimportant.
    "control": {
        "L": {"a.txt": b"alpha\r\n", "b.txt": b"gamma\r\n"},
        "R": {"a.txt": b"beta\r\n", "b.txt": b"gamma\r\n"},
    },
}

#: (tag, tree, criteria line, what it asks)
CASES: list[tuple[str, str, str, str]] = [
    ("iu-onesided", "onesided", "ignore-unimportant",
     "one-sided file rows cannot be folded"),
    ("iu-onesided-default", "onesided", "",
     "the same rows under the default pair (control)"),
    ("iu-emptydirs", "emptydirs", "ignore-unimportant",
     "empty/one-sided/nested directory rows"),
    ("iu-emptydirs-default", "emptydirs", "",
     "the same directory rows under the default pair"),
    ("iu-foldable", "foldable", "ignore-unimportant",
     "the modifier alone: measured to compare nothing"),
    ("iu-foldable-rb", "foldable", "ignore-unimportant rules-based",
     "the combination that folds comment-only differences"),
    ("iu-foldable-rb-nested", "foldable", "rules-based ignore-unimportant",
     "token order must not matter"),
    ("rb-only", "foldable", "criteria rules-based",
     "rules-based alone, so folding can be attributed"),
    ("iu-control", "control", "ignore-unimportant",
     "real content differences under the modifier alone"),
    ("iu-control-rb", "control", "ignore-unimportant rules-based",
     "real content differences under the folding combination"),
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u10-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    (run_dir / "oracle").mkdir(parents=True, exist_ok=True)
    (run_dir / "product").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"product : {PRODUCT}\n")

    # Materialise the trees.
    for tree, sides in TREES.items():
        for side, entries in sides.items():
            root = fx / tree / side
            root.mkdir(parents=True, exist_ok=True)
            for rel, content in entries.items():
                p = root / rel
                if content is None:
                    p.mkdir(parents=True, exist_ok=True)
                else:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(content)  # type: ignore[arg-type]
        # The right side's directories carry a later mtime, so a directory row
        # that compares timestamps would be visible.
        freeze(fx / tree / "L")
        freeze(fx / tree / "R", {"": 7200} if tree == "emptydirs" else None)
        os.utime(fx / tree / "R", (FIXED_MTIME + 7200, FIXED_MTIME + 7200))

    records: list[dict] = []
    passed = failed = 0
    for tag, tree, crit, purpose in CASES:
        left, right = fx / tree / "L", fx / tree / "R"
        lines = []
        if crit:
            lines.append(crit if crit.startswith("criteria") else f"criteria {crit}")
        lines += ['load "%1" "%2"', "expand all",
                  'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "oracle" / f"{tag}.bcs", lines)

        o_out = run_dir / "oracle" / f"{tag}.xml"
        run = orc.run(inst.oracle_path, script, str(left), str(right), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = ""
        if run.report_exists and run.report_bytes:
            o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        p_out = run_dir / "product" / f"{tag}.xml"
        proc = subprocess.run(
            [str(PRODUCT), "@" + str(script), str(left), str(right), str(p_out)],
            capture_output=True, timeout=120)
        p_body = ""
        if p_out.exists():
            p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

        def rows(body: str) -> list[tuple[str, str]]:
            """(kind, status) per row, kind = directory or file."""
            out = []
            for m in re.finditer(
                    r"<(foldercomp|filecomp)([^>]*)>(.*?)</\1>", body, re.S):
                st = re.search(r'status="([a-z]+)"', m.group(2))
                has_size = "<size" in m.group(3)
                kind = "dir" if (m.group(1) == "foldercomp"
                                 or (has_size and False)) else "file"
                out.append((kind, st.group(1) if st else "-"))
            return out

        o_norm = norm_mod.normalize(o_body, path=str(o_out)).text if o_body else ""
        p_norm = norm_mod.normalize(p_body, path=str(p_out)).text if p_body else ""
        same = bool(o_body and p_body) and o_norm == p_norm
        detail = ""
        if not same:
            if not o_body or not p_body:
                detail = f"missing report (oracle={bool(o_body)} product={bool(p_body)})"
            else:
                for i, (a, b) in enumerate(zip(o_norm.splitlines(),
                                               p_norm.splitlines())):
                    if a != b:
                        detail = f"line {i+1}: {a.strip()[:60]!r} vs {b.strip()[:60]!r}"
                        break
        if same and run.exit_code == proc.returncode:
            passed += 1
            mark = "OK  "
        else:
            failed += 1
            mark = "FAIL"

        records.append({"tag": tag, "tree": tree, "criteria": crit or "(default)",
                        "purpose": purpose, "pass": same,
                        "oracle_exit": run.exit_code,
                        "product_exit": proc.returncode,
                        "oracle_body": o_body, "product_body": p_body,
                        "detail": detail})
        print(f"  {mark} {tag:<24} {crit or '(default)':<34} "
              f"oracle={run.exit_code} product={proc.returncode}"
              + (f"  {detail}" if detail else ""))

    (run_dir / "u10-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{passed}/{passed + failed} passed, {failed} failed")
    print(f"raw: {run_dir / 'u10-results.json'}")

    print("\n=== what the Oracle does on structural rows (the u4d questions) ===")
    for r in records:
        if "onesided" in r["tag"] or "emptydir" in r["tag"]:
            body = r["oracle_body"]
            n_folder = body.count("<foldercomp")
            n_file = body.count("<filecomp")
            statuses = re.findall(r'<(?:folder|file)comp status="([a-z]+)"', body)
            nostatus = re.findall(r"<(?:folder|file)comp>", body)
            print(f"  {r['tag']:<24} foldercomp={n_folder} filecomp={n_file} "
                  f"statuses={statuses} rows-without-status={len(nostatus)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
