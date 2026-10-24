#!/usr/bin/env python3
"""U8 verification -- both engines over the whole measured code-page envelope.

The `u8*` probes were exploratory: each one ran the Oracle to *discover* a rule,
and several were corrected mid-flight when a result contradicted their own
expectation. This tool is the durable form of what they found: it drives the
Oracle and the product over a fixed corpus of the measured cases and asserts
their normalized reports are identical.

That distinction matters. A probe answers "what does BC do?"; this answers "does
the product still do it?" -- so it can be re-run after any change and it fails
loudly when a rule regresses. `U8-FINDINGS.md` is the evidence ledger; this is
the regression guard.

Corpus coverage (each entry cites the probe it came from):

| group | from | what it pins |
|---|---|---|
| declared page | u8b/u8c | the name selects a page; syntax accept/reject |
| name table | u8d/u8f | resolved vs refused names, incl. the cp1252 ASCII family |
| precedence | u8c | BOM beats declaration; declaration beats valid-UTF-8 body |
| error reporting | u8g | line numbers, loose decode + `<errorN>` together |
| NUL heuristic | u8/u8b | BOM-less UTF-16 detection and its envelope |
| no-autodetect | u8 | BOM-less legacy bytes stay UTF-8 lossy |

Usage (serial -- never alongside pytest or another Oracle user):
    cd D:\\Rea\\product\\verify
    python tools/u8_verify.py             # every case
    python tools/u8_verify.py --list      # corpus only
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
VERIFY = REA / "product" / "verify"
sys.path.insert(0, str(VERIFY))

from harness import installs as inst_mod  # noqa: E402
from harness import normalize as norm_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

PRODUCT = REA / "product" / "cli" / "target" / "release" / "reacmp.exe"

GBK_CE_SHI = b"\xb2\xe2\xca\xd4"                      # 测试 in GBK
UTF8_CE_SHI = "\u6d4b\u8bd5".encode("utf-8")
SJIS_TEST = b"\x83\x65\x83\x58\x83\x67"                # テスト in Shift_JIS
UTF8_TEST = "\u30c6\u30b9\u30c8".encode("utf-8")
CP1252_CAFE = b"caf\xe9"                               # café in cp1252
UTF8_CAFE = "caf\u00e9".encode("utf-8")


def decl(name: str) -> bytes:
    return f'<?xml version="1.0" encoding="{name}"?>\n'.encode("ascii")


#: name -> (left bytes, right bytes, source probe)
CASES: dict[str, tuple[bytes, bytes, str]] = {
    # ---- the declared page selects a code page (u8b) ----
    "decl-gbk": (decl("GBK") + GBK_CE_SHI + b"\n",
                 decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8b"),
    "decl-gbk-lower": (decl("gbk") + GBK_CE_SHI + b"\n",
                       decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8b"),
    "decl-gb2312": (decl("gb2312") + GBK_CE_SHI + b"\n",
                    decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8b"),
    "decl-single-quote": (decl("GBK").replace(b'"GBK"', b"'GBK'") + GBK_CE_SHI + b"\n",
                          decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8c"),
    "decl-no-version": (b'<?xml encoding="GBK"?>\n' + GBK_CE_SHI + b"\n",
                        decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8e"),
    "decl-extra-attr": (
        b'<?xml version="1.0" encoding="GBK" standalone="yes"?>\n' + GBK_CE_SHI + b"\n",
        decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8e"),
    "decl-mixed-case": (decl("GbK") + GBK_CE_SHI + b"\n",
                        decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8e"),
    "decl-shiftjis": (decl("Shift_JIS") + SJIS_TEST + b"\n",
                      decl("UTF-8") + UTF8_TEST + b"\n", "u8b"),
    "decl-windows1252": (decl("windows-1252") + CP1252_CAFE + b"\n",
                         decl("UTF-8") + UTF8_CAFE + b"\n", "u8b"),
    "decl-big5": (decl("Big5") + "\u4e2d\u6587".encode("big5") + b"\n",
                  decl("UTF-8") + "\u4e2d\u6587".encode("utf-8") + b"\n", "u8e"),

    # ---- names BC refuses: the declaration must be ignored (u8d/u8f) ----
    "name-cp936-refused": (decl("cp936") + GBK_CE_SHI + b"\n",
                           decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8b"),
    "name-936-refused": (decl("936") + GBK_CE_SHI + b"\n",
                         decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8f"),
    "name-windows936-refused": (decl("windows-936") + GBK_CE_SHI + b"\n",
                                decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8b"),
    "name-utf16-refused": (decl("utf-16") + GBK_CE_SHI + b"\n",
                           decl("utf-8") + UTF8_CE_SHI + b"\n", "u8c"),
    "name-nonexistent": (decl("x-nonexistent-page") + GBK_CE_SHI + b"\n",
                         decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8d"),

    # ---- the ASCII family resolves to cp1252 (u8f) ----
    "name-us-ascii-is-1252": (decl("US-ASCII") + CP1252_CAFE + b"\n",
                              decl("windows-1252") + CP1252_CAFE + b"\n", "u8f"),
    "name-latin1-is-1252": (decl("latin1") + CP1252_CAFE + b"\n",
                            decl("windows-1252") + CP1252_CAFE + b"\n", "u8f"),

    # ---- syntax rejections (u8c/u8e) ----
    "syntax-attr-upper": (decl("GBK").replace(b"encoding", b"ENCODING") + GBK_CE_SHI + b"\n",
                          decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8c"),
    "syntax-spaces": (b'<?xml version="1.0"   encoding = "GBK"  ?>\n' + GBK_CE_SHI + b"\n",
                      decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8c"),
    "syntax-no-quote": (b'<?xml version="1.0" encoding=GBK?>\n' + GBK_CE_SHI + b"\n",
                        decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8c"),
    "syntax-unterminated": (b'<?xml version="1.0" encoding="GBK"\n' + GBK_CE_SHI + b"\n",
                            decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8c"),
    "syntax-no-encoding": (b'<?xml version="1.0"?>\n' + GBK_CE_SHI + b"\n",
                           decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8e"),

    # ---- precedence (u8c) ----
    "bom-beats-decl": (
        b"\xff\xfe" + decl("GBK").decode("ascii").encode("utf-16-le")
        + "\u6d4b\u8bd5".encode("utf-16-le") + b"\n\x00",
        b"\xff\xfe" + decl("UTF-8").decode("ascii").encode("utf-16-le")
        + "\u6d4b\u8bd5".encode("utf-16-le") + b"\n\x00", "u8c"),
    "decl-after-utf8-bom": (b"\xef\xbb\xbf" + decl("GBK") + GBK_CE_SHI + b"\n",
                            b"\xef\xbb\xbf" + decl("UTF-8") + UTF8_CE_SHI + b"\n",
                            "u8c"),
    "decl-line2-ignored": (b"junk\n" + decl("GBK") + GBK_CE_SHI + b"\n",
                           b"junk\n" + decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8c"),
    "decl-beats-valid-utf8": (decl("GBK") + UTF8_CE_SHI + b"\n",
                              decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8b"),
    "decl-utf8-is-noop": (decl("UTF-8") + UTF8_CE_SHI + b"\n",
                          decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8b"),

    # ---- error reporting under a declared page (u8g) ----
    "err-line-2": (decl("GBK") + b"\xff\nok\nok\n",
                   decl("UTF-8") + b"x\nok\nok\n", "u8g"),
    "err-line-4": (decl("GBK") + b"a\nb\n\xff\nc\n",
                   decl("UTF-8") + b"a\nb\nx\nc\n", "u8g"),
    "err-two-bad-lines": (decl("GBK") + b"\xff\nok\n\xfe\n",
                          decl("UTF-8") + b"x\nok\ny\n", "u8g"),
    "err-dangling-eof": (decl("GBK") + b"ok\n\x81",
                         decl("UTF-8") + b"ok\n", "u8g"),
    # The lead byte consumes the following newline, so the GBK file's lines are
    # [decl, ok, ?next]. The right file spells that result out literally, which
    # keeps the case a test of the *swallow rule* rather than of how the aligner
    # pairs a 1-vs-2 tail (that tie-break is tracked separately, below).
    "err-lead-swallows-newline": (decl("GBK") + b"ok\n\x81\nnext\n",
                                  decl("UTF-8") + b"ok\n?next\n", "u8g"),
    "err-clean-gbk": (decl("GBK") + GBK_CE_SHI + b"\n",
                      decl("UTF-8") + UTF8_CE_SHI + b"\n", "u8g"),

    # ---- the NUL-parity heuristic (u8/u8b) ----
    "nul-utf16le": (b"a\x00b\x00\n\x00", b"a\nb\n", "u8b"),
    "nul-utf16le-dense": (b"a\x00b\x00c\x00\n\x00", b"a\nb\nc\n", "u8b"),
    "nul-utf16be": (b"\x00a\x00b\x00\n", b"a\nb\n", "u8b"),
    "nul-utf16le-short": (b"a\x00\n\x00", b"a\n", "u8b"),
    "nul-below-threshold": (b"ab\x00cd\x00\n\x00", b"ab\ncd\n", "u8b"),
    "nul-both-parities": (b"a\x00\x00\x00b\x00\x00\x00", b"ab", "u8c"),
    "nul-len2-not-detected": (b"\x00a", b"\x00a", "u8c"),

    # ---- no auto-detection: BOM-less legacy bytes stay UTF-8 lossy (u8) ----
    "no-autodetect-collapse": (GBK_CE_SHI + b"\n", b"\xca\xd4\xb2\xe2\n", "u8"),
    "no-autodetect-gbk-vs-utf8": (GBK_CE_SHI + b"\n", UTF8_CE_SHI + b"\n", "u8"),
    "no-autodetect-overlap": (b"\xd6\xd0\n", b"\xc8\xcb\n", "u8"),
    "no-autodetect-error-line": (b"one\ntwo\n" + GBK_CE_SHI + b"\n",
                                 b"one\ntwo\nthree\n", "u8"),

    # `tail-tiebreak-1v2` was the U8 corpus's only known difference: the shape
    # BC resolves as `rightorphan x` followed by `?next`/`next`, while the
    # product paired `?next`/`x` and orphaned `next` -- an equal-cost 1-vs-2
    # tail tie. `probes/u8h_alignment_tiebreak.py` proved it was a pre-existing
    # alignment tie-break, not a code-page effect, and it was tracked with the
    # M2.6 Myers items. On 2026-10-14 the M2.6 alignment fix (important-text
    # anchoring plus closeness pairing, `core/src/align.rs`) resolved it; the
    # case now compares byte-identical and lives here as a regression guard
    # (`runs/u8-verify-20261014T153156Z/` ran it as a pass against the live
    # oracle before this move).
    "tail-tiebreak-1v2": (decl("GBK") + b"ok\n\x81\nnext\n",
                          decl("UTF-8") + b"ok\nx\nnext\n", "u8h"),
}

#: Cases whose two engines are known to differ, counted separately: never a
#: pass, never deleted, never special-cased in the product. Currently empty:
#: the last member, `tail-tiebreak-1v2`, was resolved by the M2.6 alignment
#: fix and moved into CASES above.
KNOWN_DIFFERENCES: dict[str, tuple[bytes, bytes, str]] = {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--filter", default=None)
    args = ap.parse_args()

    if args.list:
        for name, (_, _, src) in CASES.items():
            print(f"  {name:<32} from {src}")
        for name, (_, _, src) in KNOWN_DIFFERENCES.items():
            print(f"  {name:<32} from {src}   [known difference]")
        print(f"\n{len(CASES)} cases, {len(KNOWN_DIFFERENCES)} known difference"
              f"{'s' if len(KNOWN_DIFFERENCES) != 1 else ''}")
        return 0

    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("u8-verify-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (run_dir / "oracle").mkdir(parents=True, exist_ok=True)
    (run_dir / "product").mkdir(parents=True, exist_ok=True)

    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    print(f"oracle  : {inst.oracle_path} ({inst.oracle_version})")
    print(f"product : {PRODUCT}\n")

    records: list[dict] = []
    passed = failed = known = 0
    corpus = [(n, lb, rb, src, False) for n, (lb, rb, src) in CASES.items()]
    corpus += [(n, lb, rb, src, True)
               for n, (lb, rb, src) in KNOWN_DIFFERENCES.items()]
    for name, lb, rb, source, is_known in corpus:
        if args.filter and args.filter not in name:
            continue
        lp, rp = fx / f"{name}-L.txt", fx / f"{name}-R.txt"
        lp.write_bytes(lb)
        rp.write_bytes(rb)

        lines = ['text-report layout:xml output-to:"%3" "%1" "%2"']
        script = orc.write_script(run_dir / "oracle" / f"{name}.bcs", lines)
        o_out = run_dir / "oracle" / f"{name}.xml"
        run = orc.run(inst.oracle_path, script, str(lp), str(rp), o_out,
                      timeout=180.0, script_text="\n".join(lines))

        p_out = run_dir / "product" / f"{name}.xml"
        proc = subprocess.run(
            [str(PRODUCT), str(lp), str(rp), str(p_out)],
            capture_output=True, timeout=120)

        detail = ""
        ok = False
        o_exists = o_out.exists() and o_out.stat().st_size > 0
        p_exists = p_out.exists() and p_out.stat().st_size > 0
        if not o_exists or not p_exists:
            detail = f"missing report (oracle={o_exists} product={p_exists})"
        else:
            try:
                o_norm = norm_mod.normalize(
                    norm_mod.read_report(o_out), path=str(o_out)).text
                p_norm = norm_mod.normalize(
                    norm_mod.read_report(p_out), path=str(p_out)).text
                ok = o_norm == p_norm
                if not ok:
                    ol, pl = o_norm.splitlines(), p_norm.splitlines()
                    for i in range(max(len(ol), len(pl))):
                        a = ol[i] if i < len(ol) else "<none>"
                        b = pl[i] if i < len(pl) else "<none>"
                        if a != b:
                            detail = (f"line {i + 1}: "
                                      f"oracle={a.strip()[:70]!r} "
                                      f"product={b.strip()[:70]!r}")
                            break
            except Exception as exc:  # noqa: BLE001 -- report, never hide
                detail = f"normalize/compare failed: {exc}"

        if ok:
            passed += 1
            mark = "OK  "
        elif is_known:
            # A known difference is not a pass: it is counted separately and
            # named, so it stays visible without being asserted as correct.
            known += 1
            mark = "KD  "
        else:
            failed += 1
            mark = "FAIL"
        records.append({"name": name, "source": source, "pass": ok,
                        "known_difference": is_known,
                        "oracle_exit": run.exit_code,
                        "product_exit": proc.returncode,
                        "detail": detail,
                        "left_hex": lb.hex(), "right_hex": rb.hex()})
        print(f"  {mark} {name:<32} oracle={run.exit_code:<4} "
              f"product={proc.returncode:<4}"
              + (f"  {detail}" if not ok else ""))

    total = passed + failed
    print(f"\n{passed}/{total} passed, {failed} failed, {known} known "
          f"difference{'s' if known != 1 else ''}")
    (run_dir / "u8-verify.json").write_text(
        json.dumps({"oracle": {"path": str(inst.oracle_path),
                               "version": inst.oracle_version},
                    "product": str(PRODUCT),
                    "passed": passed, "failed": failed, "known": known,
                    "records": records}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"raw: {run_dir / 'u8-verify.json'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
