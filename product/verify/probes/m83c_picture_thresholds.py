#!/usr/bin/env python3
"""M83c: is Picture Compare's "important difference" rule measurable?

The count line says `N 个重要差异像素` (important differing pixels) and
`N 个相同像素`. Before implementing anything, establish whether "important" is
a threshold BC applies to per-pixel colour distance. If it is a tolerance the
product cannot derive from these probes, the honest outcome is a recorded
residual unknown rather than a guessed constant.

Cells (all 8x8 PNGs, so 64 pixels total and N is easy to read):
  R1  all 64 pixels differ by 1 in ONE channel  -> 64 or 0? (tiny delta)
  R2  all 64 differ by 10 in one channel        -> ?
  R3  all 64 differ by 64 in one channel        -> ?
  R4  all 64 differ by 255 in one channel       -> ? (expect 64)
  R5  32 px differ by 255, 32 px identical      -> expect "32 个相同" + "32 个重要差异"
  R6  differing alpha (same RGB)                -> alpha counted?
  R7  size differs (8x8 vs 4x4): m83b saw 左边独有像素 for the mixed-type
      case; here both are PNGs -> same/left-only/right-only counts?
  R8  a GIF pair (if the loader supports it) -- format coverage probe.

Every count line is read verbatim; no interpretation without the number.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m83c_picture_thresholds.py
"""
from __future__ import annotations

import hashlib, json, pathlib, struct, sys, zlib
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def png_rgba(width: int, height: int, pixel) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + b"".join(bytes(pixel(x, y)) for x in range(width))
                   for y in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m83c-picthresh-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    base = (100, 100, 100, 255)
    def mk(delta: int, channel: int):
        def p(x, y):
            c = list(base)
            c[channel] = max(0, min(255, c[channel] + delta))
            return tuple(c)
        return p
    def half(delta: int):
        def p(x, y):
            return (255, 0, 0, 255) if (x + y) % 2 == 0 else tuple(base)
        return p

    CASES = []
    def pair(tag, lp, rp, w=8, h=8, w2=None, h2=None):
        (fx / f"{tag}-L.png").write_bytes(png_rgba(w, h, lp))
        (fx / f"{tag}-R.png").write_bytes(png_rgba(w2 or w, h2 or h, rp))
        CASES.append((tag, str((fx / f"{tag}-L.png").resolve()),
                      str((fx / f"{tag}-R.png").resolve())))

    solid = lambda x, y: base
    pair("R1-d1", solid, mk(1, 0))
    pair("R2-d10", solid, mk(10, 0))
    pair("R3-d64", solid, mk(64, 0))
    pair("R4-d255", solid, mk(-155, 0))          # 100 -> 0 (delta 100)
    pair("R5-half", solid, half(255))
    pair("R6-alpha", solid, lambda x, y: (100, 100, 100, 128))
    pair("R7-size", solid, solid, 8, 8, 4, 4)

    results = []
    for tag, l, r in CASES:
        ln = 'picture-report layout:summary output-to:"%3" "%1" "%2"'
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [ln])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        text = body.decode("utf-8-sig", errors="replace")
        counts = [x for x in text.splitlines()
                  if ("像素" in x and "文件" not in x)]
        print(f"{tag}: exit={res.exit_code}  {counts}")
        results.append({"tag": tag, "exit": res.exit_code, "counts": counts,
                        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})

    (run_dir / "m83c-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
