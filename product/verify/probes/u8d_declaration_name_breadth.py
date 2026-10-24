#!/usr/bin/env python3
"""U8d probe -- breadth of the declaration's name table.

U8b measured a surprise: ``encoding="GBK"`` and ``encoding="gb2312"`` resolve,
but ``encoding="cp936"`` and ``encoding="windows-936"`` do **not**.  That
contradicts a plain reading of ``SsCodePage.md``, which describes a registry of
IANA-style aliases (``US-ASCII``/``ANSI_X3.4-1968``/``iso-ir-6`` all naming one
page) reached through a name->codepage lookup.

The difference decides what the implementation must cover.  A five-name table
would leave a real file that says ``encoding="cp936"`` silently mis-decoded, and
silent mis-decoding is the failure mode this project treats as worse than an
explicit "unsupported" -- so the alias set is measured rather than assumed.

Each case picks a body that makes the outcome unambiguous:

* CJK candidates get GBK ``测试`` -- correct decode shows as those two characters.
* ASCII-family candidates get UTF-8 ``é`` (``C3 A9``): if the name resolves to a
  7-bit page the byte pair is invalid (``<error1>``), and if it does not resolve
  it stays ``é`` -- so "resolved to ASCII" cannot be confused with "unresolved".
* Latin-1-family candidates get ``E9``, which is ``é`` in cp1252 and invalid in
  UTF-8.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u8d_declaration_name_breadth.py
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

#: Diagnostic bodies.  Each one is chosen so that a wrong resolution is visible
#: rather than coincidentally right.
GBK_BODY = "\u6d4b\u8bd5".encode("gbk")              # b2 e2 ca d4
UTF8_EACUTE = "caf\u00e9".encode("utf-8")            # 63 61 66 c3 a9
CP1252_EACUTE = "caf\u00e9".encode("cp1252")         # 63 61 66 e9
SJIS_BODY = "\u30c6\u30b9\u30c8".encode("shift_jis")
BIG5_BODY = "\u6e2c\u8a66".encode("big5")

#: (name, body, what the body's correct decode is)
CASES: list[tuple[str, bytes, str]] = [
    # --- the CJK page this milestone is about, and its spellings.
    ("GBK", GBK_BODY, "测试"),
    ("gbk", GBK_BODY, "测试"),
    ("GB2312", GBK_BODY, "测试"),
    ("gb2312", GBK_BODY, "测试"),
    ("GB_2312-80", GBK_BODY, "测试"),
    ("cp936", GBK_BODY, "测试"),
    ("CP936", GBK_BODY, "测试"),
    ("936", GBK_BODY, "测试"),
    ("windows-936", GBK_BODY, "测试"),
    ("csgb2312", GBK_BODY, "测试"),
    ("GB18030", GBK_BODY, "测试"),
    ("gb18030", GBK_BODY, "测试"),
    ("gbk-2312", GBK_BODY, "测试"),

    # --- ASCII family: `é` as UTF-8.  A 7-bit page makes this invalid.
    ("US-ASCII", UTF8_EACUTE, "café"),
    ("ascii", UTF8_EACUTE, "café"),
    ("ANSI_X3.4-1968", UTF8_EACUTE, "café"),
    ("iso-ir-6", UTF8_EACUTE, "café"),

    # --- UTF-8 itself: must be a no-op.
    ("utf-8", UTF8_EACUTE, "café"),
    ("UTF-8", UTF8_EACUTE, "café"),
    ("utf8", UTF8_EACUTE, "café"),
    ("CP65001", UTF8_EACUTE, "café"),

    # --- Latin-1 family: `E9` is é in cp1252, invalid in UTF-8.
    ("windows-1252", CP1252_EACUTE, "café"),
    ("ISO-8859-1", CP1252_EACUTE, "café"),
    ("latin1", CP1252_EACUTE, "café"),
    ("windows-1251", CP1252_EACUTE, "café"),

    # --- other DBCS pages.
    ("Shift_JIS", SJIS_BODY, "テスト"),
    ("sjis", SJIS_BODY, "テスト"),
    ("big5", BIG5_BODY, "測試"),
    ("Big5", BIG5_BODY, "測試"),

    # --- a name that cannot exist: must be ignored, never fatal.
    ("x-nonexistent-page", GBK_BODY, "测试"),
]


def decl(name: str) -> bytes:
    return f'<?xml version="1.0" encoding="{name}"?>\n'.encode("ascii")


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8d-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})\n")

    records: list[dict] = []
    for i, (name, body, want) in enumerate(CASES):
        # The same declaration and body on both sides: this probe asks only
        # "did the name resolve", so any difference inside a case is noise.
        payload = decl(name) + body + b"\n"
        lp, rp = fx / f"{i:02d}-L.txt", fx / f"{i:02d}-R.txt"
        lp.write_bytes(payload)
        rp.write_bytes(payload)

        o_out = run_dir / "reports" / f"{i:02d}.oracle.xml"
        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{i:02d}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        body_txt = ""
        if run.report_exists and run.report_bytes:
            body_txt = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        errs = [e[0] for e in re.findall(r"<(error\d)>(.*?)</error\d>", body_txt)]
        statuses = re.findall(r'<linecomp status="([a-z]+)"', body_txt)
        texts = re.findall(r"<text [^>]*>(.*?)</text>", body_txt)

        # Resolution is judged by the body line, not by absence of an error:
        # an ASCII-family page legitimately errors on a high byte.
        decoded = texts[-1] if texts else ""
        resolved = decoded == want
        records.append({
            "name": name, "want": want, "decoded": decoded,
            "resolved": resolved, "statuses": statuses, "errors": errs,
            "texts": texts, "oracle_exit": run.exit_code,
        })
        print(f"  {name:<18} {'RESOLVED' if resolved else 'no      '}  "
              f"decoded={decoded!r:<14} err={','.join(errs) or '-'} "
              f"st={','.join(statuses) or '-'}")

    (run_dir / "u8d-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u8d-results.json'}")

    print("\n=== names BC resolves (grouped) ===")
    for r in records:
        if r["resolved"]:
            print(f"  {r['name']:<18} -> {r['decoded']!r}")
    print("\n=== names BC does NOT resolve ===")
    for r in records:
        if not r["resolved"]:
            print(f"  {r['name']:<18} decoded={r['decoded']!r} "
                  f"err={','.join(r['errors']) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
