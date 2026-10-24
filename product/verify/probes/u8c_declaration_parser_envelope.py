#!/usr/bin/env python3
"""U8c probe -- the declaration parser's exact envelope, for implementation.

U8b established the cascade:

    BOM (UTF-16LE/BE, UTF-8)
      -> ``<?xml`` at byte 0 -> declaration code page
      -> BOM-less UTF-16 NUL-parity heuristic
      -> UTF-8 lossy

and the alias table's observed members (``gbk``, ``gb2312``, ``windows-1252``,
``Shift_JIS``, ``utf-8`` resolve; ``cp936`` and ``windows-936`` do **not**).

What the parser must accept before it can be written is still open: quoting,
attribute-name case, an unterminated declaration, the Unicode-family rejection
``SsCodePage.md`` describes, and the heuristic's exact boundary.  Guessing any of
these would put an unverified branch in the decoder, which is exactly what the
project forbids.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u8c_declaration_parser_envelope.py
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

GBK_CE_SHI = "\u6d4b\u8bd5".encode("gbk")        # b2 e2 ca d4
UTF8_CE_SHI = "\u6d4b\u8bd5".encode("utf-8")

#: tag -> (left bytes, right bytes, purpose)
CASES: dict[str, tuple[bytes, bytes, str]] = {
    # --- quoting / case / spacing in the declaration.
    "single-quotes": (b'<?xml version="1.0" encoding=\'GBK\'?>\n' + GBK_CE_SHI + b"\n",
                      b'<?xml version="1.0" encoding=\'UTF-8\'?>\n' + UTF8_CE_SHI + b"\n",
                      "single-quoted attribute value"),
    "attr-upper": (b'<?xml version="1.0" ENCODING="GBK"?>\n' + GBK_CE_SHI + b"\n",
                   b'<?xml version="1.0" ENCODING="UTF-8"?>\n' + UTF8_CE_SHI + b"\n",
                   "attribute name upper case"),
    "extra-spaces": (b'<?xml version="1.0"   encoding = "GBK"  ?>\n' + GBK_CE_SHI + b"\n",
                     b'<?xml version="1.0"   encoding = "UTF-8"  ?>\n' + UTF8_CE_SHI + b"\n",
                     "spaces around the attribute"),
    "no-quote": (b'<?xml version="1.0" encoding=GBK?>\n' + GBK_CE_SHI + b"\n",
                 b'<?xml version="1.0" encoding=UTF-8?>\n' + UTF8_CE_SHI + b"\n",
                 "unquoted attribute value"),
    "unterminated": (b'<?xml version="1.0" encoding="GBK"\n' + GBK_CE_SHI + b"\n",
                     b'<?xml version="1.0" encoding="UTF-8"\n' + UTF8_CE_SHI + b"\n",
                     "no closing '>' -- is the declaration still read?"),
    "decl-only-first-64k": (b'<?xml version="1.0" encoding="GBK"?>\n' + GBK_CE_SHI + b"\n",
                            b'<?xml version="1.0" encoding="UTF-8"?>\n' + UTF8_CE_SHI + b"\n",
                            "control for the other declaration cases"),

    # --- Unicode-family rejection (SsCodePage.md step 4).
    "decl-utf16": (b'<?xml version="1.0" encoding="utf-16"?>\n' + GBK_CE_SHI + b"\n",
                   b'<?xml version="1.0" encoding="utf-8"?>\n' + UTF8_CE_SHI + b"\n",
                   "encoding=\"utf-16\" must be rejected (Unicode family)"),
    "decl-ucs2": (b'<?xml version="1.0" encoding="ucs-2"?>\n' + GBK_CE_SHI + b"\n",
                  b'<?xml version="1.0" encoding="utf-8"?>\n' + UTF8_CE_SHI + b"\n",
                  "another Unicode-family spelling"),

    # --- ASCII-only body: the declaration must not corrupt it.
    "decl-ascii": (b'<?xml version="1.0" encoding="GBK"?>\nabc\n',
                   b'<?xml version="1.0" encoding="GBK"?>\nabc\n',
                   "ASCII body under a declared DBCS page"),

    # --- input the declaration cannot describe: a UTF-16 BOM wins over it.
    "bom-beats-decl": (b'\xff\xfe' + b'<?xml version="1.0" encoding="GBK"?>\n'.decode("ascii").encode("utf-16-le")
                       + GBK_CE_SHI.decode("gbk").encode("utf-16-le") + b"\n\x00",
                       b'\xff\xfe' + b'<?xml version="1.0" encoding="UTF-8"?>\n'.decode("ascii").encode("utf-16-le")
                       + UTF8_CE_SHI.decode("utf-8").encode("utf-16-le") + b"\n\x00",
                       "UTF-16LE BOM + a GBK declaration: BOM is step 1"),

    # --- the heuristic's lower boundary.
    "nul-len2": (b"\x00a", b"\x00a",
                 "len 2: below the spec's 'even and >3' gate"),
    "nul-len4-be": (b"\x00a\x00b", b"ab",
                    "len 4, NULs on even indices -> UTF-16BE?"),
    "nul-ratio-50": (b"a\x00b\x00c\x00d\x00\x00\x00", b"abcd",
                     "odd-NUL ratio 5/6=0.83: above 0.6 -> UTF-16LE?"),
    "nul-even-also": (b"a\x00\x00\x00b\x00\x00\x00", b"ab",
                      "NULs on both parities: neither branch may fire"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8c-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"product : {PRODUCT}\n")

    records: list[dict] = []
    for tag, (lb, rb, purpose) in CASES.items():
        lp, rp = fx / f"{tag}-L.txt", fx / f"{tag}-R.txt"
        lp.write_bytes(lb)
        rp.write_bytes(rb)

        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = ""
        if run.report_exists and run.report_bytes:
            o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        p_out = run_dir / "reports" / f"{tag}.product.xml"
        proc = subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)],
                              capture_output=True, timeout=120)
        p_body = ""
        if p_out.exists():
            p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

        def shape(body: str) -> dict:
            return {
                "errors": [e[0] for e in
                           re.findall(r"<(error\d)>(.*?)</error\d>", body)],
                "statuses": re.findall(r'<linecomp status="([a-z]+)"', body),
                "texts": re.findall(r"<text [^>]*>(.*?)</text>", body),
                "fffd": body.count("\ufffd"),
                "chinese_ok": "\u6d4b\u8bd5" in body,
            }

        o_s, p_s = shape(o_body), shape(p_body)
        records.append({
            "tag": tag, "purpose": purpose,
            "left_hex": lb.hex(), "right_hex": rb.hex(),
            "oracle_exit": run.exit_code, "oracle": o_s,
            "product_exit": proc.returncode, "product": p_s,
            "oracle_body": o_body, "product_body": p_body,
        })
        print(f"  {tag:<24} O st={o_s['statuses']} err={o_s['errors']} "
              f"ok={o_s['chinese_ok']} fffd={o_s['fffd']}")
        print(f"  {'':<24} P st={p_s['statuses']} err={p_s['errors']} "
              f"ok={p_s['chinese_ok']} fffd={p_s['fffd']}")

    (run_dir / "u8c-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u8c-results.json'}")

    by = {r["tag"]: r for r in records}

    print("\n=== declaration parser: what BC accepted ===")
    for tag in ("single-quotes", "attr-upper", "extra-spaces", "no-quote",
                "unterminated", "decl-only-first-64k", "decl-utf16",
                "decl-ucs2", "decl-ascii", "bom-beats-decl"):
        r = by[tag]
        o = r["oracle"]
        # A successful GBK decode of line 2 shows as correct Chinese text.
        verdict = ("ACCEPTED" if o["chinese_ok"] and not o["errors"]
                   else "rejected")
        print(f"  {tag:<24} {verdict:<10} st={','.join(o['statuses'])} "
              f"err={','.join(o['errors']) or '-'}")

    print("\n=== heuristic boundary ===")
    for tag in ("nul-len2", "nul-len4-be", "nul-ratio-50", "nul-even-also"):
        r = by[tag]
        o = r["oracle"]
        print(f"  {tag:<24} st={','.join(o['statuses'])} texts={o['texts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
