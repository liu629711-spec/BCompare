#!/usr/bin/env python3
"""U4h probe -- two gate-round-5 disagreements.

`A3-folder-gate-serial-05` measured two hard failures:

  1. **crit-version-equal**: a synthetic blob carrying only the
     VS_FIXEDFILEINFO signature (no PE header, no resource directory) makes the
     Oracle report `same` for ALL dll rows, while the engine read a version and
     reported direction.  Hypothesis: the Oracle requires a well-formed PE with
     a real resource directory, and treats our synthetic blob as
     version-less -- which would mean the synthetic fixtures are the problem,
     not the engine's reader.
  2. **crit-ignore-unimportant-alone**: `criteria ignore-unimportant` reports
     `same` for EVERY row, including `real_change.c` whose content genuinely
     differs.  That is not "fold unimportant differences"; it looks like the
     token alone leaves NO content comparison active (so only the default,
     already-equal quick tests run) -- i.e. it really is a pure modifier.

This probe settles both: (a) a real system DLL vs the synthetic blob under
`version`, and (b) `ignore-unimportant` alone vs `ignore-unimportant
rules-based` on a pair with a real content difference.

Usage:
    cd D:\\Rea\\product\\verify
    python probes/u4h_version_pe_and_iu_alone.py
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

SYNTH_SIG = (0xFEEF04BD).to_bytes(4, "little")


def synth_blob(fv, pv) -> bytes:
    ms = (fv[0] << 16) | fv[1]
    ls = (fv[2] << 16) | fv[3]
    pms = (pv[0] << 16) | pv[1]
    pls = (pv[2] << 16) | pv[3]
    out = bytearray(b"MZ" + b"\x00" * 62)
    out += SYNTH_SIG
    out += (0x00010000).to_bytes(4, "little")
    out += ms.to_bytes(4, "little")
    out += ls.to_bytes(4, "little")
    out += pms.to_bytes(4, "little")
    out += pls.to_bytes(4, "little")
    return bytes(out)


def real_pe_with_patched_version(src: bytes, lo: int) -> bytes:
    out = bytearray(src)
    i = out.find(SYNTH_SIG)
    if i < 0:
        raise SystemExit("source PE has no VS_FIXEDFILEINFO")
    import struct
    struct.pack_into("<H", out, i + 8, lo)  # low word of FileVersionMS
    return bytes(out)


CASES = [
    ("synth-equal", "version", "synth", "synth"),
    ("synth-left-higher", "version", "synth_hi", "synth"),
    ("synth-right-higher", "version", "synth", "synth_hi"),
    ("real-equal", "version", "real", "real"),
    ("real-left-higher", "version", "real_hi", "real"),
    ("real-right-higher", "version", "real", "real_hi"),
    ("real-one-sided", "version", "real", "real_txt"),
    ("iu-alone-real-diff", "ignore-unimportant", "c1", "c2"),
    ("iu-alone-identical", "ignore-unimportant", "c1", "c1"),
    ("iu-rb-real-diff", "ignore-unimportant rules-based", "c1", "c2"),
    ("iu-alone-size-diff", "ignore-unimportant", "big", "small"),
    ("iu-alone-timestamp", "ignore-unimportant", "ts1", "ts2"),
]


def build(kind: str, dst: pathlib.Path, real: bytes) -> None:
    if kind == "synth":
        dst.write_bytes(synth_blob((1, 2, 3, 4), (1, 2, 3, 4)))
    elif kind == "synth_hi":
        dst.write_bytes(synth_blob((9, 9, 9, 9), (9, 9, 9, 9)))
    elif kind == "real":
        dst.write_bytes(real)
    elif kind == "real_hi":
        dst.write_bytes(real_pe_with_patched_version(real, 1))
    elif kind == "real_txt":
        dst.write_bytes(b"not a pe\r\n")
    elif kind == "c1":
        dst.write_bytes(b"int x = 1;\r\n")
    elif kind == "c2":
        dst.write_bytes(b"int x = 2;\r\n")
    elif kind == "big":
        dst.write_bytes(b"A" * 4096)
    elif kind == "small":
        dst.write_bytes(b"A" * 16)
    elif kind == "ts1":
        dst.write_bytes(b"same\r\n")
    elif kind == "ts2":
        dst.write_bytes(b"same\r\n")


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u4h-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle : {inst.oracle_path} ({inst.oracle_version})")

    real = pathlib.Path(r"C:\Windows\System32\version.dll").read_bytes()
    records = []
    for name, criteria, lk, rk in CASES:
        root = run_dir / "fixtures" / name
        if root.exists():
            shutil.rmtree(root)
        L, R = root / "L", root / "R"
        L.mkdir(parents=True)
        R.mkdir(parents=True)
        fname = "a.dll" if "synth" in lk or "real" in lk else "a.txt"
        build(lk, L / fname, real)
        build(rk, R / fname, real)
        if name == "iu-alone-timestamp":
            import os
            fixed = 1_767_225_600
            os.utime(L / fname, (fixed, fixed))
            os.utime(R / fname, (fixed + 7200, fixed + 7200))
        for side in (L, R):
            import os
            for p in side.rglob("*"):
                os.utime(p, (1_767_225_600, 1_767_225_600))
            os.utime(side, (1_767_225_600, 1_767_225_600))

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
        rows = {}
        for status, chunk in re.findall(r'<filecomp status="([a-z]+)">(.*?)</filecomp>', body, re.S):
            for nm in re.findall(r"<name>([^<]*)</name>", chunk):
                rows.setdefault(nm, status)
        records.append({"probe": name, "criteria": criteria, "exit": run.exit_code,
                        "rows": rows})
        print(f"  {name:<22} crit={criteria or '(default)':<32} {json.dumps(rows)}")

    (run_dir / "u4h-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u4h-results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
