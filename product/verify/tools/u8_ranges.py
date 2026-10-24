#!/usr/bin/env python3
"""u8-ranges -- can the multi-byte pages be stored as ranges instead of grids?

A faithful decoder needs the real tables (``tools/u8_tables.py`` established
that ``MultiByteToWideChar`` is the source, and that BC's declared-page decode
matches its *loose* mode).  A raw grid is ~48 KB per page, which is a lot of
source for a dependency-free crate, so this measures whether each page compresses
into ``(code_start, code_end, unicode_start)`` runs with a constant step -- the
shape Big5/GBK/SJIS tables are usually built from.

It also measures the **loose** fallback for invalid input, because BC emits
``U+F8F5`` for a lone ``0xFF`` under a declared GBK page while still reporting
``<error1>``: replicating that needs the fallback values, not just the valid grid.

Usage:
    python tools/u8_ranges.py
"""
from __future__ import annotations

import ctypes
import sys

_k32 = ctypes.windll.kernel32
MB_ERR_INVALID_CHARS = 0x00000008

PAGES = {"gbk": 936, "sjis": 932, "big5": 950}

#: Trail-byte ranges that can follow a lead byte on each page, as ``GetCPInfo``
#: does not report them.  Measured by probing every pair rather than assumed.
def trails_for(cp: int, lead: int) -> list[int]:
    out = []
    for t in list(range(0x40, 0x7F)) + list(range(0x80, 0x100)):
        buf = ctypes.create_unicode_buffer(2)
        if _k32.MultiByteToWideChar(cp, MB_ERR_INVALID_CHARS, bytes([lead, t]),
                                    2, buf, 2):
            out.append(t)
    return out


def conv(cp: int, data: bytes, strict: bool) -> str:
    buf = ctypes.create_unicode_buffer(len(data) + 4)
    flags = MB_ERR_INVALID_CHARS if strict else 0
    n = _k32.MultiByteToWideChar(cp, flags, data, len(data), buf, len(buf))
    return "".join(buf[:n])


class _CPINFO(ctypes.Structure):
    _fields_ = [("MaxCharSize", ctypes.c_uint),
                ("DefaultChar", ctypes.c_byte * 2),
                ("LeadByte", ctypes.c_byte * 12)]


def leads(cp: int) -> list[int]:
    info = _CPINFO()
    if not _k32.GetCPInfo(cp, ctypes.byref(info)):
        return []
    lb = bytes(bytearray([b & 0xFF for b in info.LeadByte]))
    out = []
    for i in range(0, len(lb), 2):
        if lb[i] == 0:
            break
        out.extend(range(lb[i], lb[i + 1] + 1))
    return out


def main() -> int:
    for name, cp in PAGES.items():
        print(f"=== {name} (cp{cp}) ===")
        pairs: list[tuple[int, int, int]] = []  # (code, unicode, trail)
        lead_list = leads(cp)
        for lead in lead_list:
            for trail in trails_for(cp, lead):
                code = (lead << 8) | trail
                s = conv(cp, bytes([lead, trail]), True)
                pairs.append((code, ord(s), trail))
        print(f"  valid pairs: {len(pairs)}")

        # Compress on the FULL code value (lead<<8|trail) so runs are code-runs.
        runs: list[tuple[int, int, int, int]] = []  # (start, end, ustart, step)
        for code, u, _ in pairs:
            if runs:
                s, e, us, st = runs[-1]
                if code == e + 1:
                    # step constant? u must follow the same delta
                    step = u - us
                    if st == 0:
                        runs[-1] = (s, code, us, step)
                        continue
                    elif (code - s) * st == (u - us):
                        runs[-1] = (s, code, us, st)
                        continue
            runs.append((code, code, u, 0))
        # Normalise step-0 runs of length 1 into explicit entries, count both.
        singles = sum(1 for r in runs if r[1] == r[0])
        multi = [r for r in runs if r[1] != r[0] and r[3] != 0]
        print(f"  compressed runs: {len(runs)} "
              f"(singletons {singles}, stepped {len(multi)})")
        # Cost model: stepped run = 4 values; singleton = 2 values (code, u+)
        cost = singles * 2 + len(multi) * 4
        print(f"  values needed: {cost}  (~{cost * 2} bytes as u16)")

        steps: dict[int, int] = {}
        for r in runs:
            if r[1] != r[0] and r[3] != 0:
                steps[r[3]] = steps.get(r[3], 0) + 1
        common = sorted(steps.items(), key=lambda kv: -kv[1])[:6]
        print(f"  most common steps: "
              f"{[(f'0x{s:04x}', n) for s, n in common]}")

        # The loose fallback for invalid single bytes on this page.
        fb = []
        leadset = set(lead_list)
        for b in range(0x80, 0x100):
            if b in leadset:
                continue
            if not conv(cp, bytes([b]), True):
                loose = conv(cp, bytes([b]), False)
                fb.append((b, [f"U+{ord(c):04X}" for c in loose]))
        print(f"  loose fallback for non-lead high bytes ({len(fb)}):")
        print(f"    {[(hex(b), v) for b, v in fb]}")
        print()

    print("=== GB18030 four-byte range ===")
    cp = 54936
    # The linear four-byte region.  Boundaries measured, not assumed.
    for probe in (b"\x81\x30\x81\x30", b"\x81\x30\x84\x36", b"\x81\x35\xf4\x37",
                  b"\x84\x31\xa4\x39", b"\x90\x30\x81\x30"):
        s = conv(cp, probe, True)
        if s:
            print(f"  {probe.hex()} -> U+{ord(s):04X}")
        else:
            print(f"  {probe.hex()} -> invalid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
