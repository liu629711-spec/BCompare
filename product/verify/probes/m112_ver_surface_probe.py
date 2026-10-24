#!/usr/bin/env python3
"""M112: the version-report surface (function 8, Version Compare, U6's other
half -- docs/17 closed the registry half).

Public grammar (help/scripting_reference.html, VERSION-REPORT):
    version-report layout:<layout> [options:<options>] [title:<report title>]
                  output-to:(printer|clipboard|<filename>) [output-options:<options>]
                  [<comparison>]
    layout = side-by-side | summary
    options (per help): ignore-unimportant (ALL layouts) |
        display-all | display-mismatches | display-matches (all except summary)
    NOTE: the help lists ignore-unimportant for version -- the registry probe
    (m101 R9) measured it as accepted-but-inert there. Same claim to measure
    here, not trust.
viewver.html semantics: file attributes aligned as a field list (the
shot_versioncompare.png screenshot shows Name/Size/Modified/Created/Accessed/
Attributes/CRC/Version rows, two columns), with the differing FIELDS
highlighted rather than character-level differences.

Open questions, one cell each (serial Oracle, Job-Object containment):
  V1  identical pair, side-by-side: frame shape, exit 0?
  V2  identical pair, summary: which count lines exist AT ALL?
  V3  different pair (5.2.1 vs 5.2.6 engines), side-by-side / V4 summary
  V5  pair differing only in ProductVersion (5.2.1.32035 vs 5.2.6.32774)
  V6  pair differing only in CompanyName/LegalCopyright wording
  V7  file with NO version resource (a plain text file) vs one WITH it
  V8  BOTH files with no version resource
  V9  missing left file / V10 missing right (107 like registry, or split?)
  V11 layout:bogus / V12 no layout (106 expected)
  V13 layout:VERSION... uppercase
  V14 options:ignore-unimportant (accepted? inert?)
  V15 options:display-mismatches / V16 display-matches (summary behaviour?)
  V17 options:bogus (106 expected)
  V18 output-options:html-embed (106 expected)
  V19 one file / V20 three files (106 expected)
  V21 zero files (0 + BOM shell like registry, or 107?)
  V22 title: replaces frame line 1?
  V23 a non-PE text pair (the .reg channel's fallback family)
  V24 a PE that differs ONLY in a field the screenshot does not show
      (InternalName / OriginalFilename) -- does it count as a difference?
  V25 a directory vs a file (folder through version-report)

Fixtures are REAL PE files with real version resources, copied verbatim into
the run's fixtures/ dir: the two Beyond Compare engines (5.2.1.32035 and
5.2.6.32774 -- differing in 6 fields), Windows system binaries (Microsoft
fields, one of them MUI-flavoured), and a plain text file with no resource.
Nothing is generated: the Oracle measures real bytes.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m112_ver_surface_probe.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

#: (dst-name, source path, note)
FIXTURES = [
    ("cur-BCompare.exe", r"D:\BCompare\BCompare\BCompare.exe", "current engine 5.2.1.32035"),
    ("ref-BCompare.exe", r"D:\bc-official\app\BCompare.exe", "reference engine 5.2.6.32774"),
    ("cur-BComp.com", r"D:\BCompare\BCompare\BComp.com", "current launcher (smaller resource set)"),
    ("ref-BComp.com", r"D:\bc-official\app\BComp.com", "reference launcher"),
    ("sys-notepad.exe", r"C:\Windows\System32\notepad.exe", "Microsoft MUI-flavoured fields"),
    ("sys-cmd.exe", r"C:\Windows\System32\cmd.exe", "Microsoft fields, different version"),
    ("sys-kernel32.dll", r"C:\Windows\System32\kernel32.dll", "DLL: no OriginalFilename path shape"),
    ("plain.txt", None, "no version resource at all"),
]
PLAIN_TEXT = "not a PE file\r\njust text\r\n"


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m112-versurface-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    copied: dict[str, str] = {}
    for name, src, _note in FIXTURES:
        dst = fx / name
        if src is None:
            dst.write_bytes(PLAIN_TEXT.encode())
        else:
            shutil.copyfile(src, dst)
        copied[name] = str(dst.resolve())
        print(f"fixture {name:<20} {dst.stat().st_size:>9} bytes  sha256={hashlib.sha256(dst.read_bytes()).hexdigest()[:16]}")

    def w(name: str, data: bytes) -> str:
        p = fx / name
        p.write_bytes(data)
        return str(p.resolve())

    # A derived pair: identical bytes except the version-number spelling, so
    # exactly one field differs (the field list must show it and nothing else).
    base = pathlib.Path(copied["cur-BCompare.exe"]).read_bytes()
    # The two engines already differ in 6 fields; a same-file pair gives the
    # identical case, and the plain/PE pair gives the missing-resource case.
    A = copied["cur-BCompare.exe"]          # current engine
    Asame = w("cur-copy.exe", base)         # byte-identical copy of A
    B = copied["ref-BCompare.exe"]          # reference engine (6 fields differ)
    C = copied["cur-BComp.com"]             # the launcher: different resource set
    D = copied["sys-notepad.exe"]           # Microsoft MUI
    E = copied["sys-cmd.exe"]               # Microsoft, other version
    F = copied["sys-kernel32.dll"]          # DLL
    T = copied["plain.txt"]                 # no version resource
    NL = str((fx / "NOPE-L.exe").resolve())
    NR = str((fx / "NOPE-R.exe").resolve())

    def line(lay, extra=""):
        return f'version-report layout:{lay}{extra} output-to:"%3" "%1" "%2"'

    CASES = [
        ("V1-sbs-equal", line("side-by-side"), A, Asame),
        ("V2-sum-equal", line("summary"), A, Asame),
        ("V3-sbs-diff", line("side-by-side"), A, B),
        ("V4-sum-diff", line("summary"), A, B),
        ("V5-sbs-com", line("side-by-side"), A, C),
        ("V6-sbs-ms", line("side-by-side"), D, E),
        ("V7-sbs-plain-vs-pe", line("side-by-side"), T, A),
        ("V8-sbs-plain-both", line("side-by-side"), T, T),
        ("V9-missing-left", line("side-by-side"), NL, Asame),
        ("V10-missing-right", line("side-by-side"), A, NR),
        ("V11-bogus-layout", line("bogus"), A, Asame),
        ("V12-no-layout", 'version-report output-to:"%3" "%1" "%2"', A, Asame),
        ("V13-layout-upper", line("SUMMARY"), A, B),
        ("V14-opt-ignore-unimp", line("summary", " options:ignore-unimportant"), A, B),
        ("V15-opt-dmism", line("summary", " options:display-mismatches"), A, B),
        ("V16-opt-dmatch", line("summary", " options:display-matches"), A, B),
        ("V17-opt-bogus", line("summary", " options:line-numbers"), A, B),
        ("V18-outopts", line("side-by-side", " output-options:html-embed"), A, Asame),
        ("V19-one-file", 'version-report layout:summary output-to:"%3" "%1"', A, ""),
        ("V22-title", line("side-by-side", ' title:"VerTitle"'), A, B),
        ("V23-sbs-reg-pair", line("side-by-side"), copied["cur-BComp.com"], copied["ref-BComp.com"]),
        ("V24-sbs-dll", line("side-by-side"), A, F),
        ("V25-sbs-dir-vs-file", line("side-by-side"), str(fx), A),
    ]
    RAW = [
        ("V13b-three-files",
         f'version-report layout:summary output-to:"%3" "{A}" "{Asame}" "{B}"', "", ""),
        ("V21-zero-files", 'version-report layout:side-by-side output-to:"%3"', "", ""),
    ]

    results = []
    for tag, ln, l, r in CASES + RAW:
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [ln])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        print(f"{tag}: exit={res.exit_code} bytes={len(body)}")
        head = body.decode("utf-8-sig", errors="replace").splitlines()[:30]
        for h in head:
            print("   ", repr(h))
        results.append({"tag": tag, "script": ln, "exit": res.exit_code,
                        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                        "head": head})
    (run_dir / "m112-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
