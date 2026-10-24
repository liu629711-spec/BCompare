#!/usr/bin/env python3
"""M7 (m70b): the HEX report body model -- alignment, blocks, layouts.

m70 pinned the verb: `hex-report layout:<l> output-to:"%3" "%1" "%2"`
(exit 0); bare/other-verb/no-layout => 106; data-report on binary goes the
table path with an encoding-error note (left untouched). The observed side-
by-side body: 8-byte rows led by a 2-hex-digit offset, ASCII gutter after
each side, a 4-char marker column (` <> `, ` =  `, blank for block
continuations), dash rules between blocks, rows pairing BY OFFSET (no byte
shifting seen -- but the m70 fixture had only in-place edits + a tail cut).

Open questions, one fixture pair each (side-by-side unless noted):

  Y1-equal    64 vs identical 64            -- single ` =  ` block, one rule?
  Y2-insert   right has ONE byte inserted at 0x04; the rest continues
              (right = left[:4] + [0x41] + left[4:]). If BC pairs rows by
              offset, EVERY row after 00 differs (byte-at-04 shift cascade);
              if it aligns bytes (Myers-style), only one block shows.
              THE alignment question for the whole channel.
  Y3-append   left 24B prefix of right 32B -- trailing ORPHAN rows: what
              marker (` -+`? ` +-`?), what ASCII/blank on the empty side?
  Y4-delete   right truncated INSIDE a row (60 vs 64 already showed a
              short last row; here: delete a full middle row -> alignment).
  Y5-many     3 separate changed runs -> does EACH block repeat a marker?
  Y6-inter    Y2 pair on layout:interleaved -- hex interleaved shape?
  Y7-summary  Y5 pair on layout:summary -- counts by byte or by row?
  Y8-bogus    layout:bogus                    -- exit code?
  Y9-options  options:ignore-whitespace       -- 105 like tables?
  Y10-outopt  output-options:csv              -- 106?
  Y11-title   title:"HexTitle"                -- frame line 1 replaced?
  Y12-wide    600-byte pair, first changed row at 0x180: does the offset
              field widen (3 digits) and how do the dashes respond?
  Y13-empty   zero-byte left vs 16-byte right -- orphan-only report.

Usage (serial):  cd D:\\Rea\\product\\verify && python probes/m70b_hex_model_probe.py
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
    # (tag, left bytes, right bytes, layout, script-verb, extra)
    ("Y1-equal", L64, L64, "side-by-side", None),
    ("Y2-insert", L64, bytes(L64[:4]) + b"\x41" + bytes(L64[4:]), "side-by-side", None),
    ("Y3-append", L64[:24], L64, "side-by-side", None),
    ("Y4-delete", L64, bytes(L64[:16]) + bytes(L64[24:]), "side-by-side", None),
    ("Y5-many",
     bytes(L64[:4]) + b"\xFF" + bytes(L64[5:12]) + b"\xFF" + bytes(L64[13:24]) + b"\xFF" + bytes(L64[25:64]),
     L64, "side-by-side", None),
    ("Y6-inter", L64, bytes(L64[:4]) + b"\x41" + bytes(L64[4:]), "interleaved", None),
    ("Y7-summary",
     bytes(L64[:4]) + b"\xFF" + bytes(L64[5:]), L64, "summary", None),
    ("Y8-bogus", L64, L64[:60], "bogus", None),
    ("Y9-options", L64, L64[:60], "side-by-side", "options:ignore-whitespace"),
    ("Y10-outopt", L64, L64[:60], "side-by-side", "output-options:csv"),
    ("Y11-title", L64, L64[:60], "side-by-side", 'title:"HexTitle"'),
    ("Y12-wide", seq(600), bytes(seq(600)[:0x180] + b"\xFF" + seq(600)[0x181:]),
     "side-by-side", None),
    ("Y13-empty", b"", seq(16), "side-by-side", None),
]


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m70b-hexmodel-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"; fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    results = []
    for tag, left, right, lay, extra in CASES:
        lp = fx / f"{tag}-L.bin"; rp = fx / f"{tag}-R.bin"
        lp.write_bytes(left); rp.write_bytes(right)
        verb = f'hex-report layout:{lay}'
        if extra:
            verb += f" {extra}"
        line = f'{verb} output-to:"%3" "%1" "%2"'
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", [line])
        out = run_dir / "reports" / f"{tag}.out"
        if out.exists():
            out.unlink()
        r = orc.run(inst.oracle_path, script, str(lp.resolve()), str(rp.resolve()),
                    str(out.resolve()), timeout=120.0, script_text=line)
        body = out.read_bytes() if out.exists() else b""
        rec = {"tag": tag, "layout": lay, "extra": extra,
               "left_len": len(left), "right_len": len(right),
               "exit": r.exit_code, "bytes": len(body),
               "sha256": hashlib.sha256(body).hexdigest()}
        results.append(rec)
        print(f"{tag:12} exit={r.exit_code} bytes={len(body)}")
        for ln in body.decode("utf-8-sig", errors="replace").splitlines()[5:]:
            if ln.strip():
                print("   ", repr(ln))

    (run_dir / "m70b-hexmodel.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"archived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
