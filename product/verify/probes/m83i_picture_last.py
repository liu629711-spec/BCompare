#!/usr/bin/env python3
"""M83i: the last three picture cells -- right-only order, ignore semantics, GIF.

m83h gave the 4-category order: 相同 -> 不重要 -> 左边独有 -> 重要.

  V1  right-only, full spread: left 8x6, right 8x8, overlap has same+imp+unimp
      so 右边独有 lands -- its position in the order (vs 左边独有 and 重要).
  V2  options:ignore-unimportant on a pair that has BOTH important and
      unimportant -- does the 不重要 line DISAPPEAR (ignore), and does the
      count still say 重要?
  V3  GIF pair (a real 1-frame GIF, solid colour): supported?
  V4  JPEG minimal 1x1 -> supported? (only if cheap; else note unsupported)
  V5  left-only AND right-only TOGETHER (8x6 L vs 8x6 R with a 1px shift --
      both sides have surplus): order of 左独有 vs 右独有.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m83i_picture_last.py
"""
from __future__ import annotations
import hashlib, json, pathlib, struct, sys, zlib
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea"); sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def png(w, h, pix):
    def chunk(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + b"".join(bytes(pix(x, y)) for x in range(w))
                   for y in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def gif_solid(w, h, rgb):
    """Minimal static GIF (global colour table, one entry = the solid colour)."""
    gct = bytes(rgb)
    return (b"GIF89a" + struct.pack("<HH", w, h) + bytes([0x80, 0, 0])
            + gct
            + bytes([0x2C]) + struct.pack("<HHHH", 0, 0, w, h) + bytes([0])
            + b"\x02\x02\x44\x01\x00"      # LZW min-code 2, one 4-byte block
            + bytes([0x3B]))


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    rd = (REA / "product" / "verify" / "runs" /
          datetime.now(timezone.utc).strftime("m83i-piclast-%Y%m%dT%H%M%SZ"))
    fx = rd / "fixtures"; fx.mkdir(parents=True)
    (rd / "scripts").mkdir(parents=True); (rd / "reports").mkdir(parents=True)
    G = (128, 128, 128)

    def band(x, y):   # same/imp/unimp columns, for the overlap
        return G if x < 2 else ((158, 128, 128) if x < 4 else (148, 128, 128))
    def base128(x, y):
        return (128, 128, 128)

    # V1: left 8x6, right 8x8 (right has 2 surplus rows).
    (fx / "V1-L.png").write_bytes(png(8, 6, band))
    (fx / "V1-R.png").write_bytes(png(8, 8, base128))
    # V2: imp + unimp pair for ignore semantics.
    (fx / "V2-L.png").write_bytes(png(8, 8, band))
    (fx / "V2-R.png").write_bytes(png(8, 8, base128))
    # V3: GIF solid, equal and differing.
    (fx / "V3a-L.gif").write_bytes(gif_solid(4, 4, (128, 128, 128)))
    (fx / "V3a-R.gif").write_bytes(gif_solid(4, 4, (128, 128, 128)))
    (fx / "V3b-L.gif").write_bytes(gif_solid(4, 4, (0, 0, 0)))
    (fx / "V3b-R.gif").write_bytes(gif_solid(4, 4, (255, 255, 255)))
    # V5: 1px shift both sides (8x6 vs 8x6 won't give surplus... use 8x8 vs 8x6
    # with left shorter by top, right shorter by bottom):
    # simplest: L 6x8 (6 wide), R 8x8 -> right has 2 surplus cols; combine with a
    # diff to also show important. Use V5 = L 6x8 band vs R 8x8 base128.
    (fx / "V5-L.png").write_bytes(png(6, 8, band))
    (fx / "V5-R.png").write_bytes(png(8, 8, base128))

    def run(tag, ln, l, r):
        sp = rd / "scripts" / f"{tag}.bcs"; orc.write_script(sp, [ln])
        out = rd / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, str((fx / l).resolve()),
                      str((fx / r).resolve()), str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        lines = body.decode("utf-8-sig", errors="replace").splitlines()
        counts = [s for s in lines if ("像素" in s or "错误" in s or "忽略" in s)]
        print(f"{tag}: exit={res.exit_code} bytes={len(body)}")
        for c in counts:
            print("   ", repr(c))
        return {"tag": tag, "script": ln, "exit": res.exit_code,
                "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "counts": counts, "lines": lines}

    S = 'picture-report layout:summary output-to:"%3" "%1" "%2"'
    R = []
    R.append(run("V1-rightonly-order", S, "V1-L.png", "V1-R.png"))
    R.append(run("V2-ignore-unimp", 'picture-report layout:summary options:ignore-unimportant output-to:"%3" "%1" "%2"', "V2-L.png", "V2-R.png"))
    R.append(run("V3a-gif-equal", S, "V3a-L.gif", "V3a-R.gif"))
    R.append(run("V3b-gif-diff", S, "V3b-L.gif", "V3b-R.gif"))
    R.append(run("V5-both", S, "V5-L.png", "V5-R.png"))
    (rd / "m83i-summary.json").write_text(json.dumps(R, indent=1, ensure_ascii=False),
                                          encoding="utf-8")
    print("archived:", rd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
