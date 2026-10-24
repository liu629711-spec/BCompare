#!/usr/bin/env python3
"""M101i: registry last-labels + ignore-semantics batch, run against BOTH
installs (pass the key as argv[1]) so the label pairs land in one comparison.

Cells:
  I1 summary+ignore on trailing-SPACE value pair (similar class? header?)
  I2 summary+ignore on CASE-differing pair
  I3 sbs+ignore default pair with values (header line? boxes?)
  I4 sbs+display-mismatches on orphan-box fixture (marker filtering)
  I5 summary parse-error side (English error line forms)
  I6 summary delete/dup line (English)
  I7 summary png pair -> encoding error line (English)
  I8 sbs zero-length hex + default value (English placeholders)
  I9 summary hex(7)/hex(1) pair -- similar or important when strings differ?
 I10 default-vs-missing @ on one side (count shape)
 I11 summary+display-matches (mode line? counts?)
 I12 sbs display-mismatches on matched+orphan (which rows drop)
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
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40

PAIRS = {
    "I1-space-ignore": ("summary", " options:ignore-unimportant",
                        reg(f"[{B}]", '"v"="x "'), reg(f"[{B}]", '"v"="x"')),
    "I2-case-ignore": ("summary", " options:ignore-unimportant",
                       reg(f"[{B}]", '"v"="Alpha"'), reg(f"[{B}]", '"v"="alpha"')),
    "I3-sbs-ignore": ("side-by-side", " options:ignore-unimportant",
                      reg(f"[{B}]", '"a"="1"', '"b"="x "', '"c"="3"'),
                      reg(f"[{B}]", '"a"="1"', '"b"="x"', '"c"="4"')),
    "I4-sbs-dmism-box": ("side-by-side", " options:display-mismatches",
                         reg(f"[{B}]", '"z"="1"', "", f"[{B}\\Kx]", '"a"="1"', '"b"="2"'),
                         reg(f"[{B}]", '"z"="1"')),
    "I5-parseerr": ("summary", "",
                    reg(f"[{B}]", '"v"="1"', "garbage line here"),
                    reg(f"[{B}]", '"v"="1"')),
    "I6-deletedup": ("summary", "",
                     reg(f"[-{B}\\Gone]", f"[{B}\\Dup]", '"v"="1"', f"[{B}\\Dup]", '"v"="1"'),
                     reg(f"[{B}\\Dup]", '"v"="1"')),
    "I8-zerolen-default": ("side-by-side", "",
                           reg(f"[{B}\\Sub]", "@=\"dd\"", '"e2"=hex:'),
                           reg(f"[{B}\\Sub]", "@=\"dd\"", '"e2"=hex:')),
    "I9-multi-diff": ("summary", "",
                      reg(f"[{B}]", '"ms"=hex(7):61,00,62,00,00,00'),
                      reg(f"[{B}]", '"ms"=hex(7):63,00,62,00,00,00')),
    "I10-default-vs-missing": ("summary", "",
                               reg(f"[{B}]", '@="dd"', '"v"="1"'),
                               reg(f"[{B}]", '"v"="1"')),
    "I11-sum-dmatch": ("summary", " options:display-matches",
                       reg(f"[{B}]", '"a"="1"'), reg(f"[{B}]", '"a"="2"')),
    "I12-sbs-dmatch": ("side-by-side", " options:display-matches",
                       reg(f"[{B}]", '"z"="1"', "", f"[{B}\\Kx]", '"a"="1"'),
                       reg(f"[{B}]", '"z"="1"')),
}


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "current"
    inst = inst_mod.discover()[which]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime(
                   f"m101i-reglabels-{which}-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} locale={inst.locale}\n")

    results = []
    for tag, (layout, extra, lt, rt) in PAIRS.items():
        script = f'registry-report layout:{layout}{extra} output-to:"%3" "%1" "%2"'
        lp = run_dir / "fixtures" / f"{tag}-L.reg"
        rp = run_dir / "fixtures" / f"{tag}-R.reg"
        lp.write_bytes(lt.encode("utf-8"))
        rp.write_bytes(rt.encode("utf-8"))
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [script])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, str(lp.resolve()),
                      str(rp.resolve()), str(out), timeout=120.0,
                      script_text=script)
        body = out.read_bytes() if out.exists() else b""
        lines = body.decode("utf-8-sig", errors="replace").splitlines()
        print(f"== {tag}: exit={res.exit_code}")
        for ln in lines:
            print("   ", repr(ln))
        results.append({"tag": tag, "script": script, "exit": res.exit_code,
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "lines": lines})

    # I7: PNG pair through registry (encoding error line)
    script = 'registry-report layout:summary output-to:"%3" "%1" "%2"'
    lp = run_dir / "fixtures" / "I7-L.png"; rp = run_dir / "fixtures" / "I7-R.png"
    lp.write_bytes(PNG); rp.write_bytes(PNG)
    sp = run_dir / "scripts" / "I7-png.bcs"
    orc.write_script(sp, [script])
    out = run_dir / "reports" / "I7-png.out"
    res = orc.run(inst.oracle_path, sp, str(lp.resolve()), str(rp.resolve()),
                  str(out), timeout=120.0, script_text=script)
    body = out.read_bytes() if out.exists() else b""
    lines = body.decode("utf-8-sig", errors="replace").splitlines()
    print(f"== I7-png: exit={res.exit_code}")
    for ln in lines:
        print("   ", repr(ln))
    results.append({"tag": "I7-png", "script": script, "exit": res.exit_code,
                    "bytes": len(body), "lines": lines,
                    "sha256": hashlib.sha256(body).hexdigest()})

    (run_dir / f"m101i-summary-{which}.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
