#!/usr/bin/env python3
"""M83e: pin the picture importance rule and its exact boundary.

m83d narrowed the threshold to (24, 32] and showed multi-channel deltas are
NOT summed (two channels of 20 = unimportant). Hypothesis: the rule is the
MAXIMUM per-channel delta > T.

Cells (8x8, grey base 128 unless stated):
  U1  channels (32, 30, 0)  -> max 32 -> expect 重要
  U2  channels (31, 0, 0)   -> boundary probe
  U3  channels (30, 0, 0)   -> expect 不重要
  U4  channels (25, 0, 0)   -> 不重要 (inside m83d's gap)
  U5  channels (32, 0, 0)   -> 重要 (re-pin, = m83d T-d32)
  U6  black vs white on ONE channel only (0,0,0)->(32,0,0): base independence
  U7  (128,128,128) vs (96,160,128): -32 and +32 on two channels -> 重要
  U8  alpha-only change of 32 (RGB identical) -> alpha ignored (m83c R6 said
      ignored at 128; confirm at a "would-be important" magnitude)
  U9  grayscale (color type 0) 8-bit, delta 32 -> same rule?
  U10 BMP with delta 32 on one channel -> does the SAME rule apply to BMP?

If U1..U5 confirm "max per-channel delta > T" with a stable T, the rule is
implementable; otherwise picture-report stays refused with this evidence.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m83e_picture_rule.py
"""
from __future__ import annotations

import hashlib, json, pathlib, struct, sys, zlib
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def png(width, height, pixel, color_type=6) -> bytes:
    nch = {0: 1, 2: 3, 6: 4}[color_type]
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    def px(x, y):
        v = pixel(x, y)
        return bytes(v[:nch])
    raw = b"".join(b"\x00" + b"".join(px(x, y) for x in range(width))
                   for y in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def bmp(width, height, rgb):
    row = bytes((rgb[2], rgb[1], rgb[0])) * width
    rows = row * height
    return (struct.pack("<2sIHHI", b"BM", 54 + len(rows), 0, 0, 54)
            + struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(rows), 0, 0, 0, 0)
            + rows)


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m83e-picrule-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    CASES = []
    def pair(tag, lb, rb, ct=6, ext="png"):
        if ext == "png":
            (fx / f"{tag}-L.png").write_bytes(png(8, 8, lambda x, y: lb, ct))
            (fx / f"{tag}-R.png").write_bytes(png(8, 8, lambda x, y: rb, ct))
        else:
            (fx / f"{tag}-L.bmp").write_bytes(bmp(8, 8, lb))
            (fx / f"{tag}-R.bmp").write_bytes(bmp(8, 8, rb))
        CASES.append((tag, str((fx / f"{tag}-L.{ext}").resolve()),
                      str((fx / f"{tag}-R.{ext}").resolve())))

    G = (128, 128, 128, 255)
    def shift(d):
        return tuple(max(0, min(255, G[i] + d[i])) for i in range(4))
    pair("U1-32-30", G, shift((32, 30, 0, 0)))
    pair("U2-31", G, shift((31, 0, 0, 0)))
    pair("U3-30", G, shift((30, 0, 0, 0)))
    pair("U4-25", G, shift((25, 0, 0, 0)))
    pair("U5-32", G, shift((32, 0, 0, 0)))
    pair("U6-black32", (0, 0, 0, 255), (32, 0, 0, 255))
    pair("U7-minusplus", G, (96, 160, 128, 255))
    pair("U8-alpha32", G, (128, 128, 128, 96))
    pair("U9-gray32", (128,), (160,), ct=0)
    pair("U10-bmp32", (128, 128, 128), (160, 128, 128), ext="bmp")

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

    (run_dir / "m83e-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
