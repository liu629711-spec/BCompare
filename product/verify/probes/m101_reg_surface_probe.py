#!/usr/bin/env python3
"""M101: the registry-report surface (function 8, Registry Compare, U6).

Public grammar (help/scripting_reference.html, REGISTRY-REPORT):
    registry-report layout:<layout> [options:<opts>] [title:<t>]
                  output-to:(printer|clipboard|<file>) [output-options:<o>]
                  [<comparison>]
    layout = side-by-side | summary
    options (per help): display-all | display-mismatches | display-matches
    NOTE: help lists NO ignore-unimportant for registry (version-report DOES)
    -- a claim to measure, not trust.
viewreg.html semantics: keys/values sorted and ALIGNED by name; keys colored
by difference vs orphan; values colored by character difference.

Open questions, one cell each (serial Oracle, Job-Object containment):
  R1  identical .reg pair, side-by-side: frame shape, exit 0?
  R2  identical pair, summary: which count lines exist AT ALL (pixel-style?)
  R3  changed value, side-by-side / R4 summary
  R5  layout:bogus -> expect 106
  R6  no layout -> expect 106 (H1 precedent)
  R7  options:display-mismatches on summary -- does registry REFUSE or accept
      the way text-report accepts display-* (unlike picture's byte-inert)?
  R8  options:display-all (help's documented default spelling)
  R9  options:ignore-unimportant -- 106 (per help) or accepted (measure)?
  R10 output-options:html-embed -> expect 106
  R11 zero files (layout given) -> picture=0+BOM shell, hex=107: WHICH?
  R12 one file -> expect 106
  R13 three files -> expect 106
  R14 missing left file / R15 missing right -> picture both 107, hex split
  R16 title: replaces frame line 1?
  R17 layout:SUMMARY uppercase (picture measured case-insensitive)
  R18 options: empty value (picture: accepted)
  R19 non-registry pair: two PNG files through registry-report -- parse
      error line (picture-style) or text fallback or refusal?
  R20 REGEDIT4-style header (Windows Registry Editor Version 5.00 vs
      REGEDIT4) accepted?

Fixtures: plain ASCII .reg exports (regedit writes UTF-16 for v5 files, but
BC reads text; ANSI/UTF-8 text is what the product must parse anyway -- the
header spelling is probed in R20, encoding depth later).

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m101_reg_surface_probe.py
"""
from __future__ import annotations

import hashlib, json, pathlib, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

HEAD5 = "Windows Registry Editor Version 5.00\r\n\r\n"

REG_A = HEAD5 + (
    "[HKEY_CURRENT_USER\\Software\\ReaProbe]\\r\n"
    '"Name"="Alpha"\r\n'
    '"Num"=dword:00000001\r\n'
    "\r\n"
    "[HKEY_CURRENT_USER\\Software\\ReaProbe\\Sub]\\r\n"
    '"Deep"="one"\r\n'
)
REG_B_SAME = REG_A
REG_C_CHANGED = HEAD5 + (
    "[HKEY_CURRENT_USER\\Software\\ReaProbe]\\r\n"
    '"Name"="Beta"\r\n'
    '"Num"=dword:00000001\r\n'
    "\r\n"
    "[HKEY_CURRENT_USER\\Software\\ReaProbe\\Sub]\\r\n"
    '"Deep"="one"\r\n'
)
REG_D_ORPHANKEY = HEAD5 + (
    "[HKEY_CURRENT_USER\\Software\\ReaProbe]\\r\n"
    '"Name"="Alpha"\r\n'
    '"Num"=dword:00000001\r\n'
    "\r\n"
    "[HKEY_CURRENT_USER\\Software\\ReaProbe\\OnlyR]\\r\n"
    '"Extra"="two"\r\n'
)
REG_E_REGEDIT4 = ("REGEDIT4\r\n\r\n"
    "[HKEY_CURRENT_USER\\Software\\ReaProbe]\r\n"
    '"Name"="Alpha"\r\n'
)
PNG = (b"\x89PNG\r\n\x1a\n" + b"\x00" * 40)


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m101-regsurface-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    def w(name: str, data: str | bytes) -> str:
        p = fx / name
        p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return str(p.resolve())

    A = w("same-L.reg", REG_A); Asame = w("same-R.reg", REG_B_SAME)
    C = w("chg-R.reg", REG_C_CHANGED)
    D = w("orph-R.reg", REG_D_ORPHANKEY)
    E = w("regedit4-L.reg", REG_E_REGEDIT4)
    P1 = w("p1-L.png", PNG); P2 = w("p2-R.png", PNG)
    NL = str((fx / "NOPE-L.reg").resolve())   # deliberately nonexistent
    NR = str((fx / "NOPE-R.reg").resolve())

    def line(lay, extra=""):
        return f'registry-report layout:{lay}{extra} output-to:"%3" "%1" "%2"'

    CASES = [
        ("R1-sbs-equal", line("side-by-side"), A, Asame),
        ("R2-sum-equal", line("summary"), A, Asame),
        ("R3-sbs-changed", line("side-by-side"), A, C),
        ("R4-sum-changed", line("summary"), A, C),
        ("R5-bogus-layout", line("bogus"), A, Asame),
        ("R6-no-layout", 'registry-report output-to:"%3" "%1" "%2"', A, Asame),
        ("R7-opt-dmism", line("summary", " options:display-mismatches"), A, C),
        ("R8-opt-dall", line("side-by-side", " options:display-all"), A, C),
        ("R9-opt-ignore-unimp", line("summary", " options:ignore-unimportant"), A, C),
        ("R10-outopts", line("side-by-side", " output-options:html-embed"), A, Asame),
        ("R12-one-file", 'registry-report layout:summary output-to:"%3" "%1"', A, ""),
        ("R13-three-files",
         f'registry-report layout:summary output-to:"%3" "{A}" "{Asame}" "{C}"', "", ""),
        ("R14-missing-left", line("side-by-side"), NL, Asame),
        ("R15-missing-right", line("side-by-side"), A, NR),
        ("R16-title", line("side-by-side", ' title:"RegTitle"'), A, C),
        ("R17-layout-upper", line("SUMMARY"), A, C),
        ("R18-opt-empty", line("summary", " options:"), A, C),
        ("R19-png-pair", line("summary"), P1, P2),
        ("R20-regedit4", line("summary"), E, A),
        ("R21-orphankey-sum", line("summary"), A, D),
    ]
    RAW = [
        ("R11-zero-files", 'registry-report layout:side-by-side output-to:"%3"', "", ""),
    ]

    results = []
    for tag, ln, l, r in CASES + RAW:
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [ln])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        print(f"{tag}: exit={res.exit_code} bytes={len(body)}")
        head = body.decode("utf-8-sig", errors="replace").splitlines()[:25]
        for h in head:
            print("   ", repr(h))
        results.append({"tag": tag, "script": ln, "exit": res.exit_code,
                        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                        "head": head})
    (run_dir / "m101-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
