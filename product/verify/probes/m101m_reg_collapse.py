#!/usr/bin/env python3
"""M101m: header-collapse rule for valueless intermediate keys.

Print FULL row text (no summaries) for a designed family:
  M1 base -> P (valueless, unlisted) -> C (value)            [KH-like, 1 child]
  M2 base -> P (valueless, unlisted) -> C1(v), C2(v)         [KH 2 children]
  M3 base -> P (LISTED valueless) -> C(v)                    [T9-like]
  M4 base -> P (LISTED valueless) -> C1(v), C2(v)
  M5 base(v=z) -> P(valueless unlisted) -> C1(v) C2(v)       [+ base value]
  M6 base -> P -> Q -> C (v) chain of singles unlisted
  M7 base -> P (valueless) listed, 0 children, 0 values      [G4b-like Empty]
  M8 base -> P valueless unlisted -> C valueless -> D value  [3-deep singles]
All sbs, both sides identical. Print every body line verbatim with repr.
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
 "M1": reg(f"[{B}\\P\\C]", '"v"="1"'),
 "M2": reg(f"[{B}\\P\\C1]", '"v"="1"', f"[{B}\\P\\C2]", '"v"="2"'),
 "M3": reg(f"[{B}\\P]", f"[{B}\\P\\C]", '"v"="1"'),
 "M4": reg(f"[{B}\\P]", "", f"[{B}\\P\\C1]", '"v"="1"',
           f"[{B}\\P\\C2]", '"v"="2"'),
 "M5": reg(f"[{B}]", '"z"="9"', "", f"[{B}\\P\\C1]", '"v"="1"',
           f"[{B}\\P\\C2]", '"v"="2"'),
 "M6": reg(f"[{B}\\P\\Q\\C]", '"v"="1"'),
 "M7": reg(f"[{B}\\P]", ""),
 "M8": reg(f"[{B}\\P\\Q\\R]", '"v"="1"'),
}


def main() -> int:
    inst = inst_mod.discover()["current"]
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m101m-regcollapse-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)

    results = []
    for tag, lt in CASES.items():
        lp = run_dir / "fixtures" / f"{tag}-L.reg"
        rp = run_dir / "fixtures" / f"{tag}-R.reg"
        lp.write_bytes(lt.encode("utf-8")); rp.write_bytes(lt.encode("utf-8"))
        script = 'registry-report layout:side-by-side output-to:"%3" "%1" "%2"'
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
            if ln.startswith(("注册", "已产生")):
                continue
            print(f"   {ln!r}")
        results.append({"tag": tag, "exit": res.exit_code,
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "lines": lines})
    (run_dir / "m101m-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
