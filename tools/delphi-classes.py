#!/usr/bin/env python3
"""Extract all Delphi class names from BCompare.exe VMTs.

Delphi x64 VMT layout (verified against TSsPersistentParent @ 0x14067bee8):
  VMT - 0x50 : pointer to the class-name ShortString (first byte = length, then ASCII)
  VMT - 0x48 : pointer to the TypeInfo / parent-class table
  VMT - 0x40 ... : method table (first virtual slot at VMT + 0x00)

Strategy: scan the whole image for pointers whose target looks like a Delphi class
name ShortString ("T" + PascalCase, plausible length), then read the class name and
report the VMT (which is the slot table this pointer belongs to + 0x50).

Usage: python tools/delphi-classes.py [exe] [out.json]
"""
import struct, sys, json, re

NAME_RE = re.compile(r'^T[A-Z][A-Za-z0-9_]{2,60}$')


def load(path):
    data = open(path, 'rb').read()
    e = struct.unpack_from('<I', data, 0x3c)[0]
    coff = e + 4
    num_sec, = struct.unpack_from('<H', data, coff + 2)
    opt_sz, = struct.unpack_from('<H', data, coff + 16)
    opt = coff + 20
    magic, = struct.unpack_from('<H', data, opt)
    img_base = struct.unpack_from('<Q', data, opt + 24)[0] if magic == 0x20b else struct.unpack_from('<I', data, opt + 28)[0]
    secs = []
    so = opt + opt_sz
    for _ in range(num_sec):
        nm = data[so:so + 8].rstrip(b'\0').decode('latin-1')
        vsz, va, rsz, ro = struct.unpack_from('<IIII', data, so + 8)
        secs.append((nm, va, vsz, ro, rsz))
        so += 40
    return data, img_base, secs


def mk_map(data, img_base, secs):
    def rva2off(va_img):
        rva = va_img - img_base
        for _nm, va, vsz, ro, rsz in secs:
            if va <= rva < va + max(vsz, rsz):
                off = ro + (rva - va)
                if 0 <= off < len(data):
                    return off
        return None
    return rva2off


def main():
    exe = sys.argv[1] if len(sys.argv) > 1 else r'D:\bc-official\app\BCompare.exe'
    out = sys.argv[2] if len(sys.argv) > 2 else r'D:\Rea\extracted\delphi-classes.json'
    data, img_base, secs = load(exe)
    rva2off = mk_map(data, img_base, secs)

    # Pass 1: index every ShortString that looks like a class name in the image.
    # A Delphi class-name ShortString is at a 2-byte aligned address, length 3..61,
    # and the bytes are printable ASCII starting with 'T'.
    name_at = {}
    for _nm, va, vsz, ro, rsz in secs:
        base_va = img_base + va
        blob = data[ro:ro + rsz]
        p = 0
        limit = len(blob) - 2
        while p < limit:
            L = blob[p]
            if 3 <= L <= 61 and 1 < p and blob[p - 1] in (0, 0x00):
                s = blob[p + 1:p + 1 + L]
                if len(s) == L and all(32 <= c < 127 for c in s):
                    txt = s.decode('latin-1')
                    if NAME_RE.match(txt):
                        name_at[base_va + p] = txt
            p += 1

    # Pass 2: find pointers to these names, at VMT-0x50.
    vmt_to_name = {}
    for _nm, va, vsz, ro, rsz in secs:
        base_va = img_base + va
        blob = data[ro:ro + rsz]
        for p in range(0, len(blob) - 8, 8):
            v, = struct.unpack_from('<Q', blob, p)
            if v in name_at:
                vmt = base_va + p + 0x50
                vmt_to_name[vmt] = name_at[v]

    print(f'class-name ShortStrings found : {len(name_at)}')
    print(f'VMTs resolved                 : {len(vmt_to_name)}')

    rows = []
    for vmt, name in sorted(vmt_to_name.items(), key=lambda kv: kv[1]):
        # parent pointer at VMT-0x48 -> another VMT
        off = rva2off(vmt - 0x48)
        parent = None
        if off is not None:
            pv, = struct.unpack_from('<Q', data, off)
            if pv in vmt_to_name:
                parent = vmt_to_name[pv]
        # instance size at VMT-0x40 (Delphi x64: vmtInstanceSize)
        off = rva2off(vmt - 0x40)
        isize = None
        if off is not None:
            iv, = struct.unpack_from('<I', data, off)
            if 8 <= iv < 0x100000:
                isize = iv
        rows.append({'class': name, 'vmt': f'0x{vmt:x}', 'parent': parent,
                     'instance_size': isize,
                     'direct_parent': parent})

    with open(out, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=1)

    groups = {}
    for r in rows:
        k = r['class'][:5]
        groups.setdefault(k, []).append(r)
    print('\n== class families (first 5 chars) ==')
    for k in sorted(groups, key=lambda x: -len(groups[x]))[:22]:
        print(f'  {k:6s}: {len(groups[k]):4d}   e.g. ' +
              ', '.join(r['class'] for r in groups[k][:4]))

    print('\n== Dir / View related ==')
    for r in rows:
        c = r['class']
        if any(c.startswith(p) for p in ('TDir', 'TView', 'TFile', 'TText', 'THex',
                                         'TTable', 'TReg', 'TVfs', 'TVFS', 'TOp',
                                         'TSession', 'TBcSession', 'TBcState')):
            print(f"  {c:42s} vmt={r['vmt']:>12s} parent={r['parent']} size={r['instance_size']}")
    print(f'\nwritten: {out}')


if __name__ == '__main__':
    main()
