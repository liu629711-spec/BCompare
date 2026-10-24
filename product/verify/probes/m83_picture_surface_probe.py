#!/usr/bin/env python3
"""M83: the picture-report surface (function 7, picture compare).

Public grammar (help/scripting_reference.html, PICTURE-REPORT):
    picture-report layout:<layout> [options:<opts>] [title:<t>]
                   output-to:(printer|clipboard|<file>) [output-options:<o>]
                   [<comparison>]
    layout = side-by-side | summary

Open questions, one cell each (serial Oracle, Job-Object containment):
  P1  two identical PNGs, side-by-side: does it run at all (exit 0) and what
      does the frame look like? (Does BC need a real image decoder?)
  P2  two DIFFERENT PNGs, side-by-side.
  P3  summary layout, same pair.
  P4  layout:bogus -> exit code (expect 106 like the other channels?).
  P5  no layout -> exit code (H1 precedent: hex-report without layout = 106).
  P6  options:<anything> -> 105 (table) or 106 (hex) or 0 (text)? WHICH channel
      does the picture channel's refuse surface follow?
  P7  output-options:html-* -> 106 (the shared refuse) or something else?
  P8  zero files (with layout) -> exit? (table=107, hex=107)
  P9  one file -> exit? (table=106, hex=106)
  P10 missing left file (nonexistent path) -> ? (hex=106)
  P11 title: replaces the frame's first line? (X4/V3 precedent)
  P12 a NON-image file (.txt/.bin) with layout: accepted? hex channel refused
      data-report on .bin with an encoding error; picture may do likewise.
  P13 bogus layout name vs a supported one -- enumerate what is accepted.

Fixtures: real minimal PNGs generated with zlib (no PIL dependency).

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m83_picture_surface_probe.py
"""
from __future__ import annotations

import hashlib, json, pathlib, struct, sys, zlib
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """A minimal RGB PNG of one solid colour (no external deps)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m83-picture-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    # Three fixtures: identical pair basis, a differing pixel, a non-image.
    (fx / "P-L.png").write_bytes(png(8, 8, (255, 0, 0)))
    (fx / "P-R.png").write_bytes(png(8, 8, (255, 0, 0)))
    (fx / "D-L.png").write_bytes(png(8, 8, (255, 0, 0)))
    (fx / "D-R.png").write_bytes(png(8, 8, (0, 0, 255)))
    (fx / "n-L.bin").write_bytes(b"\x00\x01\x02\x03")
    (fx / "n-R.bin").write_bytes(b"\x00\x01\x02\x04")
    L, R = str((fx / "P-L.png").resolve()), str((fx / "P-R.png").resolve())
    DL, DR = str((fx / "D-L.png").resolve()), str((fx / "D-R.png").resolve())
    NL, NR = str((fx / "n-L.bin").resolve()), str((fx / "n-R.bin").resolve())

    def line(lay, extra=""):
        return f'picture-report layout:{lay}{extra} output-to:"%3" "%1" "%2"'

    CASES = [
        ("P1-sbs-equal", ["side-by-side", ""], L, R),
        ("P2-sbs-diff", ["side-by-side", ""], DL, DR),
        ("P3-sum-diff", ["summary", ""], DL, DR),
        ("P4-bogus-layout", ["bogus", ""], L, R),
        ("P6-options", ["side-by-side", " options:display-mismatches"], L, R),
        ("P7-output-options", ["side-by-side", " output-options:html-embed"], L, R),
        ("P11-title", ["side-by-side", ' title:"PicTitle"'], DL, DR),
        ("P12-nonimage", ["side-by-side", ""], NL, NR),
    ]
    # P5 (no layout) and the file-count cells need a hand-written line.
    RAW = [
        ("P5-no-layout", 'picture-report output-to:"%3" "%1" "%2"', L, R, True),
        ("P8-zero-files", 'picture-report layout:side-by-side output-to:"%3"', "", "", True),
        ("P9-one-file", 'picture-report layout:side-by-side output-to:"%3" "%1"', L, "", True),
        ("P10-missing-left", 'picture-report layout:side-by-side output-to:"%3" "%1" "%2"',
         str(fx / "NOPE-L.png"), str(fx / "NOPE-R.png"), True),
    ]

    results = []
    for tag, (lay, extra), l, r in CASES:
        ln = line(lay, extra)
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [ln])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        print(f"{tag}: exit={res.exit_code} bytes={len(body)}")
        head = body.decode("utf-8-sig", errors="replace").splitlines()[:12]
        for h in head:
            print("   ", repr(h))
        results.append({"tag": tag, "script": ln, "exit": res.exit_code,
                        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                        "head": head})
    for tag, ln, l, r, _ in RAW:
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [ln])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        print(f"{tag}: exit={res.exit_code} bytes={len(body)}")
        head = body.decode("utf-8-sig", errors="replace").splitlines()[:8]
        for h in head:
            print("   ", repr(h))
        results.append({"tag": tag, "script": ln, "exit": res.exit_code,
                        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                        "head": head})

    (run_dir / "m83-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
