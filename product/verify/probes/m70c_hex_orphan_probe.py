#!/usr/bin/env python3
"""M7 (m70c): finish the hex model -- orphan shapes in interleaved/summary.

m70b pinned sbs + marker column width (2 iff a `<>` row exists, else 1) +
region-relative 8-byte chunking + interleaved merged identical rows with two
8-hex-digit offset columns. Unprobed surfaces this batch pins:

  Z1  summary, L64 vs L60 (right orphan 4B): orphan count line label/order.
  Z2  summary, L60 vs L64 (left orphan).
  Z3  summary, Y2-insert pair (change + pure insertion, no orphans):
      does a pure insert count as 1 `difference byte` or a right-only byte?
  Z4  interleaved, delete pair (left-only rows): column-2 offset blank?
  Z5  interleaved, append pair (right-only rows): column-1 offset blank?
  Z6  sbs, empty vs empty: zero rows -- any body at all?
  Z7  interleaved, 600-byte pair changed at 0x258: offset column stays 8?
  Z8  sbs, summary-only difference... skip: instead changed+orphan combined
      (L=00-3F vs R=00-3B with byte 04 changed): block order in one report.

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m70c_hex_orphan_probe.py
"""
from __future__ import annotations
import hashlib, json, pathlib, sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))
from harness import installs as inst_mod
from harness import oracle as orc


def seq(n: int, start: int = 0) -> bytes:
    return bytes((start + i) & 0xFF for i in range(n))


L64 = seq(64)
CASES = [
    ("Z1-sum-right", L64, L64[:60], "summary"),
    ("Z2-sum-left", L64[:60], L64, "summary"),
    ("Z3-sum-insert", L64, bytes(L64[:4]) + b"\x41" + bytes(L64[4:]), "summary"),
    ("Z4-int-delete", L64, bytes(L64[:16]) + bytes(L64[24:]), "interleaved"),
    ("Z5-int-append", L64[:24], L64, "interleaved"),
    ("Z6-empty-empty", b"", b"", "side-by-side"),
    ("Z7-int-600", seq(600), bytes(seq(600)[:0x258] + b"\xFF" + seq(600)[0x259:]),
     "interleaved"),
    ("Z8-sbs-mixed", bytes(L64) + seq(16), bytes(b"\xFF") + bytes(L64[1:]),
     "side-by-side"),
]


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m70c-hexorphan-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, left, right, lay in CASES:
        lp = fx / f"{tag}-L.bin"; rp = fx / f"{tag}-R.bin"
        lp.write_bytes(left); rp.write_bytes(right)
        line = f'hex-report layout:{lay} output-to:"%3" "%1" "%2"'
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", [line])
        out = run_dir / "reports" / f"{tag}.out"
        if out.exists():
            out.unlink()
        r = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                    str(out.resolve()), timeout=120.0, script_text=line)
        body = out.read_bytes() if out.exists() else b""
        rec = {"tag": tag, "layout": lay, "left_len": len(left),
               "right_len": len(right), "exit": r.exit_code, "bytes": len(body),
               "sha256": hashlib.sha256(body).hexdigest()}
        results.append(rec)
        print(f"{tag:14} exit={r.exit_code} bytes={len(body)}")
        for ln in body.decode("utf-8-sig", errors="replace").splitlines()[5:]:
            print("   ", repr(ln))

    (run_dir / "m70c-hexorphan.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
