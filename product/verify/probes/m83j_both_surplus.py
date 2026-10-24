#!/usr/bin/env python3
"""M83j: left-only AND right-only in the same report -> their relative order.

L 6x8 vs R 8x6: overlap 6x6=36 (all same), L surplus 12 (rows 6-7) = 左边独有,
R surplus 12 (cols 6-7) = 右边独有. Reveals whether the order is
相同 -> 不重要 -> 左独有 -> 右独有 -> 重要.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m83j_both_surplus.py
"""
from __future__ import annotations
import json, pathlib, struct, sys, zlib
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea"); sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def png(w, h, rgb):
    def chunk(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    rd = (REA / "product" / "verify" / "runs" /
          datetime.now(timezone.utc).strftime("m83j-bothsurplus-%Y%m%dT%H%M%SZ"))
    fx = rd / "fixtures"; fx.mkdir(parents=True)
    (rd / "scripts").mkdir(parents=True); (rd / "reports").mkdir(parents=True)
    G = (128, 128, 128)
    (fx / "BS-L.png").write_bytes(png(6, 8, G))
    (fx / "BS-R.png").write_bytes(png(8, 6, G))
    ln = 'picture-report layout:summary output-to:"%3" "%1" "%2"'
    sp = rd / "scripts" / "BS.bcs"; orc.write_script(sp, [ln])
    out = rd / "reports" / "BS.out"
    r = orc.run(inst.oracle_path, sp, str((fx / "BS-L.png").resolve()),
                str((fx / "BS-R.png").resolve()), str(out), timeout=120.0, script_text=ln)
    body = out.read_bytes() if out.exists() else b""
    lines = body.decode("utf-8-sig", errors="replace").splitlines()
    counts = [s for s in lines if "像素" in s]
    print(f"BS: exit={r.exit_code}")
    for c in counts:
        print("   ", repr(c))
    (rd / "m83j-summary.json").write_text(
        json.dumps({"exit": r.exit_code, "counts": counts, "lines": lines},
                   indent=1, ensure_ascii=False), encoding="utf-8")
    print("archived:", rd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
