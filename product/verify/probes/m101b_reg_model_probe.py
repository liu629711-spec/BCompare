#!/usr/bin/env python3
"""M101b: registry-report model on CLEAN fixtures (m101's fixture builder
escaped CRLF as literal backslash-r-backslash-n -- every body line got glued
onto one giant line; the v5-vs-regedit4 parse verdict was therefore
garbage). This batch fixes the escapes and probes the comparison model.

Open questions (one cell each, serial Oracle):
  C1  clean v5 single-key pair, summary: does the same-count line appear?
      what is the vocabulary (项 = item?)
  C2  changed value, summary: which count lines, in what order
  C3  left-only key + right-only key + changed value + same value, summary:
      full category set + measured order
  C4  same pair as C3, side-by-side: body table structure (alignment,
      markers, type/data columns)
  C5  type change with same text: dword:00000001 vs "1"
  C6  hex(16,...) multi-line continuation value
  C7  default value @="data" vs absent
  C8  key-deletion line [-HKEY...] -- does it parse at all in a report?
  C9  regedit4 clean pair (compare C1 shape)
  C10 garbage content in a .reg name: parse error position semantics
      (line:col) -- single clean bad line
  C11 real regedit UTF-16LE+BOM v5 file: accepted silently?
  C12 keys listed OUT of sorted order in file: does the table reorder?
  C13 ignore-unimportant on a clean pair: header line? label rename?
  C14 display-mismatches / display-matches on a clean sbs pair (body
      filtering like text-report? unlike picture's inert?)
  C15 value with embedded quotes/escapes
  C16 basekey suffix rule: first key? common prefix? garbage reg file?

Usage: cd D:\\Rea\\product\\verify && python probes/m101b_reg_model_probe.py
"""
from __future__ import annotations

import hashlib, json, pathlib, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc

C = "\r\n"
HEAD5 = "Windows Registry Editor Version 5.00" + C + C

def reg(*lines: str) -> str:
    return HEAD5 + C.join(lines) + C

REG_1K1V = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
               '"Name"="Alpha"',
               '"Num"=dword:00000001')
REG_CHANGED = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
                  '"Name"="Beta"',
                  '"Num"=dword:00000001')
REG_C3_L = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
              '"Name"="Alpha"',
              '"Num"=dword:00000001',
              "",
              "[HKEY_CURRENT_USER\\Software\\ReaProbe\\OnlyL]",
              '"Deep"="one"')
REG_C3_R = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
              '"Name"="Beta"',
              '"Num"=dword:00000001',
              "",
              "[HKEY_CURRENT_USER\\Software\\ReaProbe\\OnlyR]",
              '"Extra"="two"')
REG_TYPECHG = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
                  '"Name"="Alpha"',
                  '"Num"="1"')
REG_HEX_L = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
                '"Blob"=hex:68,65,6c,6c,6f',
                "  2c,20,77,6f,72,6c,64")
REG_HEX_R = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
                '"Blob"=hex:68,65,6c,6c,6f,2c,20,77,6f,72,6c,64')
REG_DEF = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
              '@="default data"')
REG_DEL = reg("[-HKEY_CURRENT_USER\\Software\\ReaProbe\\Gone]",
              "[HKEY_CURRENT_USER\\Software\\ReaProbe]",
              '"Name"="Alpha"')
REG_R4 = ("REGEDIT4" + C + C +
          "[HKEY_CURRENT_USER\\Software\\ReaProbe]" + C +
          '"Name"="Alpha"' + C + '"Num"=dword:00000001' + C)
REG_BAD1 = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
               "this is not a value line",
               '"Name"="Alpha"')
REG_UNSORTED = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe\\Zulu]",
                   '"v"="z"',
                   "",
                   "[HKEY_CURRENT_USER\\Software\\ReaProbe\\Alpha]",
                   '"v"="a"')
REG_QUOTES = reg("[HKEY_CURRENT_USER\\Software\\ReaProbe]",
                 '"Phrase"="he said \\"hi\\" ok"')
GARBAGE = ("not a registry file at all" + C + "just text" + C)


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m101b-regmodel-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    def w(name: str, data: str | bytes) -> str:
        p = fx / name
        p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return str(p.resolve())

    A = w("c1-L.reg", REG_1K1V); As = w("c1-R.reg", REG_1K1V)
    CH = w("c2-R.reg", REG_CHANGED)
    C3L = w("c3-L.reg", REG_C3_L); C3R = w("c3-R.reg", REG_C3_R)
    TC = w("c5-R.reg", REG_TYPECHG)
    HL = w("c6-L.reg", REG_HEX_L); HR = w("c6-R.reg", REG_HEX_R)
    DF = w("c7-L.reg", REG_DEF); DF2 = w("c7-R.reg", REG_1K1V)
    DL = w("c8-L.reg", REG_DEL)
    R4 = w("c9-L.reg", REG_R4); R4R = w("c9-R.reg", REG_R4)
    BAD = w("c10-L.reg", REG_BAD1); BADR = w("c10-R.reg", REG_1K1V)
    (fx / "c11-L.reg").write_bytes(
        b"\xff\xfe" + ("Windows Registry Editor Version 5.00\r\n\r\n"
                       "[HKEY_CURRENT_USER\\Software\\ReaProbe]\r\n"
                       '"Name"="Alpha"\r\n').encode("utf-16-le"))
    U16 = str((fx / "c11-L.reg").resolve())
    UNS = w("c12-L.reg", REG_UNSORTED); UNSR = w("c12-R.reg", REG_UNSORTED)
    QS = w("c15-L.reg", REG_QUOTES); QSR = w("c15-R.reg", REG_QUOTES)
    G1 = w("c16-L.reg", GARBAGE); G2 = w("c16-R.reg", GARBAGE)

    def line(lay, extra=""):
        return f'registry-report layout:{lay}{extra} output-to:"%3" "%1" "%2"'

    CASES = [
        ("C1-clean-equal-sum", line("summary"), A, As),
        ("C2-changed-sum", line("summary"), A, CH),
        ("C3-mixed-sum", line("summary"), C3L, C3R),
        ("C3b-mixed-sum-rev", line("summary"), C3R, C3L),
        ("C4-mixed-sbs", line("side-by-side"), C3L, C3R),
        ("C5-typechange-sum", line("summary"), A, TC),
        ("C6-hexwrap-sum", line("summary"), HL, HR),
        ("C6b-hexwrap-sbs", line("side-by-side"), HL, HR),
        ("C7-default-value-sum", line("summary"), DF, DF2),
        ("C8-keydelete-sum", line("summary"), DL, A),
        ("C9-regedit4-equal", line("summary"), R4, R4R),
        ("C10-badline-sum", line("summary"), BAD, BADR),
        ("C11-utf16-sum", line("summary"), U16, A),
        ("C12-unsorted-sbs", line("side-by-side"), UNS, UNSR),
        ("C12b-unsorted-diff-sbs", line("side-by-side"), UNS, As),
        ("C13-clean-ignore-sum", line("summary", " options:ignore-unimportant"), C3L, C3R),
        ("C14a-dmism-sbs", line("side-by-side", " options:display-mismatches"), C3L, C3R),
        ("C14b-dmatch-sbs", line("side-by-side", " options:display-matches"), C3L, C3R),
        ("C15-quotes-equal-sum", line("summary"), QS, QSR),
        ("C15b-quotes-equal-sbs", line("side-by-side"), QS, QSR),
        ("C16-garbage-sum", line("summary"), G1, G2),
    ]

    results = []
    for tag, ln, l, r in CASES:
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [ln])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        bom = body.startswith(b"\xef\xbb\xbf")
        print(f"{tag}: exit={res.exit_code} bytes={len(body)} bom={bom}")
        head = body.decode("utf-8-sig", errors="replace").splitlines()
        for h in head:
            print("   ", repr(h))
        results.append({"tag": tag, "script": ln, "exit": res.exit_code,
                        "bytes": len(body), "bom": bom,
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "head": head})
    (run_dir / "m101b-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
