#!/usr/bin/env python3
"""u8_sizes -- how large is a faithful, dependency-free code page table?

The decoder must reproduce ``MultiByteToWideChar`` (u8g measured BC's output as
byte-identical to it on all 23 pages it resolves).  The crate has no third-party
dependencies, so the tables have to be *in the source*, and the encoding choice
therefore matters: a raw grid is tens of kilobytes per DBCS page.

This measures the standard alternative -- per lead byte, runs of
``(trail_start, trail_end, unicode_start)`` with step 1 -- plus the single-byte
pages' 128-entry high halves, and prints the total so the decision is made on
numbers rather than on a guess about what "compresses well".

Usage:
    python tools/u8_sizes.py
"""
from __future__ import annotations

import ctypes

_k32 = ctypes.windll.kernel32
MB_ERR_INVALID_CHARS = 0x00000008


class _CPINFO(ctypes.Structure):
    _fields_ = [("MaxCharSize", ctypes.c_uint),
                ("DefaultChar", ctypes.c_byte * 2),
                ("LeadByte", ctypes.c_byte * 12)]


def cpinfo(cp: int) -> _CPINFO:
    i = _CPINFO()
    _k32.GetCPInfo(cp, ctypes.byref(i))
    return i


def lead_list(cp: int) -> list[int]:
    i = cpinfo(cp)
    lb = bytes(bytearray([b & 0xFF for b in i.LeadByte]))
    out: list[int] = []
    for j in range(0, len(lb), 2):
        if lb[j] == 0:
            break
        out.extend(range(lb[j], lb[j + 1] + 1))
    return out


def wide(cp: int, data: bytes) -> str | None:
    buf = ctypes.create_unicode_buffer(len(data) + 4)
    n = _k32.MultiByteToWideChar(cp, MB_ERR_INVALID_CHARS, data, len(data),
                                 buf, len(buf))
    return "".join(buf[:n]) if n else None


def measure_dbcs(cp: int) -> tuple[int, int, int]:
    """Returns (valid_pairs, runs, runs_with_step1_only)."""
    pairs = runs = step1 = 0
    for lead in lead_list(cp):
        row: list[tuple[int, int]] = []
        for trail in list(range(0x40, 0x7F)) + list(range(0x80, 0x100)):
            s = wide(cp, bytes([lead, trail]))
            if s:
                row.append((trail, ord(s)))
        pairs += len(row)
        i = 0
        while i < len(row):
            j = i
            while (j + 1 < len(row) and row[j + 1][0] == row[j][0] + 1
                   and row[j + 1][1] == row[j][1] + 1):
                j += 1
            runs += 1
            if j > i:
                step1 += 1
            i = j + 1
    return pairs, runs, step1


def measure_sbcs(cp: int) -> int:
    """Number of high bytes that are defined (each costs one u16)."""
    n = 0
    for b in range(0x80, 0x100):
        if wide(cp, bytes([b])):
            n += 1
    return n


DBCS = {936: "GBK", 932: "Shift_JIS", 950: "Big5", 949: "cp949", 1361: "johab"}
SBCS = {1250: "windows-1250", 1251: "windows-1251", 1252: "windows-1252",
        1253: "windows-1253", 1254: "windows-1254", 1255: "windows-1255",
        1256: "windows-1256", 1257: "windows-1257", 1258: "windows-1258",
        874: "windows-874", 28591: "ISO-8859-1", 28592: "ISO-8859-2",
        28595: "ISO-8859-5", 28597: "ISO-8859-7", 437: "IBM437",
        850: "IBM850", 866: "IBM866"}


def main() -> int:
    print("=== DBCS pages: run-length table ===")
    print(f"  {'page':<12} {'pairs':<7} {'runs':<7} {'stepped':<8} "
          f"{'bytes':<8} {'as u32x4':<10}")
    total = 0
    for cp, name in DBCS.items():
        pairs, runs, step1 = measure_dbcs(cp)
        nbytes = step1 * 4 + (runs - step1) * 3
        total += nbytes
        print(f"  {name:<12} {pairs:<7} {runs:<7} {step1:<8} "
              f"{nbytes:<8} {nbytes / 1024:.1f} KB")
    print(f"  {'DBCS total':<12} {'':<7} {'':<7} {'':<8} {total:<8} "
          f"{total / 1024:.1f} KB")

    print("\n=== single-byte pages: high-half table ===")
    sb = 0
    for cp, name in SBCS.items():
        n = measure_sbcs(cp)
        sb += n * 2
        print(f"  {name:<14} {n}/128 defined  {n * 2} B")
    print(f"  SBCS total: {sb} B ({sb / 1024:.1f} KB)")

    print("\n=== GB18030 four-byte range ===")
    # The four-byte region is algorithmic, not tabular: measure its boundaries
    # so the implementation can interpolate instead of storing ~1.1M points.
    probes = [("start", b"\x81\x30\x81\x30"),
              ("U+00A5", b"\x81\x30\x84\x36"),
              ("2-byte start", b"\x81\x30\x81\x2f")]
    for label, p in probes:
        s = wide(54936, p)
        print(f"  {p.hex():<12} {label:<14} -> {s!r} "
              f"{f'U+{ord(s):04X}' if s else ''}")

    print(f"\nTOTAL static table bytes: {(total + sb) / 1024:.1f} KB "
          f"(GB18030 four-byte range is computed)")
    print("\nNote: GB18030's four-byte region is a documented linear mapping; "
          "verify against the OS before relying on it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
