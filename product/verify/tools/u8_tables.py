#!/usr/bin/env python3
"""u8-tables -- measure the code pages locally, via the same OS API BC uses.

The decoder needs real tables, and the only defensible source is
``MultiByteToWideChar`` -- the function ``SsCodePage.md`` shows BC calling.  A
hand-written or Python-codec table would be a second-hand copy that could drift
from BC's own behaviour without anything noticing.

This script *measures* and prints; it does not write source.  Its output is the
evidence behind whatever tables get generated, and it answers the questions that
decide the table format:

1. How large is each page's two-byte grid, and does GB18030's equal GBK's?
2. What does a *loose* conversion produce for an invalid byte, per page?
   (BC showed ``0xFF`` -> ``U+F8F5`` under a declared GBK page while still
   reporting ``<error1>``, which means BC decodes loosely and reports
   separately -- that rule must be measured, not assumed.)
3. Which sequences are *invalid* (strict conversion fails)?
4. Does GB18030's four-byte range follow the linear GB18030 algorithm?

Usage:
    python tools/u8_tables.py            # summary
    python tools/u8_tables.py --dump gbk # every entry of one page
"""
from __future__ import annotations

import argparse
import ctypes
import sys

_k32 = ctypes.windll.kernel32

MB_ERR_INVALID_CHARS = 0x00000008

#: The pages the Oracle resolved by name (u8b/u8d/u8e), with their Windows IDs.
PAGES: dict[str, int] = {
    "gbk": 936,
    "gb18030": 54936,
    "cp1252": 1252,
    "iso88591": 28591,
    "sjis": 932,
    "big5": 950,
}

#: Lead-byte ranges for the DBCS pages, as ``GetCPInfo`` reports them.  Read at
#: runtime rather than hardcoded so the grid follows the OS.
class _CPINFO(ctypes.Structure):
    _fields_ = [("MaxCharSize", ctypes.c_uint),
                ("DefaultChar", ctypes.c_byte * 2),
                ("LeadByte", ctypes.c_byte * 12)]


def lead_bytes(cp: int) -> list[tuple[int, int]]:
    info = _CPINFO()
    if not _k32.GetCPInfo(cp, ctypes.byref(info)):
        return []
    out: list[tuple[int, int]] = []
    lb = bytes(bytearray([b & 0xFF for b in info.LeadByte]))
    for i in range(0, len(lb), 2):
        if lb[i] == 0:
            break
        out.append((lb[i], lb[i + 1]))
    return out


def conv(cp: int, data: bytes, strict: bool) -> tuple[int, str]:
    """Return ``(units, text)``; ``units == 0`` means the strict call failed."""
    buf = ctypes.create_unicode_buffer(len(data) + 4)
    flags = MB_ERR_INVALID_CHARS if strict else 0
    n = _k32.MultiByteToWideChar(cp, flags, data, len(data), buf, len(buf))
    return n, "".join(buf[:n])


def grid(cp: int, leads: list[tuple[int, int]]) -> tuple[int, int, str, int]:
    """Walk the two-byte grid.  Returns (valid, invalid, digest, singles)."""
    import hashlib
    h = hashlib.sha256()
    valid = invalid = 0
    for lo, hi in leads:
        for lead in range(lo, hi + 1):
            for trail in list(range(0x40, 0x7F)) + list(range(0x80, 0xFF)) + [0xFF]:
                pair = bytes([lead, trail])
                n, _ = conv(cp, pair, True)
                if n:
                    valid += 1
                    h.update(pair)
                else:
                    invalid += 1
    return valid, invalid, h.hexdigest()[:16], 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", metavar="PAGE", default=None)
    args = ap.parse_args()

    if args.dump:
        cp = PAGES[args.dump]
        leads = lead_bytes(cp)
        print(f"# {args.dump} (cp{cp}) lead ranges: "
              f"{[(hex(a), hex(b)) for a, b in leads]}")
        for lo, hi in leads:
            for lead in range(lo, hi + 1):
                for trail in [0x40, 0x41, 0x7E, 0x80, 0xA1, 0xFE, 0xFF]:
                    pair = bytes([lead, trail])
                    n, s = conv(cp, pair, False)
                    ns, _ = conv(cp, pair, True)
                    print(f"  {pair.hex()} -> {'valid' if ns else 'INVALID'} "
                          f"loose={s!r} u+{ord(s):04X}" if n else
                          f"  {pair.hex()} -> empty")
        return 0

    print("=== page geometry ===")
    print(f"  {'page':<10} {'cp':<7} {'maxchar':<8} {'leads':<28} "
          f"{'valid2':<8} {'invalid2':<9} digest")
    for name, cp in PAGES.items():
        info = _CPINFO()
        ok = _k32.GetCPInfo(cp, ctypes.byref(info))
        mcs = info.MaxCharSize if ok else -1
        leads = lead_bytes(cp)
        if leads:
            v, iv, dig, _ = grid(cp, leads)
        else:
            v = iv = 0
            dig = "-"
        print(f"  {name:<10} {cp:<7} {mcs:<8} "
              f"{str([(hex(a), hex(b)) for a, b in leads]):<28} "
              f"{v:<8} {iv:<9} {dig}")

    print("\n=== direct comparison ===")
    print("  GB18030 two-byte grid vs GBK two-byte grid: see digests above "
          "(equal digest == identical accept/reject set)")

    print("\n=== single-byte behaviour (loose vs strict) ===")
    for name, cp in PAGES.items():
        if lead_bytes(cp):
            continue  # DBCS pages are covered by the grid
        bad_loose = bad_strict = 0
        sample = ""
        for b in range(0x80, 0x100):
            n_loose, s_loose = conv(cp, bytes([b]), False)
            n_strict, _ = conv(cp, bytes([b]), True)
            if not n_strict:
                bad_strict += 1
                if not sample:
                    sample = f"first strict-fail {b:#04x} -> loose {s_loose!r}"
            if not n_loose:
                bad_loose += 1
        print(f"  {name:<10} strict-fail={bad_strict}/128  "
              f"loose-fail={bad_loose}/128  {sample}")

    print("\n=== invalid-byte handling on the DBCS pages ===")
    for name in ("gbk", "sjis", "big5"):
        cp = PAGES[name]
        leads = lead_bytes(cp)
        print(f"  {name}:")
        # single high bytes that are not a lead byte
        leadset = set()
        for lo, hi in leads:
            leadset.update(range(lo, hi + 1))
        shown = 0
        for b in range(0x80, 0x100):
            if b in leadset:
                continue
            n_s, _ = conv(cp, bytes([b]), True)
            n_l, s_l = conv(cp, bytes([b]), False)
            if not n_s and shown < 4:
                print(f"    byte {b:#04x}: strict fail, loose -> {s_l!r} "
                      f"(U+{ord(s_l):04X})" if n_l else
                      f"    byte {b:#04x}: strict fail, loose -> empty")
                shown += 1
        # a lead byte with a bad trail
        if leads:
            lead = leads[0][0]
            pair = bytes([lead, 0x7F])  # 0x7F is never a valid trail
            n_s, _ = conv(cp, pair, True)
            n_l, s_l = conv(cp, pair, False)
            print(f"    pair {pair.hex()}: strict {'ok' if n_s else 'FAIL'}, "
                  f"loose -> {s_l!r}")

    print("\n=== GB18030 four-byte range ===")
    cp = PAGES["gb18030"]
    # 81 30 84 36 -> U+00A5 was measured.  Check the linear region's start.
    for pair4 in (b"\x81\x30\x81\x30", b"\x81\x30\x84\x36", b"\x82\x35\x8f\x33",
                  b"\xe3\x32\x9a\x35", b"\xfe\x39\xfe\x39"):
        n_s, s_s = conv(cp, pair4, True)
        n_l, s_l = conv(cp, pair4, False)
        if n_s:
            print(f"  {pair4.hex()} -> strict ok  U+{ord(s_s):04X} "
                  f"({s_s!r})  loose same={s_l == s_s}")
        else:
            print(f"  {pair4.hex()} -> strict FAIL loose={s_l!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
