#!/usr/bin/env python3
"""M101n: parser-boundary facts that must NOT be guessed.

  N1 options:bogus-token -> 106? (assumed from every channel; confirm)
  N2 options:display-all on summary (documented default spelling) -> counts
  N3 hex(3) / hex(0) / hex(4) inline type display + a dword decimal check
  N4 a valid-header file whose ONLY line after header is bad -> error line pos
  N5 value line with no trailing newline at EOF
  N6 REG_SZ with a literal CR inside quoted string
  N7 key path with a space component
  N8 two values same name under one key (dup value) -> skip?
  N9 empty file (0 bytes) -> ?
  N10 header only, no keys -> empty table / zero counts
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

# (tag, layout, script_extra, L text/bytes, R text/bytes)
CASES = [
 ("N1-bogus", "summary", " options:bogus-token",
  reg(f"[{B}]", '"v"="1"'), reg(f"[{B}]", '"v"="1"')),
 ("N2-dall-sum", "summary", " options:display-all",
  reg(f"[{B}]", '"a"="1"'), reg(f"[{B}]", '"a"="2"')),
 ("N3-types", "side-by-side", "",
  reg(f"[{B}]", '"h0"=hex(0):', '"h3"=hex(3):01,00,00,00,02',
      '"h4"=dword:0000000A', '"big"=dword:80000000'),
  None),
 ("N4-only-bad", "summary", "", reg("badline alone"), None),
 ("N5-no-final-nl", "side-by-side", "",
  HEAD5 + C + f"[{B}]" + C + '"v"="1"',  # no trailing newline
  None),
 ("N6-cr-in-string", "side-by-side", "",
  HEAD5 + C + f"[{B}]" + C + '"v"="a' + C + 'b"' + C, None),
 ("N7-space-key", "side-by-side", "",
  reg(f"[{B}\\My Key]", '"v"="1"'), None),
 ("N8-dupvalue", "summary", "",
  reg(f"[{B}]", '"v"="1"', '"v"="2"'), None),
 ("N10-headonly", "side-by-side", "", HEAD5, None),
]


def main() -> int:
    inst = inst_mod.discover()["current"]
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m101n-regparser-%Y%m%dT%H%M%SZ"))
    (run_dir / "fixtures").mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)

    # N9 empty file separately
    results = []
    for tag, layout, extra, lt, rt in CASES:
        rt = lt if rt is None else rt
        lp = run_dir / "fixtures" / f"{tag}-L.reg"
        rp = run_dir / "fixtures" / f"{tag}-R.reg"
        lp.write_bytes(lt.encode("utf-8")); rp.write_bytes(rt.encode("utf-8"))
        script = f'registry-report layout:{layout}{extra} output-to:"%3" "%1" "%2"'
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [script])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, str(lp.resolve()),
                      str(rp.resolve()), str(out), timeout=120.0,
                      script_text=script)
        body = out.read_bytes() if out.exists() else b""
        lines = body.decode("utf-8-sig", errors="replace").splitlines()
        print(f"== {tag}: exit={res.exit_code} bytes={len(body)}")
        for ln in lines:
            print("   ", repr(ln))
        results.append({"tag": tag, "script": script, "exit": res.exit_code,
                        "bytes": len(body), "lines": lines,
                        "sha256": hashlib.sha256(body).hexdigest()})

    # N9 empty file
    lp = run_dir / "fixtures" / "N9-L.reg"; rp = run_dir / "fixtures" / "N9-R.reg"
    lp.write_bytes(b""); rp.write_bytes(b"")
    script = 'registry-report layout:summary output-to:"%3" "%1" "%2"'
    sp = run_dir / "scripts" / "N9-empty.bcs"
    orc.write_script(sp, [script])
    out = run_dir / "reports" / "N9-empty.out"
    res = orc.run(inst.oracle_path, sp, str(lp.resolve()), str(rp.resolve()),
                  str(out), timeout=120.0, script_text=script)
    body = out.read_bytes() if out.exists() else b""
    print(f"== N9-empty: exit={res.exit_code} bytes={len(body)}")
    for ln in body.decode("utf-8-sig", errors="replace").splitlines():
        print("   ", repr(ln))
    results.append({"tag": "N9-empty", "exit": res.exit_code,
                    "bytes": len(body), "lines":
                    body.decode("utf-8-sig", errors="replace").splitlines()})

    (run_dir / "m101n-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
