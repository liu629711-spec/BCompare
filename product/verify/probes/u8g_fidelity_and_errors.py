#!/usr/bin/env python3
"""U8g probe -- fidelity and error reporting for the resolved pages.

U8f measured the **complete** name table by fingerprinting (see its results and
``U8-FINDINGS.md``).  Two things remain before the decoder can be written, and
both are exact-value questions, not design questions:

1. **Fidelity.**  For every page the table resolves to, is BC's decode
   byte-identical to the OS table?  U8f attempted this but its comparison kept
   the newlines that BC's line splitter removes, so every case read as a
   mismatch.  The comparison here joins BC's lines first, which is the actual
   question: "does BC's text equal the OS decode of the same bytes".

2. **Error reporting under a declared page.**  U8c/u8f fixed the shape --
   a declared DBCS page decodes loosely (``0xFF`` -> ``U+F8F5``) *and* reports
   ``<error1>`` -- but not the line number rule, nor whether the element's text
   is the localized ``文件编码错误 (第 N 行)``.  Both are report-visible, so both
   are measured.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u8g_fidelity_and_errors.py
"""
from __future__ import annotations

import ctypes
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

_k32 = ctypes.windll.kernel32
MB_ERR_INVALID_CHARS = 0x00000008


def cp_decode(cp: int, data: bytes, strict: bool = False) -> str:
    buf = ctypes.create_unicode_buffer(len(data) * 2 + 8)
    flags = MB_ERR_INVALID_CHARS if strict else 0
    n = _k32.MultiByteToWideChar(cp, flags, data, len(data), buf, len(buf))
    return "".join(buf[:n])


#: page -> (the name BC resolves it by, the sample sentence)
PAGES: dict[int, tuple[str, str]] = {
    936: ("GBK", "\u4e2d\u6587\u6d4b\u8bd5\uff0c\u6807\u70b9\uff1b\u5168\u89d2"
                 "\u3002\u4f60\u597d\u4e16\u754c"),
    54936: ("GB18030", "\u4e2d\u6587\u6d4b\u8bd5\uff0c\u6807\u70b9\uff1b\u5168\u89d2"),
    932: ("Shift_JIS", "\u30c6\u30b9\u30c8\u3067\u3059\u3002\u65e5\u672c\u8a9e"
                       "\u30ab\u30bf\u30ab\u30ca"),
    950: ("Big5", "\u4e2d\u6587\u6e2c\u8a66\uff0c\u6a19\u9ede\u3002\u4f60\u597d"),
    949: ("cp949", "\ud55c\uad6d\uc5b4 \ud14c\uc2a4\ud2b8"),
    1361: ("johab", "\ud55c\uad6d\uc5b4"),
    1250: ("windows-1250", "P\u0159\u00edli\u0161 \u017elu\u0165ou\u010dk\u00fd k\u016f\u0148"),
    1251: ("windows-1251", "\u0420\u0443\u0441\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442"),
    1252: ("windows-1252", "caf\u00e9 na\u00efve \u201cquoted\u201d \u2014 dash"),
    1253: ("windows-1253", "\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac"),
    1254: ("windows-1254", "T\u00fcrk\u00e7e \u015fapka \u011f"),
    1255: ("windows-1255", "\u05e2\u05d1\u05e8\u05d9\u05ea"),
    1256: ("windows-1256", "\u0639\u0631\u0628\u064a"),
    1257: ("windows-1257", "Eesti t\u00e4hed \u0161"),
    1258: ("windows-1258", "Ti\u1ebfng Vi\u1ec7t"),
    874: ("windows-874", "\u0e44\u0e17\u0e22"),
    28591: ("L1", "caf\u00e9 \u00e0 la"),
    28592: ("ISO-8859-2", "\u0161\u010d\u017e"),
    28595: ("ISO-8859-5", "\u0416\u0438"),
    28597: ("ISO-8859-7", "\u03b1\u03b2\u03b3"),
    437: ("IBM437", "\u2591\u2592\u2593"),
    850: ("IBM850", "\u2591\u2592\u2593"),
    866: ("cp866", "\u2591\u2592\u2593"),
    20127: ("probe-ascii", "plain"),
}


def cp_encode(cp: int, text: str) -> bytes:
    n = _k32.WideCharToMultiByte(cp, 0, text, len(text), None, 0, None, None)
    if not n:
        return b""
    buf = ctypes.create_string_buffer(n)
    _k32.WideCharToMultiByte(cp, 0, text, len(text), buf, n, None, None)
    return buf.raw[:n]


def decl(name: str) -> bytes:
    return f'<?xml version="1.0" encoding="{name}"?>\n'.encode("ascii")


#: Error-reporting cases under a declared GBK page.  Each one places the
#: offending byte on a known line so the number in the element is checkable.
ERROR_CASES: dict[str, tuple[bytes, str]] = {
    "err-line-1": (decl("GBK") + b"\xff\nok\nok\n", "invalid on line 2 of file"),
    "err-line-3": (decl("GBK") + b"a\nb\n\xff\nc\n", "invalid on line 4"),
    "err-two-bad": (decl("GBK") + b"\xff\nok\n\xfe\n", "two bad lines: which is reported?"),
    "err-dangling": (decl("GBK") + b"ok\n\x81", "dangling lead at EOF"),
    "err-dangling-eol": (decl("GBK") + b"ok\n\x81\nnext\n", "lead byte before newline"),
    "err-none": (decl("GBK") + "\u4e2d\u6587\n".encode("gbk"), "clean file: no element"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8g-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})\n")

    def call(tag: str, payload: bytes) -> dict:
        lp, rp = fx / f"{tag}-L.txt", fx / f"{tag}-R.txt"
        lp.write_bytes(payload)
        rp.write_bytes(payload)
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        body = ""
        if run.report_exists and run.report_bytes:
            body = o_out.read_bytes().decode("utf-8-sig", errors="replace")
        texts = re.findall(r"<text [^>]*>(.*?)</text>", body)
        texts = [t.replace("&lt;", "<").replace("&gt;", ">")
                 .replace("&quot;", '"').replace("&amp;", "&") for t in texts]
        return {"body": body, "texts": texts,
                "errors": re.findall(r"<(error\d)>(.*?)</error\d>", body),
                "statuses": re.findall(r'<linecomp status="([a-z]+)"', body)}

    # ------------------------------------------------------------- A: fidelity
    print("=== A. fidelity: BC's decode vs the OS table ===")
    fid: list[dict] = []
    for cp, (name, text) in PAGES.items():
        if name == "probe-ascii":
            # 20127 has no name in the measured table; skip rather than invent.
            continue
        raw = cp_encode(cp, text)
        if not raw:
            print(f"  cp{cp:<6} (skip: OS cannot encode the sample)")
            continue
        r = call(f"fid-{cp}", decl(name) + raw + b"\n")
        # BC's line splitter removes the newline, so compare with it removed.
        got = "".join(t for t in r["texts"] if not t.lstrip().startswith("<"))
        want = cp_decode(cp, raw)
        same = got == want
        fid.append({"cp": cp, "name": name, "same": same,
                    "want": want, "got": got, "raw": raw.hex(),
                    "errors": [e[0] for e in r["errors"]]})
        print(f"  cp{cp:<6} via {name!r:<14} {'MATCH ' if same else 'DIFFER'}"
              f"  errors={[e[0] for e in r['errors']] or '-'}")
        if not same:
            print(f"      want={want!r}")
            print(f"      got ={got!r}")

    # -------------------------------------------------------------- B: errors
    print("\n=== B. error reporting under a declared page ===")
    errs: list[dict] = []
    for tag, (payload, purpose) in ERROR_CASES.items():
        r = call(tag, payload)
        lines = [t for t in r["texts"] if not t.lstrip().startswith("<")]
        errs.append({"tag": tag, "purpose": purpose, "lines": lines,
                     "errors": r["errors"], "statuses": r["statuses"]})
        print(f"  {tag:<18} errors={r['errors'] or '-'}")
        print(f"      lines={lines}")

    (run_dir / "u8g-results.json").write_text(
        json.dumps({"fidelity": fid, "errors": errs}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nraw: {run_dir / 'u8g-results.json'}")

    ok = sum(1 for f in fid if f["same"])
    print(f"\nfidelity: {ok}/{len(fid)} pages byte-identical to the OS table")
    bad = [f["name"] for f in fid if not f["same"]]
    if bad:
        print(f"NOT byte-identical: {bad}  -- these pages must not be claimed "
              f"as replicated without a table that matches BC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
