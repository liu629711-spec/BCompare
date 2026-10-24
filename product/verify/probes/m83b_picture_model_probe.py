#!/usr/bin/env python3
"""M83b: the picture channel's body model.

From m83:
  frame = 图片比较(P) / 已产生： <time> / '' / 左边文件： <L> / 右边文件： <R>
  [summary adds]  N 个重要差异像素
  title: replaces line 1 (P11). non-image -> 左边错误： 不被支持的类型 x2.
  refuse: bogus layout 106, no layout 106, output-options 106,
          one file 106, missing file 107; zero files -> 76-byte shell exit 0.

Open cells (serial):
  Q1  equal pair, summary: is the count line OMITTED (zero lines omitted, as
      the hex summary did) or does it say 0?
  Q2  partial difference (e.g. 8x8 with a 2x2 block changed = 4 px): does the
      count match the changed pixel count exactly?
  Q3  options values: which are accepted (exit 0) vs refused? Try the text
      channel's own vocabulary (display-mismatches accepted in P6) plus a
      bogus one. Picture Compare's real options are unknown -> measure.
  Q4  side-by-side on a DIFFERING pair: is there any body at all beyond the
      frame (m83 P2 was 232 bytes = frame only)? If sbs never lists pixels,
      the layout is frame-only and the model is trivially closed.
  Q5  a real BMP/GIF/JPEG pair: does the count appear (format support)?
  Q6  identical JPEG bytes but different files (equal) -> summary line?
  Q7  image vs non-image MIXED (png + .bin): one error line or two?

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m83b_picture_model_probe.py
"""
from __future__ import annotations

import hashlib, json, pathlib, struct, sys, zlib
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def png(width: int, height: int, pixel) -> bytes:
    """Solid or per-row pixel function; `pixel(x, y)` -> (r,g,b)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + b"".join(bytes(pixel(x, y)) for x in range(width))
                   for y in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def bmp(width: int, height: int, rgb=(0, 128, 255)) -> bytes:
    row = bytes(rgb[::-1]) * width
    rows = b"".join(row for _ in range(height))
    hdr = struct.pack("<2sIHHI", b"BM", 54 + len(rows), 0, 0, 54)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(rows), 0, 0, 0, 0)
    return hdr + dib + rows


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m83b-picturemodel-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    # Q1: identical 8x8 -> summary
    (fx / "EQ-L.png").write_bytes(png(8, 8, lambda x, y: (10, 20, 30)))
    (fx / "EQ-R.png").write_bytes(png(8, 8, lambda x, y: (10, 20, 30)))
    # Q2: 2x2 block changed (top-left 2x2) -> expect 4
    def part(x, y):
        return (200, 0, 0) if (x < 2 and y < 2) else (10, 20, 30)
    (fx / "P4-L.png").write_bytes(png(8, 8, lambda x, y: (10, 20, 30)))
    (fx / "P4-R.png").write_bytes(png(8, 8, part))
    # Q5: BMP pair, 4x4 with 3 px changed
    def b4(x, y):
        return (255, 255, 0) if (x + y) < 3 else (0, 0, 0)
    (fx / "B-L.bmp").write_bytes(bmp(4, 4))
    (fx / "B-R.bmp").write_bytes(struct.pack("<2sIHHI", b"BM", 0, 0, 0, 0)[:0] + bmp(4, 4))
    (fx / "B-R.bmp").write_bytes(bmp(4, 4, (1, 2, 3)))
    # Q7: png vs bin
    (fx / "M-L.png").write_bytes(png(4, 4, lambda x, y: (1, 1, 1)))
    (fx / "M-R.bin").write_bytes(b"\x00\x01\x02")

    def run(tag, script_line, l, r):
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [script_line])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0,
                      script_text=script_line)
        body = out.read_bytes() if out.exists() else b""
        text = body.decode("utf-8-sig", errors="replace")
        # strip the two path lines so the printout is readable
        shown = [ln for ln in text.splitlines() if "左边文件" not in ln and "右边文件" not in ln]
        print(f"{tag}: exit={res.exit_code} bytes={len(body)}")
        for s in shown[:14]:
            print("   ", repr(s))
        return {"tag": tag, "script": script_line, "exit": res.exit_code,
                "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "body": shown}

    EQ = (str((fx / "EQ-L.png").resolve()), str((fx / "EQ-R.png").resolve()))
    P4 = (str((fx / "P4-L.png").resolve()), str((fx / "P4-R.png").resolve()))
    BM = (str((fx / "B-L.bmp").resolve()), str((fx / "B-R.bmp").resolve()))
    MX = (str((fx / "M-L.png").resolve()), str((fx / "M-R.bin").resolve()))

    results = []
    results.append(run("Q1-summary-equal",
                       'picture-report layout:summary output-to:"%3" "%1" "%2"', *EQ))
    results.append(run("Q2-summary-4px",
                       'picture-report layout:summary output-to:"%3" "%1" "%2"', *P4))
    results.append(run("Q4-sbs-diff",
                       'picture-report layout:side-by-side output-to:"%3" "%1" "%2"', *P4))
    for i, opt in enumerate(["display-mismatches", "display-matches", "line-numbers",
                             "ignore-unimportant", "bogus-option"], 1):
        results.append(run(f"Q3-{i}-{opt}",
                           f'picture-report layout:summary options:{opt} output-to:"%3" "%1" "%2"',
                           *P4))
    results.append(run("Q5-bmp-summary",
                       'picture-report layout:summary output-to:"%3" "%1" "%2"', *BM))
    results.append(run("Q7-mixed",
                       'picture-report layout:summary output-to:"%3" "%1" "%2"', *MX))

    (run_dir / "m83b-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
