#!/usr/bin/env python3
"""M101d: registry type display strings, name sort case, default-value row,
column geometry (long names), orphan key-header pairing. All byte/width
verdicts from int ordinals (display-separator lesson).

 S1 type strings sbs: dword 0 vs ff vs 10000; hex(1) multi-sz; hex(2)?;
    hex(7) multi-string w/ trailing pair; REG_EXPAND_SZ; guid; none-type?
 S2 sort case: keys "beta","Alpha","_x","0z" -- table order reveals
    case-insensitive vs ASCII; values same probe
 S3 default value @ sbs row (name column text for @)
 S4 long name geometry: 20-char value name + short/long data -> integer
    column offsets of markers (= <> +- -+) and header widths
 S5 orphan key header: L has child key Kx, R does not -> how does the
    header row appear (marker? blank column?) + its orphan values
 S6 nested deeper: A\B under base, ordering: sibling keys sorted depth-first?
 S7 empty-string value "" vs missing?
 S8 multiple top-level bases: L=[HKCU\X],[HKCU\Y] R same -> basekey =
    HKCU (common parent of X,Y)? body shows X,Y as headers
 S9 value-less child keys only -> zero counts but body rows?
 S10 line continuation for STRING value ("a"\n  "b") -- hex-style only or any?

Usage: cd D:\\Rea\\product\\verify && python probes/m101d_reg_details.py
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

B = "HKEY_CURRENT_USER\\Software\\ReaProbe"

CASES = {
    # S1 type strings (L vs R of each type, identical pair -> table rows with `=`)
    "S1-types": (reg(
        f"[{B}]",
        '"dwz"=dword:00000000',
        '"dwff"=dword:000000ff',
        '"dwbig"=dword:00010000',
        '"ms1"=hex(1):61,00,62,00,00,00',
        '"ms7"=hex(7):61,00,00,00',
        '"bin"=hex:41,42,43',
        '"exp"=hex(2):25,00,50,00,41,00,54,00,48,00,25,00,00,00',
        '"q"=hex(11):ab,cd',
        '"str"="plain"',
        '"none"=-'),
        reg(
        f"[{B}]",
        '"dwz"=dword:00000000',
        '"dwff"=dword:000000ff',
        '"dwbig"=dword:00010000',
        '"ms1"=hex(1):61,00,62,00,00,00',
        '"ms7"=hex(7):61,00,00,00',
        '"bin"=hex:41,42,43',
        '"exp"=hex(2):25,00,50,00,41,00,54,00,48,00,25,00,00,00',
        '"q"=hex(11):ab,cd',
        '"str"="plain"',
        '"none"=-')),
    # S2 case sort: keys and values
    "S2-sort": (reg(
        f"[{B}]", '"z"="1"', '"A"="2"', '"_u"="3"', '"0n"="4"',
        "",
        f"[{B}\\beta]", '"v"="1"', "",
        f"[{B}\\Alpha]", '"v"="2"', "",
        f"[{B}\\_key]", '"v"="3"', "",
        f"[{B}\\0key]", '"v"="4"'),
        None),  # same file both sides
    # S3 default row
    "S3-default": (reg(f"[{B}\\Sub]", '@="dd"', '"other"="1"'), None),
    # S4 geometry: 20-char names, long/short data
    "S4-geom": (reg(
        f"[{B}]",
        '"AVeryLongValueName01"="short"',
        '"B"="' + "y" * 40 + '"',
        '"C"=dword:00000001'), None),
    # S5 orphan key header
    "S5-orphankey": (reg(
        f"[{B}]", '"v"="1"', "",
        f"[{B}\\Kx]", '"a"="1"', '"b"="2"'),
        reg(f"[{B}]", '"v"="1"')),
    # S6 nesting order: A\B vs C under base
    "S6-nest": (reg(
        f"[{B}\\A\\B]", '"x"="1"', "",
        f"[{B}\\C]", '"y"="2"', "",
        f"[{B}]", '"top"="0"'), None),
    # S7 empty string value
    "S7-empty": (reg(f"[{B}]", '"e"=""', '"v"="1"'),
                 reg(f"[{B}]", '"e"=""', '"v"="2"')),
    # S8 multiple top bases (HKCU\X and HKCU\Y)
    "S8-multiroot": (reg(
        f"[HKEY_CURRENT_USER\\Software\\ReaX]",
        '"v"="1"', "",
        f"[HKEY_CURRENT_USER\\Software\\ReaY]", '"w"="2"'),
        None),
    # S9 child keys only, no values anywhere
    "S9-keyonly": (reg(f"[{B}\\One]", "", f"[{B}\\Two]"),
                   reg(f"[{B}\\One]", "", f"[{B}\\Two]")),
    # S10 string continuation
    "S10-cont": (reg(f"[{B}]", '"s"="aaa"', '  "bbb"'), None),
}


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m101d-regdetails-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)

    results = []
    for tag, (lt, rt) in CASES.items():
        rt = lt if rt is None else rt
        for layout in ("side-by-side",):
            name = f"{tag}-sbs"
            lp = run_dir / "fixtures" / f"{name}-L.reg"
            rp = run_dir / "fixtures" / f"{name}-R.reg"
            lp.write_bytes(lt.encode("utf-8")); rp.write_bytes(rt.encode("utf-8"))
            script = f'registry-report layout:{layout} output-to:"%3" "%1" "%2"'
            sp = run_dir / "scripts" / f"{name}.bcs"
            orc.write_script(sp, [script])
            out = run_dir / "reports" / f"{name}.out"
            res = orc.run(inst.oracle_path, sp, str(lp.resolve()),
                          str(rp.resolve()), str(out), timeout=120.0,
                          script_text=script)
            body = out.read_bytes() if out.exists() else b""
            lines = body.decode("utf-8-sig", errors="replace").splitlines()
            print(f"== {name}: exit={res.exit_code}")
            for i, ln in enumerate(lines):
                print(f"   {i:2} {ln!r}")
            # marker column positions as integers
            for i, ln in enumerate(lines):
                if ln.startswith(("名称", "---")):
                    continue
                marks = []
                for m in ("+-", "-+", "<>", " = "):
                    j = ln.find(m)
                    if j != -1:
                        marks.append((m.strip(), j))
                if marks:
                    print(f"      row {i} markers@cols: {marks}")
            results.append({"tag": name, "exit": res.exit_code,
                            "bytes": len(body),
                            "sha256": hashlib.sha256(body).hexdigest(),
                            "lines": lines})
    (run_dir / "m101d-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
