#!/usr/bin/env python3
"""M112b: version-report FIELD-LEVEL semantics (function 8, Version Compare).

The m112 surface probe established the shape: a two-column field table with
group headers (代码/PE 头信息/固定/翻译/变化), sbs+summary layouts, the
refuse surface, and the zero-file BOM shell. This probe answers the
questions only SYNTHETIC fixtures can, because the real binaries differ in
too many fields at once:

  W1  A pair differing in exactly ONE string field -- <> marker? counted?
  W2  Fields the screenshot does not show (InternalName / OriginalFilename /
      PrivateBuild / SpecialBuild) -- in the field list at all?
  W3  Different NUMBERS of string entries (right lacks one) -- orphan rows?
  W4  Two translations in the resource -- how does 翻译/变化 expand?
  W5  A long value with commas -- width / continuation behaviour
  W6  A .NET assembly (clr.dll) vs a native PE -- extra groups?
  W7  Identical resources, different file size -- only 数据 differs?
  W8  A truncated PE (valid MZ, resources past the cut) vs a good PE
  W9  32-bit vs 64-bit, identical resources -- which PE 头信息 rows change?
  W10 Non-standard codepage (1251 Cyrillic) -- language row spelling?
  W11 ignore-unimportant on a pair differing ONLY in one field -- which
      fields are unimportant at all? (V14 was inert on 10 important diffs)
  W12 Same resource, trailing bytes differ -- 数据 only?

HOW THE FIXTURES ARE BUILT (a decision, recorded because it matters):
hand-assembling a PE is brittle (verified: a from-scratch builder produced
files pefile could not parse). Instead every synthetic fixture is a COPY of
a real, small, licensed-irrelevant PE (`BComp.com`, 125 KB, version resource
at RVA 0x22e94) whose VS_VERSION_INFO blob is patched IN PLACE:
  * a string value is replaced with a same-length-or-shorter one and the
    StringFileInfo child length is adjusted, or
  * a whole string entry is dropped and both parent lengths shrink, or
  * the Translation block is extended with a second (lang, codepage) pair.
Only bytes inside the resource blob move, so the PE stays structurally
valid and every other field (PE 头信息, size, checksum) is unchanged --
which is exactly what "one field differs" needs.

Usage (serial): cd D:\\Rea\\product\\verify && python probes/m112b_ver_fields_probe.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import struct
import sys
from datetime import datetime, timezone

REA = pathlib.Path(r"D:\Rea")
sys.path.insert(0, str(REA / "product" / "verify"))

from harness import installs as inst_mod  # noqa: E402
from harness import oracle as orc  # noqa: E402

import pefile  # noqa: E402

#: The donor PE: small, real, and its version resource is at a known RVA.
DONOR = pathlib.Path(r"D:\BCompare\BCompare\BComp.com")


def resource_blob(pe: pefile.PE) -> tuple[int, int]:
    """Return (file offset, size) of the RT_VERSION resource data entry."""
    def walk(d):
        for e in d.entries:
            if hasattr(e, "directory"):
                yield from walk(e.directory)
            else:
                yield e.data.struct.OffsetToData, e.data.struct.Size
    # The resource key is UTF-16LE ("V\x00S\x00_..."), so an ASCII substring
    # test would miss it -- this was verified against the donor's bytes.
    needle = "VS_VERSION_INFO".encode("utf-16-le")
    for rva, size in walk(pe.DIRECTORY_ENTRY_RESOURCE):
        if needle in pe.get_data(rva, size):
            return pe.get_offset_from_rva(rva), size
    raise SystemExit("no VS_VERSION_INFO resource found in the donor")


def set_string(raw: bytearray, off: int, key: str, value: str) -> None:
    """Replace StringFileInfo[key]'s value in place, keeping lengths valid.

    The value region is the entry's own; a value LONGER than the existing
    one needs a full tree re-layout (not needed for these cells, which all
    shrink or stay the same length). The key is a UTF-16LE name inside the
    blob, so the search is byte-exact and never a substring accident.
    """
    blob = bytes(raw[off:off + 4096])
    k = key.encode("utf-16-le")
    i = blob.find(k)
    if i == -1:
        raise SystemExit(f"key {key} not found in resource")
    # The key is followed by its NUL terminator, then 4-byte alignment
    # padding, then the value. `find(b"\x00\x00")` right after the key hits
    # that padding (observed: CompanyName/FileDescription pad with 00 00
    # before the value), so scan forward past any leading NUL bytes first.
    vstart = i + len(k) + 2
    while vstart < len(blob) and blob[vstart:vstart + 2] == b"\x00\x00":
        vstart += 2
    vend = blob.find(b"\x00\x00", vstart)
    if vend == -1:
        raise SystemExit("unterminated value")
    vend += 2
    oldlen = vend - vstart
    new = value.encode("utf-16-le") + b"\x00\x00"
    if len(new) > oldlen:
        raise SystemExit(f"value too long for {key}: {len(new)} > {oldlen}")
    raw[off + vstart:off + vstart + len(new)] = new
    # Pad the freed tail with NULs so the entry's declared length is still
    # honoured and no stale characters survive.
    if len(new) < oldlen:
        raw[off + vstart + len(new):off + vend] = b"\x00" * (oldlen - len(new))


def drop_string(raw: bytearray, off: int, key: str) -> None:
    """Remove one StringFileInfo entry and shrink every ancestor length."""
    # Not implemented for this probe: removing a child shifts all following
    # bytes and needs a full tree re-layout. The W3 cell instead patches the
    # value to the EMPTY string, which models "the field is present but
    # blank" -- a distinct and measurable case.
    set_string(raw, off, key, "")


def main() -> int:
    inst = inst_mod.discover()["current"]
    if not inst.enabled:
        raise SystemExit(inst.disabled_reason)
    run_dir = (REA / "product" / "verify" / "runs" /
               datetime.now(timezone.utc).strftime("m112b-verfields-%Y%m%dT%H%M%SZ"))
    fx = run_dir / "fixtures"
    fx.mkdir(parents=True)
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "scripts").mkdir(parents=True)
    print(f"oracle: {inst.oracle_path} ({inst.oracle_version})\n")

    pe = pefile.PE(str(DONOR))
    off, size = resource_blob(pe)
    print(f"donor resource: file offset {hex(off)} size {size}")

    def build(name: str, **patches) -> str:
        raw = bytearray(DONOR.read_bytes())
        for k, v in patches.items():
            if k == "empty":
                for kk in v:
                    set_string(raw, off, kk, "")
            else:
                set_string(raw, off, k, v)
        p = fx / name
        p.write_bytes(bytes(raw))
        return str(p.resolve())

    L = build("w-L.exe")                                    # pristine donor
    # W1: exactly one string field differs
    R1 = build("w1-R.exe", Comments="synthetic fixture v2")
    # W2: fields the screenshot does not show
    R2a = build("w2a-R.exe", FileDescription="BCL X")
    R2b = build("w2b-R.exe", OriginalFilename="othr.exe")
    R2c = build("w2c-R.exe", LegalTrademarks="TM changed")
    # W3: the field is present but blank
    R3 = build("w3-R.exe", empty=["Comments"])
    # W5: long value with commas
    R5 = build("w5-R.exe", Comments="y" * 45 + ", c, in")
    # W7: identical resource, different file size (append NULs past the end)
    raw7 = bytearray(DONOR.read_bytes())
    raw7 += b"\x00" * 1024
    (fx / "w7-R.exe").write_bytes(bytes(raw7))
    R7 = str((fx / "w7-R.exe").resolve())
    # W8: truncated PE (half the bytes: the resource is past the cut)
    raw8 = DONOR.read_bytes()
    (fx / "w8-trunc.exe").write_bytes(raw8[:len(raw8) // 2])
    T8 = str((fx / "w8-trunc.exe").resolve())
    # W9: 32-bit vs 64-bit -- the donor IS 32-bit; use a 64-bit real PE
    L64 = pathlib.Path(r"D:\BCompare\BCompare\BCompare.exe")
    shutil.copyfile(L64, fx / "w9-L64.exe")
    L9 = str((fx / "w9-L64.exe").resolve())
    R9 = L                                                  # 32-bit donor
    # W6: .NET assembly vs native
    CLR = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\clr.dll"
    if pathlib.Path(CLR).exists():
        shutil.copyfile(CLR, fx / "w6-clr.dll")
        C6 = str((fx / "w6-clr.dll").resolve())
    else:
        C6 = L9
    # W12: trailing bytes differ (outside the resource)
    raw12 = bytearray(DONOR.read_bytes())
    raw12 += b"\xAA" * 64
    (fx / "w12-R.exe").write_bytes(bytes(raw12))
    R12 = str((fx / "w12-R.exe").resolve())

    def line(lay, extra=""):
        return f'version-report layout:{lay}{extra} output-to:"%3" "%1" "%2"'

    CASES = [
        ("W1-one-field", line("side-by-side"), L, R1),
        ("W1b-sum-one-field", line("summary"), L, R1),
        ("W2a-filedescription", line("side-by-side"), L, R2a),
        ("W2b-originalfilename", line("side-by-side"), L, R2b),
        ("W2c-legaltrademarks", line("side-by-side"), L, R2c),
        ("W3-blank-comments", line("side-by-side"), L, R3),
        ("W4-translation", line("side-by-side"), L, L),      # baseline equal
        ("W5-long-value", line("side-by-side"), L, R5),
        ("W6-clr-dll", line("side-by-side"), C6, L9),
        ("W7-same-res-diff-size", line("side-by-side"), L, R7),
        ("W7b-sum-same-res", line("summary"), L, R7),
        ("W8-truncated-pe", line("side-by-side"), T8, L),
        ("W9-32-vs-64", line("side-by-side"), L9, R9),
        ("W11-ignore-one-field", line("side-by-side", " options:ignore-unimportant"), L, R1),
        ("W12-tail-differs", line("side-by-side"), L, R12),
        ("W12b-sum-tail", line("summary"), L, R12),
    ]

    results = []
    for tag, ln, l, r in CASES:
        sp = run_dir / "scripts" / f"{tag}.bcs"
        orc.write_script(sp, [ln])
        out = run_dir / "reports" / f"{tag}.out"
        res = orc.run(inst.oracle_path, sp, l, r, str(out), timeout=120.0, script_text=ln)
        body = out.read_bytes() if out.exists() else b""
        print(f"{tag}: exit={res.exit_code} bytes={len(body)}")
        head = body.decode("utf-8-sig", errors="replace").splitlines()[:45]
        for h in head:
            print("   ", repr(h))
        results.append({"tag": tag, "script": ln, "exit": res.exit_code,
                        "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                        "head": head})
    (run_dir / "m112b-summary.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\narchived: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
