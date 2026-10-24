#!/usr/bin/env python3
"""M101c: registry-report geometry, basekey rule, item semantics (shell bytes
with ordinals -- the display-separator lesson of docs/12 §3 means every
byte verdict here comes from ints, never from the console).

Q groups:
 G1 basekey: L=[HKCU\\A] R=[HKCU\\B] -- suffix on both file lines?
 G2 basekey: L has 2 top keys, R has both -- common prefix or first key?
 G3 basekey: right file has NO valid keys (garbage) -- suffix shape?
 G4 items=values: key with NO values at all -- counted?
 G5 key vs value name collision ordering within one key: "a" value + "a"
    subkey both named; what does the row show
 G6 similar/unimportant: value "x " vs "x" (trailing space) -- unimportant?
 G7 similar: case difference "Alpha" vs "alpha" on a .reg -- important?
 G8 multi-key sbs geometry: 3 sibling keys, one differing value deep inside
 G9 +-/-+ orphan pairing inside one key: value present left, absent right,
    and vice versa, under one key
 G10 default-value display under a child key (@=) in sbs
 G11 shell bytes: zero-file registry-report, BOM? mode line? full ord list
 G12 same-value long data: data column width cap? (300-char value)
 G13 two same-named keys (duplicate) -- 删除/重复跳过 semantics
 G14 key header alignment across sides when only one side has the key at
    that table position (already seen C4) -- confirm stable
 G15 REG_SZ hex(00)-terminated multi-string (hex(1,00,00...))
 G16 value-name case sort: "Beta" vs "alpha" ordering in one key
 G17 basekey when first key line is a delete line on ONE side only
 G18 mode line in summary layout (should be absent -- confirm)
 G19 title on summary
 G20 options:display-mismatches on summary (mode line? counts?)

Usage: cd D:\\Rea\\product\\verify && python probes/m101c_reg_geometry.py
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

BASE = "HKEY_CURRENT_USER\\Software\\ReaProbe"

CASES_TEXT = {}

# G1 / G2 / G3 / G17: basekey rule
CASES_TEXT["G1"] = (reg(f"[HKEY_CURRENT_USER\\Software\\A]", '"v"="1"'),
                    reg(f"[HKEY_CURRENT_USER\\Software\\B]", '"v"="1"'))
CASES_TEXT["G2"] = (reg(f"[{BASE}\\A]", '"v"="1"', "", f"[{BASE}\\B]", '"v"="1"'),
                    reg(f"[{BASE}\\A]", '"v"="1"', "", f"[{BASE}\\B]", '"v"="1"'))
CASES_TEXT["G3"] = (reg(f"[{BASE}\\A]", '"v"="1"'),
                    "Windows Registry Editor Version 5.00\r\n\r\nnot a key line\r\n")
CASES_TEXT["G17"] = (reg(f"[-{BASE}\\Gone]", f"[{BASE}\\A]", '"v"="1"'),
                     reg(f"[{BASE}\\A]", '"v"="1"'))
# G4 empty key
CASES_TEXT["G4"] = (reg(f"[{BASE}]"), reg(f"[{BASE}]"))
CASES_TEXT["G4b"] = (reg(f"[{BASE}\\Empty]", f"[{BASE}]", '"v"="1"'),
                     reg(f"[{BASE}]", '"v"="1"'))
# G5 same-name key+value
CASES_TEXT["G5"] = (reg(f"[{BASE}\\a]", '"v"="1"', f"[{BASE}]", '"a"="2"'),
                   reg(f"[{BASE}\\a]", '"v"="1"', f"[{BASE}]", '"a"="2"'))
# G6 trailing whitespace value
CASES_TEXT["G6"] = (reg(f"[{BASE}]", '"v"="x "'), reg(f"[{BASE}]", '"v"="x"'))
# G7 case-insensitive value data
CASES_TEXT["G7"] = (reg(f"[{BASE}]", '"v"="Alpha"'), reg(f"[{BASE}]", '"v"="alpha"'))
# G8 three siblings deep diff
G8L = reg(f"[{BASE}]", '"top"="1"', "",
          f"[{BASE}\\K1]", '"a"="1"', "",
          f"[{BASE}\\K2]", '"b"="X"', "",
          f"[{BASE}\\K3]", '"c"="3"')
G8R = reg(f"[{BASE}]", '"top"="1"', "",
          f"[{BASE}\\K1]", '"a"="1"', "",
          f"[{BASE}\\K2]", '"b"="Y"', "",
          f"[{BASE}\\K3]", '"c"="3"')
CASES_TEXT["G8"] = (G8L, G8R)
# G9 orphan pairing under one key
G9L = reg(f"[{BASE}]", '"A"="1"', '"B"="2"', '"D"="4"')
G9R = reg(f"[{BASE}]", '"A"="1"', '"C"="3"', '"D"="4"')
CASES_TEXT["G9"] = (G9L, G9R)
# G10 default value in sbs under child
G10L = reg(f"[{BASE}\\Sub]", '@="dd"')
G10R = reg(f"[{BASE}\\Sub]", '@="ee"')
CASES_TEXT["G10"] = (G10L, G10R)
# G12 long data
LONG = "x" * 300
CASES_TEXT["G12"] = (reg(f"[{BASE}]", f'"v"="{LONG}"'),
                     reg(f"[{BASE}]", f'"v"="{LONG}"'))
# G13 duplicate keys
CASES_TEXT["G13"] = (reg(f"[{BASE}\\Dup]", '"v"="1"', f"[{BASE}\\Dup]", '"v"="1"'),
                     reg(f"[{BASE}\\Dup]", '"v"="1"'))
# G15 multi-string hex(1,...)
CASES_TEXT["G15"] = (reg(f"[{BASE}]", '"s"=hex(1):61,00,62,00,00,00'),
                     reg(f"[{BASE}]", '"s"=hex(1):61,00,62,00,00,00'))
# G16 value case sort
CASES_TEXT["G16"] = (reg(f"[{BASE}]", '"Beta"="1"', '"alpha"="2"', '"Gamma"="3"'),
                     reg(f"[{BASE}]", '"Beta"="1"', '"alpha"="2"', '"Gamma"="3"'))

def run_cell(inst, run_dir, tag, script, l_text, r_text, lbytes=None, rbytes=None):
    fx = run_dir / "fixtures"
    lp = fx / f"{tag}-L.reg"; rp = fx / f"{tag}-R.reg"
    lp.write_bytes((lbytes if lbytes is not None else l_text.encode("utf-8")))
    rp.write_bytes((rbytes if rbytes is not None else r_text.encode("utf-8")))
    sp = run_dir / "scripts" / f"{tag}.bcs"
    orc.write_script(sp, [script])
    out = run_dir / "reports" / f"{tag}.out"
    res = orc.run(inst.oracle_path, sp, str(lp.resolve()), str(rp.resolve()),
                  str(out), timeout=120.0, script_text=script)
    body = out.read_bytes() if out.exists() else b""
    text = body.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    print(f"== {tag}: exit={res.exit_code} bytes={len(body)}")
    for ln in lines:
        print("   ", repr(ln))
    return {"tag": tag, "script": script, "exit": res.exit_code,
            "bytes": len(body), "ords_head": list(body[:100]),
            "sha256": hashlib.sha256(body).hexdigest(), "lines": lines}

def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m101c-reggeom-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)

    results = []
    for tag, (lt, rt) in CASES_TEXT.items():
        for layout in ("summary", "side-by-side"):
            if tag in ("G6", "G7") and layout == "summary":
                continue      # counts interesting; body geometry for sbs only
            script = (f'registry-report layout:{layout} output-to:"%3" "%1" "%2"')
            results.append(run_cell(inst, run_dir, f"{tag}-{layout[:3]}",
                                    script, lt, rt))

    # G11 zero-file shell: exact bytes
    sp = run_dir / "scripts" / "G11-shell.bcs"
    orc.write_script(sp, ['registry-report layout:side-by-side output-to:"%3"'])
    out = run_dir / "reports" / "G11-shell.out"
    res = orc.run(inst.oracle_path, sp, "", "", str(out), timeout=120.0,
                  script_text=sp.read_text(encoding="utf-8"))
    body = out.read_bytes() if out.exists() else b""
    print(f"== G11-shell: exit={res.exit_code} bytes={len(body)}")
    print("   ords:", list(body))
    results.append({"tag": "G11-shell", "exit": res.exit_code,
                    "bytes": len(body), "ords": list(body),
                    "lines": body.decode("utf-8-sig", errors="replace").splitlines()})

    # G19 title summary / G20 display-mismatches on summary
    lt, rt = CASES_TEXT["G8"]
    results.append(run_cell(inst, run_dir, "G19-title-sum",
        'registry-report layout:summary title:"RegSum" output-to:"%3" "%1" "%2"', lt, rt))
    results.append(run_cell(inst, run_dir, "G20-dmism-sum",
        'registry-report layout:summary options:display-mismatches output-to:"%3" "%1" "%2"', lt, rt))

    (run_dir / "m101c-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
