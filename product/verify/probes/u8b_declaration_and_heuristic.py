#!/usr/bin/env python3
"""U8b probe -- the two measured gaps from U8, pinned down to implementable rules.

U8 established, on this host (ACP=65001), that BC:

* does **not** autodetect a BOM-less legacy encoding -- it decodes as UTF-8 lossy;
* **does** honour ``<?xml ... encoding="NAME"?>`` and decodes the body with that
  code page (``测试`` came back correct, no ``<errorN>``, line judged ``same``);
* **does** implement the BOM-less UTF-16 NUL-parity heuristic.

Those two mechanisms are what has to be implemented, so this probe answers the
questions an implementation cannot guess:

A. Declaration name resolution -- which spellings select a code page?
   ``GBK`` / ``gbk`` / ``cp936`` / ``gb2312`` / ``windows-936`` / ``Shift_JIS`` /
   ``windows-1252`` / ``utf-8``.  Case sensitivity and alias breadth matter:
   ``SsCodePage.md`` says the lookup is a name->codepage table.

B. Declaration placement -- must it be the very first bytes?  What if a UTF-8 BOM
   precedes it (BOM and declaration disagree)?  What if it is on line 2?

C. Priority -- a declared code page vs bytes that are *already valid UTF-8*:
   does the declaration win (decode as GBK anyway) or lose?

D. Failure inside a declared code page -- bytes that are invalid in the declared
   encoding too: is ``<errorN>`` emitted, and with which line number?

E. The UTF-16 heuristic's envelope -- which NUL densities trigger it, and does a
   declaration or BOM outrank it?

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u8b_declaration_and_heuristic.py
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

#: 测试 in GBK; its correct UTF-8 spelling is the decode oracle for the case.
GBK_CE_SHI = "\u6d4b\u8bd5".encode("gbk")      # b2 e2 ca d4
UTF8_CE_SHI = "\u6d4b\u8bd5".encode("utf-8")

#: 中文 in GBK -- also the string Shift-JIS would misread, so a wrong code page
#: is visible in the decoded text rather than silently correct.
GBK_ZHONG_WEN = "\u4e2d\u6587".encode("gbk")

#: A lone 0xFF is invalid in GBK *and* in UTF-8: it fails under every code page,
#: which is what case D needs.
BAD_EVERYWHERE = b"\xff"


def decl(name: str) -> bytes:
    return f'<?xml version="1.0" encoding="{name}"?>\n'.encode("ascii")


#: tag -> (left bytes, right bytes, purpose)
CASES: dict[str, tuple[bytes, bytes, str]] = {
    # --- A. name resolution.  Left is GBK+decl; right is the UTF-8 spelling with
    # a UTF-8 declaration.  If the name resolves, line 2 is `same`; if not,
    # line 2 is `different` (GBK bytes are invalid UTF-8) and `<error1>` appears.
    "decl-gbk-upper": (decl("GBK") + GBK_CE_SHI + b"\n",
                       decl("UTF-8") + UTF8_CE_SHI + b"\n",
                       "the exact name GBK"),
    "decl-gbk-lower": (decl("gbk") + GBK_CE_SHI + b"\n",
                       decl("UTF-8") + UTF8_CE_SHI + b"\n",
                       "case-insensitive name lookup?"),
    "decl-cp936": (decl("cp936") + GBK_CE_SHI + b"\n",
                   decl("UTF-8") + UTF8_CE_SHI + b"\n",
                   "numeric-alias spelling cp936"),
    "decl-gb2312": (decl("gb2312") + GBK_ZHONG_WEN + b"\n",
                    decl("UTF-8") + "\u4e2d\u6587".encode("utf-8") + b"\n",
                    "gb2312 (distinct alias, near-identical table)"),
    "decl-windows936": (decl("windows-936") + GBK_CE_SHI + b"\n",
                        decl("UTF-8") + UTF8_CE_SHI + b"\n",
                        "windows-NNNN spelling"),
    "decl-windows1252": (decl("windows-1252") + "caf\u00e9".encode("cp1252") + b"\n",
                         decl("UTF-8") + "caf\u00e9".encode("utf-8") + b"\n",
                         "a single-byte code page (cp1252 e-acute)"),
    "decl-shiftjis": (decl("Shift_JIS") + "\u30c6\u30b9\u30c8".encode("shift_jis") + b"\n",
                      decl("UTF-8") + "\u30c6\u30b9\u30c8".encode("utf-8") + b"\n",
                      "a DBCS page other than GBK"),
    "decl-utf8": (decl("utf-8") + UTF8_CE_SHI + b"\n",
                  decl("UTF-8") + UTF8_CE_SHI + b"\n",
                  "control: explicit utf-8 must be a no-op"),

    # --- B. placement / precedence.
    "decl-after-bom": (b"\xef\xbb\xbf" + decl("GBK") + GBK_CE_SHI + b"\n",
                       b"\xef\xbb\xbf" + decl("UTF-8") + UTF8_CE_SHI + b"\n",
                       "BOM before the declaration -- does the declaration win?"),
    "decl-line2": (b"junk\n" + decl("GBK") + GBK_CE_SHI + b"\n",
                   b"junk\n" + decl("UTF-8") + UTF8_CE_SHI + b"\n",
                   "declaration not at byte 0 -- honoured at all?"),
    "decl-no-xml": (b'encoding="GBK"\n' + GBK_CE_SHI + b"\n",
                    b'encoding="UTF-8"\n' + UTF8_CE_SHI + b"\n",
                    "no <?xml prefix -- is the name still read?"),

    # --- C. priority: declaration vs already-valid UTF-8 body.
    "decl-gbk-valid-utf8": (decl("GBK") + UTF8_CE_SHI + b"\n",
                            decl("UTF-8") + UTF8_CE_SHI + b"\n",
                            "declared GBK but the bytes are valid UTF-8: who wins?"),

    # --- D. failure inside the declared page.
    "decl-gbk-bad-byte": (decl("GBK") + GBK_CE_SHI + b"\n" + BAD_EVERYWHERE + b"\n",
                          decl("UTF-8") + UTF8_CE_SHI + b"\n" + b"x\n",
                          "0xFF is invalid in GBK too -- error element? line?"),

    # --- E. the UTF-16 heuristic envelope.
    "utf16le-dense": (b"a\x00b\x00c\x00\n\x00", b"a\nb\nc\n",
                      "3/4 NULs odd -- above the 0.6 threshold"),
    "utf16le-ascii-mix": (b"ab\x00cd\x00\n\x00", b"ab\ncd\n",
                          "fewer NULs: below threshold?"),
    "utf16le-cjk": ("中文测试\n".encode("utf-16-le"), "中文测试\n".encode("utf-8"),
                    "CJK UTF-16LE: almost no NULs -- heuristic must miss"),
    "utf16le-short": (b"a\x00\n\x00", b"a\n",
                      "len 4: spec requires len even and >3"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8b-probe-%Y%m%dT%H%M%SZ"))
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
            errs = [e[0] for e in re.findall(r"<(error\d)>(.*?)</error\d>", body)]
            statuses = re.findall(r'<linecomp status="([a-z]+)"', body)
            texts = re.findall(r"<text [^>]*>(.*?)</text>", body)
            return {
                "errors": errs,
                "statuses": statuses,
                "texts": texts,
                "want": "测试" in body or "中文" in body or "テスト" in body
                        or "café" in body,
                "fffd": body.count("\ufffd"),
            }

        o_s, p_s = shape(o_body), shape(p_body)
        records.append({
            "tag": tag, "purpose": purpose,
            "left_hex": lb.hex(), "right_hex": rb.hex(),
            "oracle_exit": run.exit_code, "oracle": o_s,
            "product_exit": proc.returncode, "product": p_s,
            "oracle_body": o_body, "product_body": p_body,
        })
        print(f"  {tag:<20} O st={o_s['statuses']} err={o_s['errors']} "
              f"want={o_s['want']} fffd={o_s['fffd']}")
        print(f"  {'':<20} P st={p_s['statuses']} err={p_s['errors']} "
              f"want={p_s['want']} fffd={p_s['fffd']}")

    (run_dir / "u8b-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u8b-results.json'}")

    by = {r["tag"]: r for r in records}

    def line(tag: str) -> str:
        r = by[tag]
        return (f"  {tag:<20} statuses={','.join(r['oracle']['statuses']):<24} "
                f"errors={','.join(r['oracle']['errors']) or '-':<8} "
                f"correct-text={r['oracle']['want']}")

    print("\n=== A. declaration name resolution (oracle) ===")
    for tag in ("decl-gbk-upper", "decl-gbk-lower", "decl-cp936", "decl-gb2312",
                "decl-windows936", "decl-windows1252", "decl-shiftjis",
                "decl-utf8"):
        # `same` on the text line means the name resolved to a working page.
        print(line(tag))

    print("\n=== B/C/D. placement, priority, failure ===")
    for tag in ("decl-after-bom", "decl-line2", "decl-no-xml",
                "decl-gbk-valid-utf8", "decl-gbk-bad-byte", "decl-gbk-upper"):
        print(line(tag))

    print("\n=== E. UTF-16 heuristic envelope (oracle) ===")
    for tag in ("utf16le-dense", "utf16le-ascii-mix", "utf16le-cjk",
                "utf16le-short"):
        r = by[tag]
        print(f"  {tag:<20} statuses={','.join(r['oracle']['statuses']):<24} "
              f"texts={r['oracle']['texts']}")

    print("\n=== decoded text, side by side (the decode evidence) ===")
    for tag in ("decl-gbk-upper", "decl-windows1252", "decl-shiftjis",
                "decl-after-bom", "decl-gbk-valid-utf8", "decl-gbk-bad-byte",
                "utf16le-dense", "utf16le-ascii-mix"):
        r = by[tag]
        print(f"  {tag}:")
        print(f"    O: {r['oracle']['texts']}")
        print(f"    P: {r['product']['texts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
