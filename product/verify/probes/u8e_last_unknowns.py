#!/usr/bin/env python3
"""U8e probe -- the last unknowns before the decoder is written.

Four questions the implementation cannot guess:

1. **Where does the ASCII family resolve to?**  U8d showed ``US-ASCII`` /
   ``ascii`` / ``ANSI_X3.4-1968`` / ``iso-ir-6`` turning the UTF-8 bytes
   ``C3 A9`` into ``Ã©`` -- i.e. they *did* resolve, to a single-byte page, and
   the probe mislabelled them because it expected a no-op.  ``SsCodePage.md``
   says codepage 20191 ("US-ASCII (7-bit)") is "treated as ANSI", and
   ``GetACP()`` on this host is 65001, which would have produced ``café``.  So
   the target has to be fingerprinted byte by byte, not reasoned about.

2. **The declaration's exact syntax.**  Measured so far: single quotes are
   accepted, ``ENCODING=`` and ``encoding =`` are not.  Still open: a minimal
   declaration with no ``version``, a missing closing quote, and a trailing
   attribute after ``encoding``.

3. **GB18030's four-byte sequences.**  GB18030 resolved, and its two-byte range
   is GBK's -- but a four-byte sequence would need real GB18030 support.  If BC
   decodes one, so must we; if it does not, "GB18030" is really "the GBK table".

4. **Name case handling**, so the alias table's matching rule is known rather
   than assumed.

Expectations for the single-byte fingerprint come from ``MultiByteToWideChar``
via ctypes -- the same source BC uses -- so the comparison tests BC against the
OS table rather than against a hand-written one.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u8e_last_unknowns.py
"""
from __future__ import annotations

import ctypes
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

_k32 = ctypes.windll.kernel32


def cp_to_str(cp: int, data: bytes) -> str:
    """Loose ``MultiByteToWideChar`` -- what BC's ANSI path is built on."""
    buf = ctypes.create_unicode_buffer(len(data) * 2 + 8)
    n = _k32.MultiByteToWideChar(cp, 0, data, len(data), buf, len(buf))
    return "".join(buf[:n])


#: Bytes chosen to separate the plausible single-byte targets: 0x93/0x94 are
#: smart quotes in cp1252 but undefined in ISO-8859-1; 0xE9 is é in both, ù in
#: cp1250 and й in cp1251; 0x81 and 0x8D are undefined in cp1252; 0xA0 is NBSP
#: everywhere; 0xB2 is superscript-2 in cp1252 but a quote in cp1251.
FINGERPRINT_BODY = b"\x80\n\x93\n\x94\n\xe9\n\x81\n\x8d\n\xa0\n\xb2\n"

GBK_CE_SHI = "\u6d4b\u8bd5".encode("gbk")
#: U+00A4 in GB18030 is the four-byte sequence 81 30 84 36.  Two-byte GBK
#: cannot express it, so a correct decode proves real GB18030 support.
GB18030_4BYTE = b"\x81\x30\x84\x36"


def decl(name: str, *, version: bool = True, close_quote: bool = True,
         extra: str = "") -> bytes:
    v = ' version="1.0"' if version else ""
    q = f'encoding="{name}"' if close_quote else f'encoding="{name}'
    return f'<?xml{v} {q}{extra}?>\n'.encode("ascii")


CASES: dict[str, tuple[bytes, bytes, str]] = {
    # --- 1. fingerprint the ASCII family's target page.
    "ascii-us": (decl("US-ASCII") + FINGERPRINT_BODY,
                 decl("US-ASCII") + FINGERPRINT_BODY,
                 "US-ASCII target page, byte by byte"),
    "ascii-lower": (decl("ascii") + FINGERPRINT_BODY,
                    decl("ascii") + FINGERPRINT_BODY,
                    "same page for the lower-case spelling?"),
    "cp1252-control": (decl("windows-1252") + FINGERPRINT_BODY,
                       decl("windows-1252") + FINGERPRINT_BODY,
                       "control: the page the ASCII family may equal"),

    # --- 2. declaration syntax.
    "decl-minimal": (decl("GBK", version=False) + GBK_CE_SHI + b"\n",
                     decl("UTF-8", version=False) + "\u6d4b\u8bd5".encode("utf-8") + b"\n",
                     "<?xml encoding=\"GBK\"?> with no version attribute"),
    "decl-no-close-quote": (decl("GBK", close_quote=False) + GBK_CE_SHI + b"\n",
                            decl("UTF-8") + "\u6d4b\u8bd5".encode("utf-8") + b"\n",
                            "closing quote missing though '>' is present"),
    "decl-extra-attr": (decl("GBK", extra=' standalone="yes"') + GBK_CE_SHI + b"\n",
                        decl("UTF-8", extra=' standalone="yes"') + "\u6d4b\u8bd5".encode("utf-8") + b"\n",
                        "a further attribute after encoding"),
    "decl-mixed-case": (decl("GbK") + GBK_CE_SHI + b"\n",
                        decl("UTF-8") + "\u6d4b\u8bd5".encode("utf-8") + b"\n",
                        "mixed-case encoding name"),
    "decl-no-encoding": (b'<?xml version="1.0"?>\n' + GBK_CE_SHI + b"\n",
                         b'<?xml version="1.0"?>\n' + "\u6d4b\u8bd5".encode("utf-8") + b"\n",
                         "a declaration with no encoding attribute"),

    # --- 3. GB18030's four-byte range.
    "gb18030-4byte": (decl("GB18030") + GB18030_4BYTE + b"\n" + GBK_CE_SHI + b"\n",
                      decl("UTF-8") + "\u00a4\n".encode("utf-8")
                      + "\u6d4b\u8bd5".encode("utf-8") + b"\n",
                      "U+00A4 as 81 30 84 36 -- four-byte GB18030"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8e-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})\n")

    # The candidate single-byte pages, decoded by the OS for comparison.
    candidates = {
        "windows-1252": cp_to_str(1252, FINGERPRINT_BODY.rstrip(b"\n")),
        "ISO-8859-1": cp_to_str(28591, FINGERPRINT_BODY.rstrip(b"\n")),
        "windows-1251": cp_to_str(1251, FINGERPRINT_BODY.rstrip(b"\n")),
        "windows-1250": cp_to_str(1250, FINGERPRINT_BODY.rstrip(b"\n")),
        "US-ASCII(20127)": cp_to_str(20127, FINGERPRINT_BODY.rstrip(b"\n")),
        "ANSI-20191": cp_to_str(20191, FINGERPRINT_BODY.rstrip(b"\n")),
    }
    print("=== candidate pages, per the OS (bytes "
          f"{FINGERPRINT_BODY.rstrip(chr(10).encode()).hex()}) ===")
    for label, s in candidates.items():
        print(f"  {label:<18} {s!r}")
    print()

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
        body = ""
        if run.report_exists and run.report_bytes:
            body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        texts = re.findall(r"<text [^>]*>(.*?)</text>", body)
        errs = [e[0] for e in re.findall(r"<(error\d)>(.*?)</error\d>", body)]
        statuses = re.findall(r'<linecomp status="([a-z]+)"', body)

        # Unescape the tiny entity set the fingerprints can contain.
        unesc = [t.replace("&lt;", "<").replace("&gt;", ">")
                 .replace("&amp;", "&").replace("&quot;", '"') for t in texts]

        # The fingerprint cases carry one body line per byte; the others ask
        # whether the *last* line decoded to the expected text.
        fp_line = None
        if "fingerprint" in purpose or tag in ("ascii-us", "ascii-lower",
                                               "cp1252-control"):
            # First non-declaration text element is the first byte line.
            body_lines = [t for t in unesc if not t.startswith("<")]
            fp_line = "".join(body_lines)

        records.append({
            "tag": tag, "purpose": purpose,
            "left_hex": lb.hex(), "right_hex": rb.hex(),
            "oracle_exit": run.exit_code, "statuses": statuses, "errors": errs,
            "texts": unesc, "fingerprint": fp_line,
            "oracle_body": body,
        })
        print(f"  {tag:<22} st={','.join(statuses) or '-':<18} "
              f"err={','.join(errs) or '-'}")
        if fp_line is not None:
            print(f"       {'':<19} bytes->{fp_line!r}")

    (run_dir / "u8e-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u8e-results.json'}")

    by = {r["tag"]: r for r in records}

    print("\n=== 1. which page did the ASCII family land on? ===")
    for tag in ("ascii-us", "ascii-lower", "cp1252-control"):
        got = by[tag]["fingerprint"]
        match = [k for k, v in candidates.items() if v == got]
        print(f"  {tag:<22} {got!r}  -> {match or 'no single-byte candidate'}")

    print("\n=== 2. declaration syntax ===")
    for tag in ("decl-minimal", "decl-no-close-quote", "decl-extra-attr",
                "decl-mixed-case", "decl-no-encoding"):
        r = by[tag]
        ok = any("\u6d4b\u8bd5" == t for t in r["texts"])
        print(f"  {tag:<22} {'ACCEPTED' if ok and not r['errors'] else 'rejected':<9} "
              f"st={','.join(r['statuses'])} err={','.join(r['errors']) or '-'}")

    print("\n=== 3. GB18030 four-byte ===")
    r = by["gb18030-4byte"]
    print(f"  texts={r['texts']}")
    print(f"  U+00A4 decoded: {any(chr(0xA4) in t for t in r['texts'])}   "
          f"errors={r['errors'] or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
