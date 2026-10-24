#!/usr/bin/env python3
"""M83d: bisect Picture Compare's importance threshold, and the channel rule.

m83c: delta 1 and 10 -> 不重要; delta 64 and 100 -> 重要. So the threshold
sits in (10, 64]. Also measured: alpha is ignored (64 same), and a size
difference yields 左边独有像素 for the surplus pixels.

Cells:
  T1..T6  single-channel deltas 16, 24, 32, 40, 48, 56 on a grey base.
  T7      delta 24 spread over THREE channels (8 each) -> additive or per-channel?
  T8      delta 20 on two channels (20 each) -> ?
  T9      black vs white (delta 255 on all three) -> important (control)
  T10     the SAME delta on a mid-grey base vs a saturated base (255,0,0):
          does the threshold depend on the base colour (perceptual)?
  T11     delta exactly at the discovered boundary, re-run twice (repro).

If the boundary is a clean integer and base-independent, the product can
implement it; otherwise it is a residual unknown and picture-report stays
refused with the measured evidence.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m83d_picture_bisect.py
"""
from __future__ import annotations

import hashlib, json, pathlib, struct, sys, zlib
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def png_rgba(width, height, pixel) -> bytes:
    def chunk(tag, data):
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
               datetime.now(timezone.utc).strftime("m83d-picbisect-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    grey = (128, 128, 128, 255)
    def shift(base, deltas):
        def p(x, y):
            return tuple(max(0, min(255, base[i] + deltas[i])) for i in range(4))
        return p

    CASES = []
    def pair(tag, left_base, deltas, right_base=None):
        (fx / f"{tag}-L.png").write_bytes(png_rgba(8, 8, lambda x, y: left_base))
        rb = right_base or tuple(max(0, min(255, left_base[i] + deltas[i]))
                                 for i in range(4))
        (fx / f"{tag}-R.png").write_bytes(png_rgba(8, 8, lambda x, y: rb))
        CASES.append((tag, str((fx / f"{tag}-L.png").resolve()),
                      str((fx / f"{tag}-R.png").resolve())))

    for d in (16, 24, 32, 40, 48, 56):
        pair(f"T-d{d}", grey, (d, 0, 0, 0))
    pair("T7-three8", grey, (8, 8, 8, 0))
    pair("T8-two20", grey, (20, 20, 0, 0))
    pair("T9-bw", (0, 0, 0, 255), (255, 255, 255, 0))
    pair("T10-sat", (255, 0, 0, 255), (0, 32, 0, 0))   # delta 32 on a saturated base
    pair("T11a-32rep", grey, (32, 0, 0, 0))
    pair("T11b-24rep", grey, (24, 0, 0, 0))

    results = []
    for tag, l, r in CASES:
        ln = 'picture-report layout:summary output-to:"%3" "%1" "%2"'
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [ln])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        counts = [x for x in body.decode("utf-8-sig", errors="replace").splitlines()
                  if "像素" in x and "文件" not in x]
        print(f"{tag}: exit={res.exit_code}  {counts}")
        results.append({"tag": tag, "exit": res.exit_code, "counts": counts})

    (run_dir / "m83d-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
