#!/usr/bin/env python3
"""M101e: S5 orphan-key geometry dissection + sort prefix zone + display
width question (CJK names), + English-reference label corroboration batch.

 E1 S5b: orphan key "Kx" with ONE value "a", basekey has a normal value
    "z" -- exact marker columns via find() on the raw line
 E2 S5c: orphan key at depth 2 (A\Kx), value under it
 E3 S5d: both sides have the key, only it orphan VALUES (control)
 E4 CJK: key/value names with Chinese chars -- column width in chars vs
    display cells (compare to ASCII width)
 E5 sort zone: sibling keys "~t","-t",".t","(t","@t","[t","#t","$t" --
    linguistic prefix ordering (product must reproduce ONE total order;
    anything the measure does not pin down = residual unknown, fallback
    documented)
 E6 orphan-key header line byte-ords when name column is wide
 E7 summary count for orphan key values (count == values only, again)

Usage: cd D:\\Rea\\product\\verify && python probes/m101e_reg_orphankey.py
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
    "E1-orphkey1v": (reg(f"[{B}\\Kx]", '"a"="1"', "", f"[{B}]", '"z"="2"'),
                     reg(f"[{B}]", '"z"="2"')),
    "E2-orphkey2d": (reg(f"[{B}\\A\\Kx]", '"a"="1"', "", f"[{B}\\A]", '"m"="0"',
                         "", f"[{B}]", '"z"="2"'),
                     reg(f"[{B}\\A]", '"m"="0"', "", f"[{B}]", '"z"="2"')),
    "E3-orphval-only": (reg(f"[{B}]", '"a"="1"', '"z"="2"'),
                        reg(f"[{B}]", '"z"="2"')),
    "E4-cjk": (reg(f"[{B}]", '"名称"="值"', '"az"="1"'), None),
    "E5-sortzone": (reg(
        f"[{B}\\~t]", '"v"="1"', "", f"[{B}\\-t]", '"v"="1"', "",
        f"[{B}\\.t]", '"v"="1"', "", f"[{B}\\(t]", '"v"="1"', "",
        f"[{B}\\@t]", '"v"="1"', "", f"[{B}\\[t]", '"v"="1"', "",
        f"[{B}\\#t]", '"v"="1"', "", f"[{B}\\$t]", '"v"="1"', "",
        f"[{B}\\9t]", '"v"="1"', "", f"[{B}\\_t]", '"v"="1"', "",
        f"[{B}\\at]", '"v"="1"'), None),
}

def dump(inst, run_dir, tag, script, lt, rt, layout):
    fx = run_dir / "fixtures"; fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    (run_dir / "scripts").mkdir(parents=True, exist_ok=True)
    lp = fx / f"{tag}-L.reg"; rp = fx / f"{tag}-R.reg"
    lp.write_bytes(lt.encode("utf-8")); rp.write_bytes(rt.encode("utf-8"))
    sp = run_dir / "scripts" / f"{tag}.bcs"
    orc.write_script(sp, [script])
    out = run_dir / "reports" / f"{tag}.out"
    res = orc.run(inst.oracle_path, sp, str(lp.resolve()), str(rp.resolve()),
                  str(out), timeout=120.0, script_text=script)
    body = out.read_bytes() if out.exists() else b""
    lines = body.decode("utf-8-sig", errors="replace").splitlines()
    print(f"== {tag}: exit={res.exit_code}")
    for i, ln in enumerate(lines):
        print(f"   {i:2} {ln!r}")
        # integer column map of every marker token in this line
        for tok in ("+-", "-+", "<>", "=", "@"):
            j = ln.find(tok)
            if j != -1 and not ln.startswith(("已产生", "左边", "右边", "基点")):
                print(f"         tok {tok!r}@{j} (len={len(ln)})")
    return {"tag": tag, "exit": res.exit_code, "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(), "lines": lines}


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "current"
    inst = inst_mod.discover()[which]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime(
                   f"m101e-regorphkey-{which}-%Y%m%dT%H%M%SZ"))
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version}) locale={inst.locale}\n")

    results = []
    for tag, (lt, rt) in CASES.items():
        rt = lt if rt is None else rt
        for layout in ("side-by-side", "summary"):
            if tag.startswith(("E4", "E5", "E2")) and layout == "summary":
                continue
            script = f'registry-report layout:{layout} output-to:"%3" "%1" "%2"'
            results.append(dump(inst, run_dir, f"{tag}-{layout[:3]}",
                                script, lt, rt, layout))
    (run_dir / f"m101e-summary-{which}.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
