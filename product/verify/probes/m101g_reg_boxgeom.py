#!/usr/bin/env python3
"""M101g: registry orphan-box geometry, nailed by column ordinals.

The S5/F1/F2 comparison showed:
  - orphan KEY, 1 value, no nested orphan  -> '\\a ... +-'  (NO box char)
  - orphan KEY, 2 values                   -> '+a' then '\\b' (box top '+')
  - orphan KEY + nested orphan child        -> '+Deep' header + '|\\d' bar rows
  - orphan VALUE alone                      -> plain '+-' marker rows
So a box (top '+', bars '|') is drawn over the span of an orphan group WHEN
THE GROUP HAS >=2 ROWS, but its exact extent (which row gets '+', which get
'|', which nothing) needs row-index + column-index dumps. Every verdict here
is printed as (row_index, col_index, char) triples -- ints, never console
guesses.

Also pins:
  T1 hex continuation WITH trailing comma (regedit's real long-value format)
  T2 string continuation proper regedit form
  T3 orphan key whose name sorts BETWEEN matched siblings (row position)
  T4 matched key containing one orphan value at start and one at end
  T5 orphan key 3 values (bar count)
  T6 nested orphan two levels (Zx\Deep\Deeper)
  T7 right-side mirror boxes
  T8 orphan key + orphan value in same subtree
  T9 box with only children-keys (no direct values on orphan key)
  T10 CJK orphan key box (width interplay)

Usage: cd D:\\Rea\\product\\verify && python probes/m101g_reg_boxgeom.py
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


def dump_table(lines: list[str]) -> None:
    """Print every table row with its character-index specials as ints."""
    for i, ln in enumerate(lines):
        if ln.startswith("已产生") or "文件：" in ln or ln.startswith(("注册", "模式")):
            continue
        if set(ln) == {"-"}:
            print(f"   [{i}] RULE len={len(ln)}")
            continue
        if ln.startswith("名称"):
            print(f"   [{i}] HEADER {ln!r}")
            continue
        specials = [(ch, j) for j, ch in enumerate(ln)
                    if ch in "+-|\\<>="]
        print(f"   [{i}] len={len(ln)} specials={specials}")


CASES = {
    # T5 orphan key, 3 values -> box extent
    "T5-threevals": (reg(f"[{B}]", '"z"="1"', "",
                         f"[{B}\\Kx]", '"a"="1"', '"b"="2"', '"c"="3"'),
                     reg(f"[{B}]", '"z"="1"')),
    # T10/T9 orphan key with NO direct values, but a value child
    "T9-keychild": (reg(f"[{B}]", '"z"="1"', "",
                        f"[{B}\\Kx]", f"[{B}\\Kx\\Ch]", '"a"="1"'),
                    reg(f"[{B}]", '"z"="1"')),
    # T6 nested orphan two levels
    "T6-nest2": (reg(f"[{B}]", '"z"="1"', "",
                     f"[{B}\\Kx]", '"a"="1"', f"[{B}\\Kx\\Dp]", '"b"="2"',
                     f"[{B}\\Kx\\Dp\\Dp2]", '"c"="3"'),
                 reg(f"[{B}]", '"z"="1"')),
    # T7 right mirror box (2 values)
    "T7-rightbox": (reg(f"[{B}]", '"z"="1"'),
                    reg(f"[{B}]", '"z"="1"', "",
                        f"[{B}\\Ky]", '"a"="1"', '"b"="2"')),
    # T8 orphan key + orphan value in same file
    "T8-mixed": (reg(f"[{B}]", '"z"="1"', '"orphanval"="2"', "",
                     f"[{B}\\Kx]", '"a"="1"', '"b"="2"'),
                 reg(f"[{B}]", '"z"="1"')),
    # T3 orphan sorts between siblings
    "T3-between": (reg(f"[{B}]", "", f"[{B}\\Am]", '"x"="1"',
                       f"[{B}\\Zm]", '"y"="1"', f"[{B}\\Mid]", '"m"="1"'),
                   reg(f"[{B}]", "", f"[{B}\\Am]", '"x"="1"',
                       f"[{B}\\Zm]", '"y"="1"')),
    # T4 matched key, orphan values at start and end
    "T4-endpoints": (reg(f"[{B}]", '"a1"="1"', '"z"="2"', '"z9"="3"'),
                     reg(f"[{B}]", '"z"="2"')),
    # T1 hex continuation with trailing comma (real regedit format)
    "T1-comma": (reg(f"[{B}]", '"Blob"=hex:68,65,6c,6c,6f,',
                     '  2c,20,77,6f,72,6c,64'),
                 reg(f"[{B}]", '"Blob"=hex:68,65,6c,6c,6f,2c,20,77,6f,72,6c,64')),
    # T2 string continuation (regedit form: quoted segments)
    "T2-strcont": (reg(f"[{B}]", '"s"="aaa"', '  "bbb"'),
                    reg(f"[{B}]", '"s"="aaabbb"')),
}


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "current"
    inst = inst_mod.discover()[which]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime(
                   f"m101g-regboxgeom-{which}-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} locale={inst.locale}\n")

    results = []
    for tag, (lt, rt) in CASES.items():
        name = f"{tag}-sbs"
        lp = run_dir / "fixtures" / f"{name}-L.reg"
        rp = run_dir / "fixtures" / f"{name}-R.reg"
        lp.write_bytes(lt.encode("utf-8")); rp.write_bytes(rt.encode("utf-8"))
        script = f'registry-report layout:side-by-side output-to:"%3" "%1" "%2"'
        sp = run_dir / "scripts" / f"{name}.bcs"
        orc.write_script(sp, [script])
        out = run_dir / "reports" / f"{name}.out"
        res = orc.run(inst.oracle_path, sp, str(lp.resolve()),
                      str(rp.resolve()), str(out), timeout=120.0,
                      script_text=script)
        body = out.read_bytes() if out.exists() else b""
        lines = body.decode("utf-8-sig", errors="replace").splitlines()
        print(f"== {name}: exit={res.exit_code}")
        for i, ln in enumerate(lines[:6]):
            print(f"   hdr {i}: {ln!r}")
        dump_table(lines)
        results.append({"tag": name, "exit": res.exit_code, "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "lines": lines})
    (run_dir / f"m101g-summary-{which}.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
