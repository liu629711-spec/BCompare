#!/usr/bin/env python3
"""M83h: all four count categories in ONE report -> the line order.

Q2 said `相同` then `重要`; Q1/R7 said the rest. One 8x8-vs-8x6 fixture with a
same region, an important region, an unimportant region AND a left-only band
tests whether the order is same -> important -> unimportant -> left-only.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m83h_picture_order.py
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


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    rd = (REA / "product" / "verify" / "runs" /
          datetime.now(timezone.utc).strftime("m83h-picorder4-%Y%m%dT%H%M%SZ"))
    fx = rd / "fixtures"; fx.mkdir(parents=True)
    (rd / "scripts").mkdir(parents=True); (rd / "reports").mkdir(parents=True)

    G = (128, 128, 128)
    # left 8x8: x0..1 same | x2..3 important(+30) | x4..5 unimportant(+20);
    # right 8x6 (top two rows of left dropped -> those become left-only).
    def left(x, y):
        if x < 2:
            return G
        if x < 4:
            return (158, 128, 128)   # +30 important
        return (148, 128, 128)       # +20 unimportant

    def right(x, y):
        return G if x < 2 else (left(x, y + 2)[0], 128, 128) if False else left(x, y)
    # right must equal left for x<2, important-diff for x2..3, unimportant-diff
    # for x4..5, and be 2 rows shorter.
    def right2(x, y):
        if x < 2:
            return G
        if x < 4:
            return (128, 128, 128)   # 30-off from left (158) -> important
        return (128, 128, 128)       # 20-off from left (148) -> unimportant
    (fx / "F-L.png").write_bytes(png(8, 8, left))
    (fx / "F-R.png").write_bytes(png(8, 6, right2))

    ln = 'picture-report layout:summary output-to:"%3" "%1" "%2"'
    sp = rd / "scripts" / "F.all4.bcs"; orc.write_script(sp, [ln])
    out = rd / "reports" / "F.all4.out"
    r = orc.run(inst.oracle_path, sp, str((fx / "F-L.png").resolve()),
                str((fx / "F-R.png").resolve()), str(out), timeout=120.0, script_text=ln)
    body = out.read_bytes() if out.exists() else b""
    print(f"F.all4: exit={r.exit_code}")
    lines = body.decode("utf-8-sig", errors="replace").splitlines()
    for s in lines:
        print("   ", repr(s))
    (rd / "m83h-summary.json").write_text(json.dumps(
        {"exit": r.exit_code, "bytes": len(body),
         "sha256": hashlib.sha256(body).hexdigest(), "lines": lines},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print("archived:", rd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
