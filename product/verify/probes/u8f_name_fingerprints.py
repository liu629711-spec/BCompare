#!/usr/bin/env python3
"""U8f probe -- fingerprint every candidate name, and verify decode fidelity.

Why fingerprinting rather than expected values
---------------------------------------------

U8b/U8d each assumed a name's target and labelled anything else "unresolved".
Two of those labels were wrong: ``US-ASCII`` and ``windows-1251`` *do* resolve,
they just do not land where the probe expected.  An expectation-based probe
turns its own guess into a false negative.

This probe measures instead:

1. Each candidate name is given a **fingerprint body** -- one high byte per line,
   covering the bytes that separate the plausible pages (``0x80`` is € in cp1252
   but a control in ISO-8859-1; ``0x93`` is “ in cp1252 but a control
   elsewhere; ``0xE9`` is é in cp1252, й in cp1251, ů in cp1250; ``0xFE``/``0xFF``
   are undefined in most single-byte pages).
2. BC's decode of that body is compared against the OS decode
   (``MultiByteToWideChar``) of the *same* body under **every** candidate page.
   The name is then labelled with whichever page matches, or "unresolved" when
   the result is the UTF-8-lossy fallback.
3. Fidelity: for each page that resolved, a realistic sentence in that language
   is decoded by BC and by the OS, and the two are compared byte for byte.  A
   page that resolves to a table we cannot reproduce is a page we must not claim.

It also answers the last decode questions: a dangling lead byte before a newline
and at EOF, an invalid lead+trail pair, and whether GB18030's two-byte range is
identical to GBK's.

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u8f_name_fingerprints.py
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
MB_ERR_INVALID_CHARS = 0x00000008


def cp_decode(cp: int, data: bytes, strict: bool = False) -> str:
    buf = ctypes.create_unicode_buffer(len(data) * 2 + 8)
    flags = MB_ERR_INVALID_CHARS if strict else 0
    n = _k32.MultiByteToWideChar(cp, flags, data, len(data), buf, len(buf))
    return "".join(buf[:n])


def cp_encode(cp: int, text: str) -> bytes:
    """Encode via the OS, so the sample bytes come from the same table the
    decoder will be compared against.  Python's codecs disagree with the OS for
    some pages (cp1258 cannot encode its own characters), and using them would
    make the probe depend on a second, unrelated table."""
    n = _k32.WideCharToMultiByte(cp, 0, text, len(text), None, 0, None, None)
    if not n:
        return b""
    buf = ctypes.create_string_buffer(n)
    _k32.WideCharToMultiByte(cp, 0, text, len(text), buf, n, None, None)
    return buf.raw[:n]


#: One discriminating byte per line.  0x0A is the separator; the sample avoids
#: 0x0D so the bytes are not read as line breaks.
FINGERPRINT = b"\x80\n\x82\n\x93\n\x9f\n\xa1\n\xb0\n\xe9\n\xf7\n\xfe\n\xff\n"

#: A realistic sentence per candidate page, encoded **via the OS** in that page.
#: ``SAMPLES_TEXT`` holds the text; the bytes are produced by ``cp_encode`` below
#: so they come from the same table the decode comparison uses.
SAMPLES_TEXT: dict[int, str] = {
    936: "\u4e2d\u6587\u6d4b\u8bd5\uff0c\u6807\u70b9\uff1b\u5168\u89d2",
    54936: "\u4e2d\u6587\u6d4b\u8bd5\uff0c\u6807\u70b9\uff1b\u5168\u89d2",
    932: "\u30c6\u30b9\u30c8\u3067\u3059\u3002\u65e5\u672c\u8a9e",
    950: "\u4e2d\u6587\u6e2c\u8a66\uff0c\u6a19\u9ede",
    949: "\ud55c\uad6d\uc5b4 \ud14c\uc2a4\ud2b8",
    1361: "\ud55c\uad6d\uc5b4",
    1250: "P\u0159\u00edli\u0161 \u017elu\u0165ou\u010dk\u00fd",
    1251: "\u0420\u0443\u0441\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442",
    1252: "caf\u00e9 na\u00efve \u201cquoted\u201d",
    1253: "\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac",
    1254: "T\u00fcrk\u00e7e \u015fapka",
    1255: "\u05e2\u05d1\u05e8\u05d9\u05ea",
    1256: "\u0639\u0631\u0628\u064a",
    1257: "Eesti t\u00e4hed",
    1258: "Ti\u1ebfng Vi\u1ec7t",
    874: "\u0e44\u0e17\u0e22",
    28591: "caf\u00e9 \u00e0 la",
    28592: "\u0161\u010d\u017e",
    28595: "\u0416\u0438",
    28597: "\u03b1\u03b2\u03b3",
    28605: "caf\u00e9",
    20127: "plain ascii",
    437: "\u2591\u2592\u2593",
    850: "\u2591\u2592\u2593",
    866: "\u2591\u2592\u2593",
    20866: "\u2591\u2592\u2593",
    21866: "\u2591\u2592\u2593",
    65001: "caf\u00e9 \u4e2d\u6587",
}

#: Candidate declaration names.  Deliberately wide: the goal is to find the
#: table's shape, not to confirm the names already known.
NAMES: list[str] = [
    # Chinese
    "GBK", "gbk", "GB2312", "gb2312", "GB_2312-80", "csGB2312", "csgb2312",
    "GB18030", "gb18030", "GBK-2312", "gbk-2312",
    "cp936", "CP936", "936", "windows-936", "ms936",
    "x-gbk", "chinese", "Chinese", "gb_2312", "gb231280",
    # Japanese
    "Shift_JIS", "shift_jis", "sjis", "SJIS", "cp932", "932", "windows-31j",
    "x-sjis", "ms_kanji", "Japanese",
    # Korean
    "cp949", "949", "ks_c_5601-1987", "euc-kr", "EUC-KR", "ksc5601", "johab",
    # Traditional Chinese
    "Big5", "big5", "big-5", "cp950", "950", "cn-big5", "csbig5",
    # Western single-byte
    "windows-1252", "windows-1251", "windows-1250", "windows-1253",
    "windows-1254", "windows-1255", "windows-1256", "windows-1257",
    "windows-1258", "windows-874", "cp1252", "1252",
    "ISO-8859-1", "ISO8859-1", "iso-8859-1", "latin1", "latin-1", "L1",
    "ISO-8859-2", "ISO-8859-5", "ISO-8859-7", "ISO-8859-15",
    "US-ASCII", "ascii", "ASCII", "ANSI_X3.4-1968", "iso-ir-6", "646",
    "IBM437", "cp437", "IBM850", "cp866",
    # Unicode family
    "utf-8", "UTF-8", "utf8", "UTF8", "CP65001",
    "utf-16", "UTF-16", "utf-16le", "utf-16be", "ucs-2", "UCS-2",
    "utf-32",
    # nonsense controls
    "x-nonexistent-page", "", " ",
]


def decl(name: str) -> bytes:
    return f'<?xml version="1.0" encoding="{name}"?>\n'.encode("ascii")


#: Extra decode questions, independent of names.
EXTRA: dict[str, tuple[bytes, str]] = {
    # A GBK lead byte immediately before the newline: is \n taken as the trail?
    "dangling-lead-eol": (decl("GBK") + b"ok\n\x81\nnext\n",
                          "dangling lead byte at end of line"),
    # A lead byte at EOF with nothing after it.
    "dangling-lead-eof": (decl("GBK") + b"ok\n\x81",
                          "dangling lead byte at EOF"),
    # A lead byte followed by a byte that is never a valid trail (0x7F).
    "invalid-pair": (decl("GBK") + b"ok\n\x81\x7f\nnext\n",
                     "lead + invalid trail"),
    # A valid trail range boundary: 0x40 and 0xFE.
    "pair-boundaries": (decl("GBK") + b"\x81\x40\n\x81\xfe\n\x81\x7e\n",
                        "pair boundary trails"),
    # The invalid byte on line 4, to check the reported line number.
    "error-line-4": (decl("GBK") + b"a\nb\nc\n\xff\n", "error on line 4"),
}


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8f-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"candidate pages: {len(SAMPLES_TEXT)}   candidate names: {len(NAMES)}\n")

    # Bytes for each page's sample sentence, produced by the OS encoder so the
    # comparison uses one table rather than Python's codecs.
    SAMPLES: dict[int, bytes] = {cp: cp_encode(cp, t)
                                 for cp, t in SAMPLES_TEXT.items()}

    # Precompute the OS decode of the fingerprint under every candidate page, so
    # a measured result can be labelled by comparison.
    fp_table: dict[int, str] = {cp: cp_decode(cp, FINGERPRINT) for cp in SAMPLES}
    utf8_fallback = cp_decode(65001, FINGERPRINT)

    def oracle_texts(body: str) -> list[str]:
        texts = re.findall(r"<text [^>]*>(.*?)</text>", body)
        return [t.replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&amp;", "&") for t in texts]

    def run_case(tag: str, payload: bytes) -> dict:
        """One Oracle call.  Both sides get the same bytes: this probe asks what
        the decoder produced, not how two files differ."""
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
        return {
            "tag": tag,
            "oracle_exit": run.exit_code,
            "errors": [e[0] for e in
                       re.findall(r"<(error\d)>(.*?)</error\d>", body)],
            "texts": oracle_texts(body),
            "body": body,
        }

    # ---------------------------------------------------------------- A: names
    print("=== A. name resolution (fingerprint match) ===")
    name_records: list[dict] = []
    for i, name in enumerate(NAMES):
        payload = decl(name) + FINGERPRINT if name.strip() else FINGERPRINT
        r = run_case(f"name-{i:02d}", payload)
        # The fingerprint lines are the last N text elements (the declaration is
        # line 1 when present).
        body_lines = [t for t in r["texts"] if not t.lstrip().startswith("<")]
        joined = "".join(body_lines)
        # A page matches when every byte's decode agrees.
        match = [cp for cp, s in fp_table.items() if s == joined]
        if not match and joined == utf8_fallback:
            verdict = "utf-8 (unresolved)"
        elif match:
            verdict = f"cp{match[0]}"
        else:
            verdict = f"UNKNOWN {joined!r}"
        name_records.append({"name": name, "verdict": verdict,
                             "decoded": joined, "errors": r["errors"]})
        print(f"  {name!r:<20} -> {verdict}")

    # ------------------------------------------------------------ B: fidelity
    print("\n=== B. decode fidelity: BC vs the OS table ===")
    fid_records: list[dict] = []
    for cp, sample in SAMPLES.items():
        if cp == 65001:
            continue
        payload = decl(f"probe-cp{cp}") + sample + b"\n"
        # Feed the *name* that resolved to this page, so the page is selected.
        names_for = [n for n in name_records if n["verdict"] == f"cp{cp}"]
        if not names_for:
            continue
        name = names_for[0]["name"]
        r = run_case(f"fid-{cp}", decl(name) + sample + b"\n")
        want = cp_decode(cp, sample)
        got = [t for t in r["texts"] if not t.lstrip().startswith("<")]
        got = "".join(got)
        same = got == want
        fid_records.append({"cp": cp, "name": name, "same": same,
                            "want": want, "got": got,
                            "errors": r["errors"]})
        print(f"  cp{cp:<6} via {name!r:<14} {'MATCH' if same else 'DIFFER'}"
              f"  errors={','.join(r['errors']) or '-'}")
        if not same:
            print(f"      want={want!r}")
            print(f"      got ={got!r}")

    # ------------------------------------------------------------- C: extras
    print("\n=== C. dangling / invalid sequences ===")
    extra_records: list[dict] = []
    for tag, (payload, purpose) in EXTRA.items():
        r = run_case(tag, payload)
        lines = [t for t in r["texts"] if not t.lstrip().startswith("<")]
        extra_records.append({"tag": tag, "purpose": purpose,
                              "lines": lines, "errors": r["errors"]})
        print(f"  {tag:<18} errors={','.join(r['errors']) or '-'}")
        print(f"      lines={lines}")

    (run_dir / "u8f-results.json").write_text(
        json.dumps({"names": name_records, "fidelity": fid_records,
                    "extras": extra_records}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nraw: {run_dir / 'u8f-results.json'}")

    # ------------------------------------------------------------ D: GB18030
    print("\n=== D. GB18030 two-byte range vs GBK (OS-side, no Oracle) ===")
    diff = 0
    checked = 0
    for lead in range(0x81, 0xFF):
        for trail in list(range(0x40, 0x7F)) + list(range(0x80, 0xFF)):
            pair = bytes([lead, trail])
            a = cp_decode(936, pair, strict=True)
            b = cp_decode(54936, pair, strict=True)
            checked += 1
            if a != b:
                diff += 1
                if diff <= 5:
                    print(f"  {pair.hex()}: gbk={a!r} gb18030={b!r}")
    print(f"  checked {checked} pairs, {diff} differ")

    print("\n=== resolved-name summary ===")
    resolved = sorted({n["verdict"] for n in name_records
                       if not n["verdict"].startswith("utf-8")})
    print(f"  distinct pages reached: {resolved}")
    unresolved = [n["name"] for n in name_records
                  if n["verdict"] == "utf-8 (unresolved)"]
    print(f"  unresolved ({len(unresolved)}): {unresolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
