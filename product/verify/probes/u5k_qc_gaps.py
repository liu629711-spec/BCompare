#!/usr/bin/env python3
"""U5k probe -- the two /qc cells u5b left unmeasured.

u5b measured 14 /qc cells and produced the full level set (1/2/11/12/13/100).
Two cells that a `reacmp /qc` implementation would be *asked* to produce were
not among them:

  * `/qc=size` on two files with EQUAL size but DIFFERENT bytes.  Is a size
    comparison "binary same" (1) because sizes match, or does it read the
    bytes and say 11?
  * `/qc=crc` on two zero-byte files (identical) -- control for "empty file"
    handling.
  * `/qc` (rules) on two files that differ only in a line's **leading
    indentation**, which M2's importance engine calls important, versus
    **trailing whitespace**, which is unimportant.  This separates "rules
    verdict = similar" from "rules verdict = same" for the two whitespace
    kinds and is the last input the /qc mapping needs.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u5k_qc_gaps.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402


def run_raw(oracle, args: list[str], *, timeout: float = 120.0) -> tuple[int, str]:
    cmd = [str(oracle), "/silent", *args]
    with orc.ProcessTree() as tree:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(pathlib.Path(oracle).parent),
            creationflags=orc._CREATE_SUSPENDED if tree.enabled else 0,
        )
        tree.assign(proc)
        if tree.enabled:
            orc._resume(proc)
        try:
            _, raw_err = proc.communicate(timeout=timeout)
            return proc.returncode, raw_err.decode("utf-8", errors="replace")[:200]
        except subprocess.TimeoutExpired:
            tree.kill_tree()
            proc.kill()
            try:
                _, raw_err = proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                raw_err = b""
            return -1, raw_err.decode("utf-8", errors="replace")[:200]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u5k-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    blobs = {
        "eq-size-A.bin": b"AAAABBBB",
        "eq-size-B.bin": b"CCCCDDDD",          # same length, different bytes
        "empty-1.bin": b"",
        "empty-2.bin": b"",
        "indent-L.py": b"def f():\n    return 1\n",
        "indent-R.py": b"def f():\n        return 1\n",   # indentation differs
        "trail-L.py": b"x = 1   \n",
        "trail-R.py": b"x = 1\n",                          # trailing ws differs
        "indent-3sp-L.c": b"int main() {\n   int a;\n}\n",
        "indent-3sp-R.c": b"int main() {\n  int a;\n}\n",
    }
    for name, blob in blobs.items():
        (fx / name).write_bytes(blob)

    records: list[dict] = []

    def qc(tag: str, kind: str | None, left: str, right: str) -> None:
        flag = f"/qc={kind}" if kind else "/qc"
        code, err = run_raw(inst.oracle_path,
                            [flag, str(fx / left), str(fx / right)])
        records.append({"tag": tag, "flag": flag, "left": left, "right": right,
                        "exit": code, "stderr": err.strip()})
        print(f"  {flag:<12} {tag:<28} exit={code}")

    qc("eq-size-diff-bytes", "size", "eq-size-A.bin", "eq-size-B.bin")
    qc("eq-size-diff-bytes-crc", "crc", "eq-size-A.bin", "eq-size-B.bin")
    qc("empty-pair", "crc", "empty-1.bin", "empty-2.bin")
    qc("empty-pair-rules", None, "empty-1.bin", "empty-2.bin")
    qc("indent-only-py", None, "indent-L.py", "indent-R.py")
    qc("trailing-ws-py", None, "trail-L.py", "trail-R.py")
    qc("indent-3v2-c", None, "indent-3sp-L.c", "indent-3sp-R.c")

    (run_dir / "u5k-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u5k-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
