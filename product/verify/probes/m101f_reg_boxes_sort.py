#!/usr/bin/env python3
"""M101f: registry orphan-box geometry, sort classes/ties, depth, misc.
Every geometry verdict comes from integer indices in the raw line (never the
console). Column probe: for each row we print the index of every non-space
"interesting" token (+, |, -+, +-, =, <>, and the right-field start).

Box family:
 F1 orphan key inside a matched parent, at END of the parent block
 F2 orphan key whose own subtree has children (nested orphan)
 F3 orphan key entirely on the RIGHT (mirror geometry)
 F4 parent key itself orphan (whole subtree missing on right)
 F5 two orphan keys in one parent (contiguity of box bars)
 F6 orphan key + orphan value under another orphan key
Sort family:
 F7 case ties: keys AA Aa aA aa
 F8 symbol zoo: & * ; < = > ? ^ ` { | } % ! + and codepoint order
 F9 '-' inside string: a-b vs ab vs a!b vs ac
 F10 CJK vs latin: 中 a Z 0 (sibling keys)
 F11 multi-char: a0/0a/aa/ab sibling ordering (does sort compare segmentwise?)
Depth/format:
 F12 depth-3 chain A/B/C under base: indent prefix for every row class
 F13 hex(7) two strings; empty hex: ; "hex:00" single byte
 F14 value name with spaces 'a b'; leading/trailing spaces in name
 F15 different roots both sides: basekey suffix
 F16 orphan KEY with no values: counted? row?
 F17 long hex continuation wraps in the DATA column
 F18 default @ on both sides vs one side only, sbs row text

Usage: cd D:\\Rea\\product\\verify && python probes/m101f_reg_boxes_sort.py
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
    # F1 orphan at END of matched parent's block (values match, orphan child last)
    "F1-orphanend": (reg(f"[{B}\\A]", '"m"="0"', "", f"[{B}\\A\\Zx]", '"a"="1"'),
                     reg(f"[{B}\\A]", '"m"="0"')),
    # F2 nested orphan subtree: A\Zx\Deeper only on left
    "F2-nested": (reg(f"[{B}\\A]", '"m"="0"', f"[{B}\\A\\Zx]", '"a"="1"',
                      f"[{B}\\A\\Zx\\Deep]", '"d"="1"'),
                  reg(f"[{B}\\A]", '"m"="0"')),
    # F3 orphan key only on the RIGHT
    "F3-rightorph": (reg(f"[{B}\\A]", '"m"="0"'),
                     reg(f"[{B}\\A]", '"m"="0"', "", f"[{B}\\A\\Zy]", '"b"="2"')),
    # F4 parent key itself orphan (missing on right)
    "F4-parentorph": (reg(f"[{B}\\Ap]", '"x"="1"', "", f"[{B}\\Ap\\Ch]", '"y"="2"'),
                      reg(f"[{B}\\Other]", '"z"="0"')),
    # F5 two orphan keys in one parent
    "F5-twoorph": (reg(f"[{B}\\A]", '"m"="0"', "", f"[{B}\\A\\K1]", '"a"="1"',
                       f"[{B}\\A\\K2]", '"b"="2"'),
                   reg(f"[{B}\\A]", '"m"="0"')),
    # F7 case ties
    "F7-casetie": (reg(f"[{B}]", "",
                       f"[{B}\\AA]", '"v"="1"', f"[{B}\\Aa]", '"v"="1"',
                       f"[{B}\\aA]", '"v"="1"', f"[{B}\\aa]", '"v"="1"'), None),
    # F8 symbol zoo (keys: one value each so headers show)
    "F8-zoo": (reg(f"[{B}\\!x]", '"v"="1"', f"[{B}\\&x]", '"v"="1"',
                   f"[{B}\\*x]", '"v"="1"', f"[{B}\\+x]", '"v"="1"',
                   f"[{B}\\;x]", '"v"="1"', f"[{B}\\<x]", '"v"="1"',
                   f"[{B}\\>x]", '"v"="1"', f"[{B}\\?x]", '"v"="1"',
                   f"[{B}\\^x]", '"v"="1"', f"[{B}\\`x]", '"v"="1"',
                   f"[{B}\\{{x]", '"v"="1"', f"[{B}\\}}x]", '"v"="1"',
                   f"[{B}\\%x]", '"v"="1"', f"[{B}\\|x]", '"v"="1"'), None),
    # F9 hyphen ignorable inside
    "F9-hyphen": (reg(f"[{B}]", "",
                      f"[{B}\\ab]", '"v"="1"', f"[{B}\\a-b]", '"v"="1"',
                      f"[{B}\\a!b]", '"v"="1"', f"[{B}\\ac]", '"v"="1"'), None),
    # F10 CJK vs latin
    "F10-cjk": (reg(f"[{B}\\中]", '"v"="1"', f"[{B}\\a]", '"v"="1"',
                    f"[{B}\\Z]", '"v"="1"', f"[{B}\\0]", '"v"="1"'), None),
    # F11 multi-char ordering
    "F11-multi": (reg(f"[{B}\\a0]", '"v"="1"', f"[{B}\\0a]", '"v"="1"',
                      f"[{B}\\aa]", '"v"="1"', f"[{B}\\ab]", '"v"="1"'), None),
    # F12 depth 3
    "F12-depth3": (reg(f"[{B}\\A\\B\\C]", '"x"="1"', f"[{B}]"), None),
    # F13 hex variants
    "F13-hex": (reg(f"[{B}]", '"ms"=hex(7):61,00,62,00,00,00',
                    '"e1"=hex:00', '"e2"=hex:', '"big"=hex:' +
                    ",".join(f"{i:02x}" for i in range(64))), None),
    # F14 spaced names
    "F14-spaces": (reg(f"[{B}]", '"a b"="1"', '"lead"="1"', '" trail"="2"'), None),
    # F15 different roots
    "F15-roots": (reg("[HKEY_LOCAL_MACHINE\\Software\\ProbeA]", '"v"="1"'),
                  reg("[HKEY_CURRENT_USER\\Software\\ProbeB]", '"v"="1"')),
    # F16 orphan key WITHOUT values
    "F16-noval": (reg(f"[{B}\\Empty]", f"[{B}]", '"z"="1"'),
                  reg(f"[{B}]", '"z"="1"')),
    # F18 default both sides, differing
    "F18-default": (reg(f"[{B}]", '@="dd"', '"v"="1"'),
                    reg(f"[{B}]", '@="ee"', '"v"="1"')),
}


def interesting_cols(line: str) -> list[tuple[str, int]]:
    hits = []
    for tok in ("+-", "-+", "<>", "|"):
        start = 0
        while True:
            j = line.find(tok, start)
            if j == -1:
                break
            hits.append((tok, j))
            start = j + 1
    # the marker token ' = ' / '<> ' region: find ' = ' too
    j = line.find(" = ")
    if j != -1:
        hits.append(("= ", j))
    j = line.find(" <> ")
    if j != -1:
        hits.append(("<>", j))
    j = line.find(" +-")
    if j != -1:
        hits.append(("+-", j))
    j = line.find("-+ ")
    if j != -1:
        hits.append(("-+", j))
    return sorted(set(hits))


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "current"
    inst = inst_mod.discover()[which]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime(
                   f"m101f-regbox-{which}-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} locale={inst.locale}\n")

    results = []
    for tag, (lt, rt) in CASES.items():
        rt = lt if rt is None else rt
        for layout in ("side-by-side", "summary"):
            if layout == "summary" and not tag.startswith(
                    ("F1", "F2", "F3", "F5", "F16", "F18", "F4")):
                continue
            name = f"{tag}-{layout[:3]}"
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
                cols = interesting_cols(ln)
                print(f"   {i:2} {ln!r}" + (f"   cols={cols}" if cols else ""))
            results.append({"tag": name, "exit": res.exit_code,
                            "bytes": len(body),
                            "sha256": hashlib.sha256(body).hexdigest(),
                            "lines": lines})
    (run_dir / f"m101f-summary-{which}.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
