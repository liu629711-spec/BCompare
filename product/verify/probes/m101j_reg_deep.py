#!/usr/bin/env python3
"""M101j: registry deep-prefix alignment (matched rows, no boxes) +
data-display decoding (multi-sz join, expand-sz, NULs) + type field widths.
Dump every line as ord lists for the table rows -- console never decides.

 J1 chain base->K1->K2->K3 each with one value: what prefix does each
    level's VALUE and HEADER carry (matched, no orphan)?
 J2 deep orphan boxes (already seen bars) + matched deep inside orphan:
    bar prefix + value prefix composition
 J3 hex(7) three strings a,b,c: displayed how (NUL separators?)
 J4 hex(1) three strings (REG_SZ-typed multi): display
 J5 hex(2) expand-sz with internal NULs and trailing pair
 J6 REG_SZ with literal backslash and quotes in data
 J7 dword min/max + value name length vs type field (padding widths)
 J8 sibling key + same-name value + different case value (dup vs sibling)
 J9 base key WITHOUT header block at all (single key file: header shown?)
 J10 key with only default value: header + (默认) row
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
    "J1-chain": reg(f"[{B}\\K1\\K2\\K3]", '"x3"="3"', "",
                    f"[{B}\\K1\\K2]", '"x2"="2"', "",
                    f"[{B}\\K1]", '"x1"="1"', "",
                    f"[{B}]", '"x0"="0"'),
    "J2-deepmix": (reg(f"[{B}\\K1]", '"m"="0"', "",
                       f"[{B}\\K1\\Zx]", '"a"="1"'),
                   reg(f"[{B}\\K1]", '"m"="0"')),
    "J3-ms3": reg(f"[{B}]", '"ms"=hex(7):61,00,62,00,63,00,00,00'),
    "J4-ms1x3": reg(f"[{B}]", '"ms"=hex(1):61,00,62,00,63,00,00,00'),
    "J5-expand": reg(f"[{B}]", '"e"=hex(2):41,00,42,00,00,00'),
    "J6-escapes": reg(f"[{B}]", '"bs"="a\\\\b"', '"qt"="he said \\"q\\" ok"'),
    "J7-dword": reg(f"[{B}]", '"lo"=dword:00000000', '"hi"=dword:ffffffff'),
    "J8-sibling": (reg(f"[{B}\\a]", '"v"="1"', f"[{B}\\A]", '"w"="2"'),
                   reg(f"[{B}\\a]", '"v"="1"', f"[{B}\\A]", '"w"="2"')),
    "J9-singlekey": reg(f"[{B}]"),
    "J10-defonly": reg(f"[{B}\\Sub]", '@="dd"'),
}


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "current"
    inst = inst_mod.discover()[which]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime(
                   f"m101j-regdeep-{which}-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} locale={inst.locale}\n")

    results = []
    for tag, spec in CASES.items():
        if isinstance(spec, tuple):
            lt, rt = spec
        else:
            lt = rt = spec
        name = f"{tag}-sbs"
        lp = run_dir / "fixtures" / f"{name}-L.reg"
        rp = run_dir / "fixtures" / f"{name}-R.reg"
        lp.write_bytes(lt.encode("utf-8")); rp.write_bytes(rt.encode("utf-8"))
        script = 'registry-report layout:side-by-side output-to:"%3" "%1" "%2"'
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
            ords = [ord(ch) for ch in ln]
            # compact: show ASCII printable + mark >0x7f ranges separately
            print(f"   {i:2} {ln!r}")
            print(f"      ords={ords}")
        results.append({"tag": name, "exit": res.exit_code,
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "lines": lines})
    (run_dir / f"m101j-summary-{which}.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
