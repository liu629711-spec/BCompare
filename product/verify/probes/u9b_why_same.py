#!/usr/bin/env python3
"""U9b probe -- why did BC report `same` for every extension in U9?

U9 asked whether `criteria version` gates on the file name, and got a surprising
answer: BC reported `same` for **all 24** names, including `.exe` and `.dll`,
while the product reported `ltnewer` for all of them. Both readings cannot be
about the name mask, because the existing M3 gate passes a `versioned` tree whose
`left_higher.dll` / `right_higher.dll` rows BC does report as `ltnewer`/`rtnewer`.

Something about U9's fixture differs from the working one. The candidates, all
checkable:

1. **Identical sizes.**  U9 gave both sides the same-size blob (only the version
   fields patched). The working `versioned` tree pairs files of *different*
   sizes for the directional rows. If BC short-circuits an identical-size,
   identical-mtime pair, `criteria version` would never be consulted — which
   would make U9 measure the shortcut, not the mask.

2. **Identical mtimes.**  U9 wrote both sides in the same instant, so the
   timestamps match to the second. The working tree pins mtimes.

3. **Missing size token.**  Every U9 row had `criteria version` alone. The
   working `crit-version-size` case uses `version size`.

4. **The base PE.**  U9 patched `version.dll` (as u4h established). The working
   tree patches the same file, so this is unlikely but cheap to include.

This probe separates them by varying one factor at a time, all with the **same
extension question implicit**: whatever makes BC compare a version, it is asked
on `.dll` (known comparable) and on `.txt` (the actual question).

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u9b_why_same.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import struct
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"
VERSION_BASE_PE = pathlib.Path("C:/Windows/System32/version.dll")

#: A fixed instant for fixture mtimes (matching the harness convention), so a
#: timestamp difference cannot be mistaken for a version difference.
FIXED_MTIME = 1_767_225_600


def pe_blob(fv: tuple[int, int, int, int]) -> bytes:
    data = bytearray(VERSION_BASE_PE.read_bytes())
    sig = (0xFEEF04BD).to_bytes(4, "little")
    i = data.find(sig)
    if i < 0:
        raise SystemExit(f"{VERSION_BASE_PE} has no VS_FIXEDFILEINFO")
    struct.pack_into("<I", data, i + 8, (fv[0] << 16) | fv[1])
    struct.pack_into("<I", data, i + 12, (fv[2] << 16) | fv[3])
    struct.pack_into("<I", data, i + 16, (9 << 16) | 9)
    struct.pack_into("<I", data, i + 20, (9 << 16) | 9)
    return bytes(data)


#: tag -> (criteria line, left extra suffix, right extra suffix, mtime delta,
#:          purpose)
SCENARIOS: dict[str, tuple[str, bytes, bytes, int, str]] = {
    "u9-repro": ("criteria version", b"", b"", 0,
                 "U9 as measured: same size, same mtime, version only"),
    "size-differs": ("criteria version", b"", b"\x00" * 8, 0,
                     "sizes differ (the working tree's shape)"),
    "mtime-differs": ("criteria version", b"", b"", 3600,
                      "same size, mtimes an hour apart"),
    "version-and-size": ("criteria version size", b"", b"\x00" * 8, 0,
                         "the working case's token set"),
    "content-truncated": ("criteria version", b"", b"", 0,
                          "right side is not a PE at all"),
    "default-criteria": ("", b"", b"\x00" * 8, 0,
                         "no criteria line: the default pair, as a control"),
}

#: The extension question, asked on the two names that bracket it.
NAMES = ["probe.dll", "probe.txt"]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u9b-probe-%Y%m%dT%H%M%SZ"))
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"base PE : {VERSION_BASE_PE}")
    print(f"fixed mtime: {FIXED_MTIME}\n")

    records: list[dict] = []
    for tag, (crit, lsuf, rsuf, mdt, purpose) in SCENARIOS.items():
        fx = run_dir / "fixtures" / tag
        left, right = fx / "L", fx / "R"
        left.mkdir(parents=True, exist_ok=True)
        right.mkdir(parents=True, exist_ok=True)
        for name in NAMES:
            if tag == "content-truncated":
                (left / name).write_bytes(pe_blob((2, 0, 0, 0)))
                (right / name).write_bytes(b"not a pe at all\r\n")
            else:
                (left / name).write_bytes(pe_blob((2, 0, 0, 0)) + lsuf)
                (right / name).write_bytes(pe_blob((1, 0, 0, 0)) + rsuf)
            # Pin both sides, then shift the right side when the scenario asks.
            os.utime(left / name, (FIXED_MTIME, FIXED_MTIME))
            os.utime(right / name, (FIXED_MTIME + mdt, FIXED_MTIME + mdt))

        # `criteria` MUST precede `load`: measured in the U4 series (u4j/u4k, and
        # the working recipe in `U4-FINDINGS.md`), a `criteria` line after `load`
        # does not take effect for the report. Getting this wrong produced the
        # false "BC compares nothing" reading that prompted this probe.
        lines = []
        if crit:
            lines.append(crit)
        lines += ['load "%1" "%2"', "expand all",
                  'folder-report layout:xml output-to:"%3"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        run = orc.run(inst.oracle_path, script, str(left), str(right), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = ""
        if run.report_exists and run.report_bytes:
            o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        p_out = run_dir / "reports" / f"{tag}.product.xml"
        proc = subprocess.run([str(PRODUCT), "@" + str(script), str(left),
                               str(right), str(p_out)],
                              capture_output=True, timeout=120)
        p_body = ""
        if p_out.exists():
            p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

        def per_name(body: str) -> dict[str, str]:
            out: dict[str, str] = {}
            for m in re.finditer(r"<filecomp([^>]*)>(.*?)</filecomp>", body, re.S):
                st = re.search(r'status="([a-z]+)"', m.group(1))
                nm = re.search(r"<name>(.*?)</name>", m.group(2))
                if nm:
                    out[nm.group(1)] = st.group(1) if st else "?"
            return out

        o_s, p_s = per_name(o_body), per_name(p_body)
        agreements = sum(1 for n in NAMES if o_s.get(n) == p_s.get(n))
        records.append({"tag": tag, "criteria": crit or "(default)",
                        "purpose": purpose,
                        "oracle": o_s, "product": p_s,
                        "agree": agreements, "of": len(NAMES)})
        print(f"  {tag:<20} oracle={o_s}  product={p_s}  "
              f"({agreements}/{len(NAMES)})")

    (run_dir / "u9b-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u9b-results.json'}")

    print("\n=== which factor makes BC compare the version? ===")
    for r in records:
        dll = r["oracle"].get("probe.dll", "-")
        txt = r["oracle"].get("probe.txt", "-")
        verdict = ("compares" if dll in ("ltnewer", "rtnewer", "diff")
                   else "same")
        print(f"  {r['tag']:<20} {r['criteria']:<22} "
              f"dll={dll:<10} txt={txt:<10} -> {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
