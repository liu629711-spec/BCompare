#!/usr/bin/env python3
"""U8 probe -- the code-page cascade, measured rather than assumed.

Why this probe exists
---------------------

The product decodes every non-BOM file as **UTF-8 lossy** and has no code-page
concept beyond that (`core/src/lines.rs`).  Two questions decide whether that is
correct or merely convenient, and neither can be answered from the specs:

1. **Does BC decode a legacy multibyte encoding (GBK/CP936) at all?**
   `specs/ss/SsCodePage.md` describes a cascade whose step 3 validates UTF-8 and
   says nothing about what happens when validation *fails*;
   `specs/ss/SsLineParse.md` claims there is no ANSI fallback on the `.txt`
   path.  A claim in a spec is not a measurement.

2. **The false-`same` risk.**  GBK ``测试`` is ``B2 E2 CA D4`` and GBK ``试测`` is
   ``CA D4 B2 E2``.  Under lossy UTF-8 **both** decode to four U+FFFD, so a naive
   decoder reports them **identical**.  If BC agrees, that is BC behaviour to
   replicate; if BC disagrees, the product has a real correctness bug that no
   existing anchor covers (every `enc-*` anchor uses *equal-length* fixtures, so
   none of them can detect a collapse).

Host dependence -- read this before drawing conclusions
------------------------------------------------------

``SsCodePage.md`` says the ANSI fallback calls ``GetACP()``.  On **this** host the
ACP is **65001 (UTF-8)**, not 936, so "fall back to ANSI" here means "stay on
UTF-8" -- the legacy behaviour is *unreachable* on this machine by that route.
The probe records the ACP so the finding is never read as host-independent: any
result that depends on the ACP is marked, and the ANSI-fallback question stays
open on a 936 host.

What is measured
----------------

| Case | Question |
|---|---|
| `gbk-collapse`    | do two different GBK strings both become `same`? (false-`same` risk) |
| `gbk-same`        | identical GBK bytes: `same`, and is `<errorN>` emitted? |
| `gbk-vs-utf8`     | GBK bytes vs the UTF-8 spelling of the same text |
| `gbk-overlap`     | GBK ``中`` is also *valid* UTF-8 (U+0590) -- does BC notice? |
| `xml-decl-gbk`    | does `encoding="GBK"` in an XML declaration select a code page? |
| `xml-decl-bogus`  | an unknown declaration name must be ignored, not fatal |
| `utf16le-nobom`   | the NUL-parity heuristic (spec: odd>0.6, even<0.02) |
| `utf16be-nobom`   | the same, mirrored |
| `gbk-error-line`  | which line number an undecodable line reports |

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python probes/u8_codepage_cascade.py
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

#: 测试 and 试测 in GBK: the same four bytes in a different order.  Both are
#: invalid UTF-8, and lossy decoding maps each to four U+FFFD -- so any decoder
#: without a code page cannot tell them apart.
GBK_CE_SHI = b"\xb2\xe2\xca\xd4"          # 测试
GBK_SHI_CE = b"\xca\xd4\xb2\xe2"          # 试测
UTF8_CE_SHI = "测试".encode("utf-8")

#: 中 (D6 D0) and 人 (C8 CB) in GBK.  Both byte pairs happen to be *valid* UTF-8
#: (two-byte sequences), so a lossy decoder turns them into U+0590 / U+0232 --
#: wrong characters, no error, and the file looks perfectly decodable.
GBK_ZHONG = b"\xd6\xd0"
GBK_REN = b"\xc8\xcb"

XML_DECL_GBK = '<?xml version="1.0" encoding="GBK"?>\n'.encode("ascii")
XML_DECL_UTF8 = '<?xml version="1.0" encoding="UTF-8"?>\n'.encode("ascii")
XML_DECL_BOGUS = '<?xml version="1.0" encoding="NOT-A-REAL-CP"?>\n'.encode("ascii")

#: name -> (left bytes, right bytes, what the case is for)
CASES: dict[str, tuple[bytes, bytes, str]] = {
    "gbk-collapse": (
        GBK_CE_SHI + b"\n", GBK_SHI_CE + b"\n",
        "different GBK text that collapses to the same lossy UTF-8",
    ),
    "gbk-same": (
        GBK_CE_SHI + b"\n", GBK_CE_SHI + b"\n",
        "identical GBK bytes (control for the collapse case)",
    ),
    "gbk-vs-utf8": (
        GBK_CE_SHI + b"\n", UTF8_CE_SHI + b"\n",
        "GBK bytes vs the UTF-8 spelling of the same characters",
    ),
    "gbk-overlap": (
        GBK_ZHONG + b"\n", GBK_REN + b"\n",
        "two GBK characters that are also valid (but different) UTF-8",
    ),
    "xml-decl-gbk": (
        XML_DECL_GBK + GBK_CE_SHI + b"\n", XML_DECL_UTF8 + UTF8_CE_SHI + b"\n",
        "encoding=\"GBK\" declaration vs the UTF-8 spelling",
    ),
    "xml-decl-bogus": (
        XML_DECL_BOGUS + GBK_CE_SHI + b"\n", XML_DECL_BOGUS + GBK_CE_SHI + b"\n",
        "unknown declaration name: ignored, or fatal?",
    ),
    "utf16le-nobom": (
        b"a\x00b\x00\n\x00", b"a\nb\n",
        "UTF-16LE without BOM (NUL-parity heuristic)",
    ),
    "utf16be-nobom": (
        b"\x00a\x00b\x00\n", b"a\nb\n",
        "UTF-16BE without BOM (mirrored heuristic)",
    ),
    "gbk-error-line": (
        b"one\ntwo\n" + GBK_CE_SHI + b"\n", b"one\ntwo\nthree\n",
        "undecodable bytes on line 3 of 3 -- which line is reported?",
    ),
}


def acp() -> tuple[str, str, list[str]]:
    """The host ANSI/OEM code pages, read from the registry rather than guessed.

    ``GetACP()`` is what the spec says the ANSI fallback uses, so the value has
    to travel with every result: on a 936 host the whole probe could answer
    differently.
    """
    notes: list[str] = []
    a = o = ""
    try:
        out = subprocess.run(
            ["reg", "query", r"HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage",
             "/v", "ACP"],
            capture_output=True, text=True, timeout=30)
        m = re.search(r"ACP\s+REG_SZ\s+(\S+)", out.stdout)
        if m:
            a = m.group(1)
    except (OSError, subprocess.SubprocessError) as exc:
        notes.append(f"ACP unreadable: {exc}")
    try:
        out = subprocess.run(
            ["reg", "query", r"HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage",
             "/v", "OEMCP"],
            capture_output=True, text=True, timeout=30)
        m = re.search(r"OEMCP\s+REG_SZ\s+(\S+)", out.stdout)
        if m:
            o = m.group(1)
    except (OSError, subprocess.SubprocessError) as exc:
        notes.append(f"OEMCP unreadable: {exc}")
    return a, o, notes


def main() -> int:
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8-probe-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)

    a, o, notes = acp()
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"product : {PRODUCT}")
    print(f"host ACP: {a or '?'}   OEMCP: {o or '?'}")
    for n in notes:
        print(f"  note  : {n}")
    if a == "65001":
        print("  NOTE: ACP is UTF-8, so BC's ANSI fallback *is* UTF-8 here;")
        print("        legacy-ANSI behaviour is unreachable on this host.")
    print()

    records: list[dict] = []
    for tag, (lb, rb, purpose) in CASES.items():
        lp, rp = fx / f"{tag}-L.txt", fx / f"{tag}-R.txt"
        lp.write_bytes(lb)
        rp.write_bytes(rb)

        # --- Oracle (one call at a time, always) ---
        o_out = run_dir / "reports" / f"{tag}.oracle.xml"
        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "reports" / f"{tag}.bcs", lines)
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))
        o_body = ""
        if run.report_exists and run.report_bytes:
            o_body = o_out.read_bytes().decode("utf-8-sig", errors="replace")

        # --- product ---
        p_out = run_dir / "reports" / f"{tag}.product.xml"
        proc = subprocess.run([str(PRODUCT), str(lp), str(rp), str(p_out)],
                              capture_output=True, timeout=120)
        p_body = ""
        if p_out.exists():
            p_body = p_out.read_bytes().decode("utf-8-sig", errors="replace")

        def shape(body: str) -> dict:
            """The parts of the report that answer the questions above."""
            errs = re.findall(r"<(error\d)>(.*?)</error\d>", body)
            statuses = re.findall(r'<linecomp status="([a-z]+)"', body)
            texts = re.findall(r"<text ([^>]*)>(.*?)</text>", body)
            return {
                "errors": errs,
                "statuses": statuses,
                "texts": [t[1] for t in texts],
                "has_correct_chinese": "测试" in body,
                "fffd_count": body.count("\ufffd"),
            }

        o_s, p_s = shape(o_body), shape(p_body)
        agree = (o_s["errors"] == p_s["errors"]
                 and o_s["statuses"] == p_s["statuses"])
        records.append({
            "tag": tag,
            "purpose": purpose,
            "left_hex": lb.hex(),
            "right_hex": rb.hex(),
            "host_acp": a,
            "host_oemcp": o,
            "oracle_exit": run.exit_code,
            "oracle": o_s,
            "product_exit": proc.returncode,
            "product": p_s,
            "agree": agree,
            "oracle_body": o_body,
            "product_body": p_body,
        })

        mark = "OK  " if agree else "DIFF"
        print(f"  {mark} {tag:<16} oracle exit={run.exit_code:<4} "
              f"statuses={o_s['statuses']} errs={[e[0] for e in o_s['errors']]}")
        if not agree:
            print(f"       {'':<16} product exit={proc.returncode:<4} "
                  f"statuses={p_s['statuses']} "
                  f"errs={[e[0] for e in p_s['errors']]}")

    (run_dir / "u8-results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nraw: {run_dir / 'u8-results.json'}")

    # The decisive questions, answered from the recorded bodies rather than from
    # a summary of them.
    print("\n=== decisive readings ===")
    by_tag = {r["tag"]: r for r in records}

    c = by_tag["gbk-collapse"]
    if c["oracle"]["statuses"] and all(s == "same" for s in c["oracle"]["statuses"]):
        print("  gbk-collapse   : BC returns `same` -> BC itself collapses "
              "distinct GBK text; lossy UTF-8 REPLICATES BC on this host.")
    else:
        print(f"  gbk-collapse   : BC returns {c['oracle']['statuses']} -> BC "
              "distinguishes them; lossy UTF-8 is a real false-`same` bug.")

    d = by_tag["gbk-vs-utf8"]
    print(f"  gbk-vs-utf8    : BC {d['oracle']['statuses']}  "
          f"correct-Chinese-in-report={d['oracle']['has_correct_chinese']}  "
          f"U+FFFD count={d['oracle']['fffd_count']}")

    e = by_tag["xml-decl-gbk"]
    print(f"  xml-decl-gbk   : BC {e['oracle']['statuses']}  "
          f"correct-Chinese-in-report={e['oracle']['has_correct_chinese']}  "
          f"U+FFFD count={e['oracle']['fffd_count']}")

    g = by_tag["utf16le-nobom"]
    h = by_tag["utf16be-nobom"]
    print(f"  utf16le-nobom  : BC {g['oracle']['statuses']} "
          f"(same => NUL-parity heuristic fired)")
    print(f"  utf16be-nobom  : BC {h['oracle']['statuses']} "
          f"(same => mirrored heuristic fired)")

    i = by_tag["gbk-error-line"]
    print(f"  gbk-error-line : BC {i['oracle']['errors']} "
          f"statuses={i['oracle']['statuses']}")

    print("\n=== text as BC rendered it (the decode evidence) ===")
    for tag in ("gbk-collapse", "gbk-vs-utf8", "xml-decl-gbk", "gbk-overlap"):
        r = by_tag[tag]
        print(f"  {tag}:")
        print(f"    oracle : {r['oracle']['texts']}")
        print(f"    product: {r['product']['texts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
