#!/usr/bin/env python3
"""M101k: final geometry discriminator -- matched chains vs orphan boxes.

Hypotheses to separate:
  H1: key-header rows use plain depth-backslashes (S6/T9) -- then J1's
      '+K2'/K3 bars were orphan-box remnants??  J1 was FULLY MATCHED, so
      they cannot be.  Probe minimal matched cases to isolate the exact
      condition for '+' / '|' on MATCHED rows.

Cases (all sbs; both sides identical unless noted):
  K-A single value at base only                          (control: bare)
  K-B d1 key with value only                             ('K1' header + '\v')
  K-C d2 chain, value at d2 only (no values above)       (S6-like, expect '\B' style)
  K-D d2 chain, value at d1 AND d2                      (J1-like minimal)
  K-E d3 chain, values at every level
  K-F two d1 keys, each with one value                  (G8-like)
  K-G d1 key with value + d1 key with d2 child value    (ordering of bars?)
  K-H MATCHED d2 chain where d1 key has TWO d2 children
  K-I orphan d2 key under matched d1                    (box + backslash interplay)
  K-J matched d3 chain, no values except d4
Print ord-based prefixes.
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
    "KA": reg(f"[{B}]", '"v"="1"'),
    "KB": reg(f"[{B}\\K1]", '"v"="1"'),
    "KC": reg(f"[{B}\\K1\\K2]", '"v"="1"'),
    "KD": reg(f"[{B}\\K1]", '"m"="0"', "", f"[{B}\\K1\\K2]", '"v"="1"'),
    "KE": reg(f"[{B}\\K1\\K2\\K3]", '"v"="1"', "",
              f"[{B}\\K1\\K2]", '"m2"="2"', "",
              f"[{B}\\K1]", '"m1"="1"'),
    "KF": reg(f"[{B}\\K1]", '"a"="1"', "", f"[{B}\\K2]", '"b"="2"'),
    "KG": reg(f"[{B}\\K1]", '"a"="1"', "",
              f"[{B}\\K2\\K2a]", '"b"="2"'),
    "KH": reg(f"[{B}\\K1\\Ka]", '"x"="1"', "",
              f"[{B}\\K1\\Kb]", '"y"="2"'),
    "KJ": reg(f"[{B}\\K1\\K2\\K3]", '"v"="1"'),
}
PAIRS = {
    "KI": (reg(f"[{B}\\K1]", '"m"="0"', "", f"[{B}\\K1\\Z]", '"a"="1"'),
           reg(f"[{B}\\K1]", '"m"="0"')),
}


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m101k-reggeom2-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)

    results = []
    for tag, spec in list(CASES.items()) + list(PAIRS.items()):
        lt, rt = spec if isinstance(spec, tuple) else (spec, spec)
        lp = run_dir / "fixtures" / f"{tag}-L.reg"
        rp = run_dir / "fixtures" / f"{tag}-R.reg"
        lp.write_bytes(lt.encode("utf-8")); rp.write_bytes(rt.encode("utf-8"))
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
            if ln.startswith(("注册", "已产生", "模式", "左边文件", "右边文件")):
                continue
            pre = []
            for ch in ln:
                if ch in "+|\\<=>":
                    pre.append(ch)
                elif ch == " " and (pre and pre[-1] in "+|\\"):
                    continue
                else:
                    break
            print(f"   {ln!r}  prefix={''.join(pre)!r}")
        results.append({"tag": tag, "exit": res.exit_code, "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(), "lines": lines})
    (run_dir / "m101k-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
