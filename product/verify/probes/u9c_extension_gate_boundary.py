#!/usr/bin/env python3
"""U9c probe -- the exact boundary of the `version` extension gate.

U9/U9b measured that BC compares a PE's version **only for some extensions**:

    compared : .exe .dll .ocx .scr .sys .drv
    ignored  : .cpl .efi .ax .tsp .olb .vbx .msi .com .txt .bin .dat
               .zip .html .xls, and a name with no extension

That list is not "every executable extension" (`.cpl` is a Control Panel applet
and a real PE; `.efi` is a PE) nor "every PE content" (the ignored names carried
real PE bytes). So the gate is a specific set, and implementing it needs that set
to be *complete* rather than "the ones I happened to try".

This probe closes the boundary:

A. **Additional plausible extensions** -- `.exe`-family names a mask might carry:
   `.pif .acm .ax .cpl .efi .tsp .olb .vbx .mun .rll .dll16 .exe16 .bin .elf .so
   .ocx16 .sbr .ime .fon .fnt .vxd .sys16 .prx .pyd .wll .ocx2`
   plus `.com .386 .vxd .mui .msp .msu .cab .hta .jse .vbs .wsf` (loader-ish).

B. **Name-shape edges** on a known-compared extension (`.exe`), because a mask
   implementation can differ from a suffix test here:
   * no extension at all (`readme`)              -- already measured: ignored
   * trailing dot (`prog.`)                      -- empty extension
   * double extension (`prog.tar.exe`)           -- the last one wins?
   * directory-like name (`my.directory/prog.exe`) -- a dot earlier in the path
   * a dot in a *directory* component only
   * uppercase / mixed case                      -- measured: case-insensitive
   * `.exe` as the whole name (`.exe`)           -- no stem
   * a very long name ending in `.exe`
   * a name whose extension contains the mask as a prefix (`.exe2`, `.dllx`)

C. **A second control on the content question**: `.exe` whose content is *not* a
   PE (already have `command.com`; add `.exe` with text content) -- U9b's
   `content-truncated` showed `.dll` still reads `ltnewer` when the right side is
   not a PE, and a non-PE `.dll` was measured `same` in the working tree's
   `one_sided.dll` row, so the name gate and the content requirement are separate
   conditions and both need confirming here.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u9c_extension_gate_boundary.py
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


#: Candidate extensions beyond the six already measured.
EXTRA_EXTS = [
    "pif", "acm", "cpl", "efi", "tsp", "olb", "vbx", "mun", "rll", "bin",
    "elf", "so", "sbr", "ime", "fon", "fnt", "vxd", "prx", "pyd", "wll",
    "com", "386", "mui", "msp", "msu", "cab", "hta", "jse", "vbs", "wsf",
    "exe2", "dllx", "EXE2", "sysx", "drv2", "ocx2", "scr2",
    # the six that were measured as compared, repeated as controls
    "exe", "dll", "ocx", "scr", "sys", "drv",
]

#: Name-shape probes.  Each entry is a relative path inside the fixture tree, so
#: a dotted *directory* component is expressible.  Every one of these carries a
#: real PE on both sides with different FileVersion, so a `same` reading means
#: the gate excluded it and a directional reading means it was compared.
SHAPE_NAMES = [
    "noext",
    "trailingdot.",
    "double.tar.exe",
    "dot.dir/prog.exe",
    "onlyext/.exe",
    "long" + "n" * 80 + ".exe",
    "dotnonexec.dir/prog.txt",
]


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u9c-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    left, right = fx / "L", fx / "R"
    for root in (left, right):
        root.mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})\n")

    newer, older = pe_blob((2, 0, 0, 0)), pe_blob((1, 0, 0, 0))

    # ---- A: extra extensions, plus one non-PE-content exe as a control ----
    for ext in EXTRA_EXTS:
        name = f"probe.{ext}"
        (left / name).write_bytes(newer)
        (right / name).write_bytes(older)
        os.utime(left / name, (FIXED_MTIME, FIXED_MTIME))
        os.utime(right / name, (FIXED_MTIME, FIXED_MTIME))
    # `.exe` carrying text: the name passes the gate, the content is not a PE.
    (left / "textonly.exe").write_bytes(newer)
    (right / "textonly.exe").write_bytes(b"this is plainly not a pe\r\n")
    for p in (left / "textonly.exe", right / "textonly.exe"):
        os.utime(p, (FIXED_MTIME, FIXED_MTIME))

    # ---- B: name shapes ----
    for rel in SHAPE_NAMES:
        lp, rp = left / rel, right / rel
        lp.parent.mkdir(parents=True, exist_ok=True)
        rp.parent.mkdir(parents=True, exist_ok=True)
        lp.write_bytes(newer)
        rp.write_bytes(older)
        os.utime(lp, (FIXED_MTIME, FIXED_MTIME))
        os.utime(rp, (FIXED_MTIME, FIXED_MTIME))

    # The fixed recipe order (criteria BEFORE load) -- see u9b's note.
    script_lines = [
        "criteria version",
        'load "%1" "%2"',
        "expand all",
        'folder-report layout:xml output-to:"%3"',
    ]
    script = orc.write_script(run_dir / "reports" / "u9c.bcs", script_lines)
    o_out = run_dir / "reports" / "u9c.oracle.xml"
    run = orc.run(inst.oracle_path, script, str(left), str(right), o_out,
                  timeout=180.0, script_text="\n".join(script_lines))
    o_body = ""
    if run.report_exists and run.report_bytes:
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

    p_out = run_dir / "reports" / "u9c.product.xml"
    proc = subprocess.run([str(PRODUCT), "@" + str(script), str(left),
                           str(right), str(p_out)],
                          capture_output=True, timeout=120)
    p_body = ""
    if p_out.exists():
        p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

    # The report lists paths relative to the compared roots, with `/` as the
    # separator; map by the final path component (or full relative path for the
    # dotted-directory cases, which would otherwise collide).
    def per_path(body: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for m in re.finditer(r"<filecomp([^>]*)>(.*?)</filecomp>", body, re.S):
            st = re.search(r'status="([a-z]+)"', m.group(1))
            nm = re.search(r"<name>(.*?)</name>", m.group(2))
            if nm:
                key = nm.group(1).replace("\\", "/").strip()
                out[key] = st.group(1) if st else "?"
        return out

    o_s, p_s = per_path(o_body), per_path(p_body)
    print(f"oracle exit={run.exit_code}  product exit={proc.returncode}")
    print(f"oracle entries={len(o_s)}  product entries={len(p_s)}\n")

    def lookup(table: dict[str, str], rel: str) -> str:
        rel = rel.replace("\\", "/")
        if rel in table:
            return table[rel]
        base = rel.rsplit("/", 1)[-1]
        hits = [v for k, v in table.items() if k.rsplit("/", 1)[-1] == base]
        return hits[0] if len(hits) == 1 else ("?" if not hits else "ambig")

    print("=== A. extension gate ===")
    records = []
    for ext in EXTRA_EXTS:
        rel = f"probe.{ext}"
        o, p = lookup(o_s, rel), lookup(p_s, rel)
        compared = o in ("ltnewer", "rtnewer", "diff")
        records.append({"kind": "ext", "name": rel, "oracle": o,
                        "product": p, "compared": compared})
        print(f"  {rel:<24} oracle={o:<10} "
              f"{'COMPARED' if compared else 'ignored '}  product={p}")

    print("\n=== B. name shapes ===")
    for rel in SHAPE_NAMES:
        o, p = lookup(o_s, rel), lookup(p_s, rel)
        compared = o in ("ltnewer", "rtnewer", "diff")
        records.append({"kind": "shape", "name": rel, "oracle": o,
                        "product": p, "compared": compared})
        print(f"  {rel:<34} oracle={o:<10} "
              f"{'COMPARED' if compared else 'ignored '}  product={p}")

    print("\n=== C. non-PE content under a compared extension ===")
    o, p = lookup(o_s, "textonly.exe"), lookup(p_s, "textonly.exe")
    records.append({"kind": "content", "name": "textonly.exe",
                    "oracle": o, "product": p,
                    "compared": o in ("ltnewer", "rtnewer", "diff")})
    print(f"  textonly.exe (text content)  oracle={o}  product={p}")

    (run_dir / "u9c-results.json").write_text(
        json.dumps({"oracle_exit": run.exit_code,
                    "product_exit": proc.returncode,
                    "records": records}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nraw: {run_dir / 'u9c-results.json'}")

    print("\n=== the complete measured gate ===")
    compared = sorted(r["name"] for r in records if r["compared"])
    print(f"  COMPARED ({len(compared)}): {compared}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
