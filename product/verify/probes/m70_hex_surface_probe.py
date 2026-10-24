#!/usr/bin/env python3
"""M7-pre (m70): pin the hex-channel CLI surface of the Oracle.

The help corpus documents a GUI "Hex Compare Report" (commandshex.html) but
never names a scripting verb; the feature matrix (U5) assumed `hex-report`.
Before ANY implementation, measure the accept/refuse surface directly, in
the exact m63 style (raw subprocess, deliberate error counts, per-call
residue kill):

  H1  `hex-report output-to:"%3" "%1" "%2"`      -- verb exists at all?
  H2  `hex-report layout:side-by-side ...`        -- layout arg accepted?
  H3  `file-report output-to ...`                 -- other plausible verbs
  H4  `binary-report ...`                          (exit 105 unknown-command
  H5  `hex-report` zero files                      vs 106 bad-arg tells the
  H6  `data-report` on two BINARY files            table channel's fallback
                                                   for .bin inputs)
  H7  plain `load:left/right` + `hex-report` two-line form

Fixtures: BIN pair = 64-byte files differing in a few bytes + one length
difference (so both a changed run and an orphan region exist).

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m70_hex_surface_probe.py
"""
from __future__ import annotations
import json, pathlib, subprocess, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m70-hexsurface-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)

    # Binary fixtures: left 64 bytes, right 60 bytes; changed bytes at
    # offsets 0x03-0x04 and 0x10; right truncated tail.
    left = bytearray(range(64))
    right = bytearray(range(64))[:60]
    right[0x03] = 0xFF; right[0x04] = 0xFE
    lp = fx / "B-L.bin"; rp = fx / "B-R.bin"
    lp.write_bytes(bytes(left)); rp.write_bytes(bytes(right))

    CASES = [
        # (tag, script lines, nfiles)
        ("H1-bare",      ['hex-report output-to:"%3" "%1" "%2"'], 2),
        ("H2-layout",    ['hex-report layout:side-by-side output-to:"%3" "%1" "%2"'], 2),
        ("H3-filereport", ['file-report output-to:"%3" "%1" "%2"'], 2),
        ("H4-binary",    ['binary-report output-to:"%3" "%1" "%2"'], 2),
        ("H5-nofiles",   ['hex-report output-to:"%3"'], 0),
        ("H6-data-bin",  ['data-report layout:side-by-side output-to:"%3" "%1" "%2"'], 2),
        ("H7-twoline",   ['load:left "%1"', 'load:right "%2"',
                          'hex-report output-to:"%3"'], 2),
    ]

    results = []
    for tag, lines, nfiles in CASES:
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        out = run_dir / "reports" / f"{tag}.out"
        if out.exists():
            out.unlink()
        files = [str(lp.resolve()), str(rp.resolve())][:nfiles]
        argv = [str(inst.oracle_path), "/silent", f"@{script}"] + files + \
               [str(out.resolve())]
        proc = subprocess.run(argv, cwd=str(pathlib.Path(inst.oracle_path).parent),
                              capture_output=True, timeout=120)
        body = out.read_bytes() if out.exists() else b""
        rec = {"tag": tag, "lines": lines, "exit": proc.returncode,
               "stdout": proc.stdout.decode("utf-8", errors="replace")[:300],
               "stderr": proc.stderr.decode("utf-8", errors="replace")[:300],
               "report_bytes": len(body),
               "report_head": body[:600].decode("utf-8-sig", errors="replace")}
        results.append(rec)
        print(f"{tag:13} exit={proc.returncode:4} bytes={len(body):6}")
        for ln in rec["report_head"].splitlines()[:12]:
            if ln.strip():
                print("   ", repr(ln))
        r = subprocess.run(["tasklist"], capture_output=True, text=True)
        if "BComp" in r.stdout or "BCompare" in r.stdout:
            print("  RESIDUE DETECTED -- killing")
            subprocess.run(["taskkill", "/F", "/IM", "BComp.com"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "BCompare.exe"], capture_output=True)

    (run_dir / "m70-hexsurface.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
