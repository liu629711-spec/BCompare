#!/usr/bin/env python3
"""U9 probe -- does `criteria version` gate on the file name, or on content?

`product/docs/08-folder-criteria.md` §已知差异 1 records this as unmeasured:

    `version` 的文件名掩码（BC 只对 `.exe`/`.dll` 等 EXE 格式生效？）未探测：
    当前实现对任意扩展名都尝试读 PE。

That is a real divergence risk in both directions. BC decides a file's *format*
from its name (its masks), so `version` may only ever read an executable-format
file; this product reads the PE resource from whatever the name is. If BC gates
and the product does not, then a `notes.txt` that happens to contain a PE would
be `same` in BC and `ltnewer`/`rtnewer` here.

Design
------

One Oracle call answers it for every extension at once. A single directory pair
contains one file per extension, each a **real** PE (patched `version.dll`, as
u4h established a synthetic blob is ignored) whose two sides differ *only* in
the version fields and therefore have identical sizes. Under
`criteria version` the size and timestamp criteria are cleared, so:

    `ltnewer` / `rtnewer`  -> BC compared the version resource (gated open)
    `same`                 -> BC did not (gated closed)

Identical sizes matter: it removes any chance that a `same` reading comes from
some other criterion falling back to a match.

A second group asks whether the gate is a *mask* or a *content sniff*: the same
PE bytes under names BC's executable mask may or may not cover
(`.exe`/`.dll`/`.ocx`/`.scr`/`.sys`/`.cpl`/`.drv`/`.efi`/`.ax`/`.tsp`), plus
case variants (`.EXE`/`.Dll`), a no-extension name, and a name whose extension
is executable but whose *content* is not a PE.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u9_version_extension_mask.py
"""
from __future__ import annotations

import json
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

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

#: A real, structurally valid PE. u4h measured that the Oracle ignores version
#: resources outside a valid PE, so a synthetic blob would measure nothing.
VERSION_BASE_PE = pathlib.Path("C:/Windows/System32/version.dll")

#: (file name, note). The first group is the extension question; the last few
#: probe the mask's edges and the content-vs-name question.
NAMES: list[tuple[str, str]] = [
    # --- executable extensions BC plausibly covers ---
    ("prog.exe", "exe (control: must be compared)"),
    ("lib.dll", "dll (control)"),
    ("ctrl.ocx", "ocx"),
    ("screen.scr", "scr"),
    ("driver.sys", "sys"),
    ("panel.cpl", "cpl"),
    ("legacy.drv", "drv"),
    ("firmware.efi", "efi"),
    ("plugin.ax", "ax"),
    ("telephony.tsp", "tsp"),
    ("library.olb", "olb"),
    ("control.vbx", "vbx"),
    ("setup.msi", "msi (an installer, not a PE)"),
    ("command.com", "com (16-bit, not a PE)"),
    # --- non-executable extensions carrying PE bytes ---
    ("notes.txt", "txt carrying a real PE"),
    ("data.bin", "bin"),
    ("blob.dat", "dat"),
    ("archive.zip", "zip carrying a real PE"),
    ("readme", "no extension at all"),
    ("page.html", "html"),
    ("sheet.xls", "xls"),
    # --- case variants ---
    ("upper.EXE", "upper-case exe"),
    ("mixed.Dll", "mixed-case dll"),
    ("upper.TXT", "upper-case txt carrying a PE"),
]


def pe_blob(fv: tuple[int, int, int, int]) -> bytes:
    """A real PE whose FileVersion is `fv`."""
    if not VERSION_BASE_PE.is_file():
        raise SystemExit(f"need a real PE base at {VERSION_BASE_PE}")
    data = bytearray(VERSION_BASE_PE.read_bytes())
    sig = (0xFEEF04BD).to_bytes(4, "little")
    i = data.find(sig)
    if i < 0:
        raise SystemExit(f"{VERSION_BASE_PE} has no VS_FIXEDFILEINFO")
    struct.pack_into("<I", data, i + 8, (fv[0] << 16) | fv[1])
    struct.pack_into("<I", data, i + 12, (fv[2] << 16) | fv[3])
    # ProductVersion is patched to a *different* value than FileVersion, so a
    # comparison that read the wrong field would be visible rather than equal.
    struct.pack_into("<I", data, i + 16, (9 << 16) | 9)
    struct.pack_into("<I", data, i + 20, (9 << 16) | 9)
    return bytes(data)


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u9-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    left, right = fx / "L", fx / "R"
    left.mkdir(parents=True, exist_ok=True)
    right.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"base PE : {VERSION_BASE_PE}\n")

    # Left is 2.0.0.0, right is 1.0.0.0: `ltnewer` means the version was read.
    newer = pe_blob((2, 0, 0, 0))
    older = pe_blob((1, 0, 0, 0))
    if len(newer) != len(older):
        raise SystemExit("the two PE blobs must be the same size")
    for name, _ in NAMES:
        (left / name).write_bytes(newer)
        (right / name).write_bytes(older)

    # The product must be asked the same question. It takes two folders plus an
    # output, with the criteria in a script.
    #
    # `criteria` MUST precede `load`: measured in the U4 series, a `criteria`
    # line after `load` does not take effect (the folder report would then use
    # the default pair and every row would read `same` regardless of the mask).
    script_lines = [
        "criteria version",
        'load "%1" "%2"',
        "expand all",
        'folder-report layout:xml output-to:"%3"',
    ]
    script = orc.write_script(run_dir / "reports" / "u9.bcs", script_lines)
    o_out = run_dir / "reports" / "u9.oracle.xml"
    run = orc.run(inst.oracle_path, script, str(left), str(right), o_out,
                  timeout=180.0, script_text="\n".join(script_lines))
    o_body = ""
    if run.report_exists and run.report_bytes:
        o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

    p_out = run_dir / "reports" / "u9.product.xml"
    proc = subprocess.run([str(PRODUCT), "@" + str(script), str(left),
                           str(right), str(p_out)],
                          capture_output=True, timeout=120)
    p_body = ""
    if p_out.exists():
        p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

    def per_name(body: str) -> dict[str, str]:
        """name -> filecomp/@status."""
        out: dict[str, str] = {}
        for m in re.finditer(r"<filecomp([^>]*)>(.*?)</filecomp>", body, re.S):
            attrs, inner = m.group(1), m.group(2)
            st = re.search(r'status="([a-z]+)"', attrs)
            nm = re.search(r"<name>(.*?)</name>", inner)
            if nm:
                out[nm.group(1)] = st.group(1) if st else "?"
        return out

    o_s, p_s = per_name(o_body), per_name(p_body)
    print(f"oracle exit={run.exit_code}  product exit={proc.returncode}")
    print(f"oracle entries={len(o_s)}  product entries={len(p_s)}\n")

    print(f"  {'name':<22} {'oracle':<14} {'product':<14} {'note'}")
    records = []
    agree = 0
    for name, note in NAMES:
        o = o_s.get(name, "-")
        p = p_s.get(name, "-")
        same = o == p
        agree += same
        mark = " " if same else "*"
        print(f"{mark} {name:<22} {o:<14} {p:<14} {note}")
        records.append({"name": name, "note": note, "oracle": o,
                        "product": p, "agree": same})

    (run_dir / "u9-results.json").write_text(
        json.dumps({"oracle_exit": run.exit_code,
                    "product_exit": proc.returncode,
                    "records": records}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\n{agree}/{len(NAMES)} agree")
    print(f"raw: {run_dir / 'u9-results.json'}")

    print("\n=== reading: which extensions does BC compare? ===")
    compared = [r["name"] for r in records
                if r["oracle"] in ("ltnewer", "rtnewer", "diff")]
    ignored = [r["name"] for r in records if r["oracle"] == "same"]
    print(f"  BC COMPARED  ({len(compared)}): {compared}")
    print(f"  BC IGNORED   ({len(ignored)}): {ignored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
