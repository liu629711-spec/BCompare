#!/usr/bin/env python3
"""Probe a PE for Delphi DFM form resources (RT_RCDATA) and report the form inventory.

Answers: is the GUI layout embedded in the EXE as structured data we can decode?
DFM (Delphi Form) resources hold the complete control tree of every form:
control names, classes, positions, sizes, captions, tab order, and the NAMES
of event handler methods (OnClick = BtnXClick etc.).
"""
import struct, sys, collections, re


def main(path):
    data = open(path, 'rb').read()
    print(f"file : {path}")
    print(f"size : {len(data):,} bytes")
    assert data[:2] == b'MZ'
    e = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[e:e + 4] == b'PE\0\0', "not PE"
    coff = e + 4
    machine, = struct.unpack_from('<H', data, coff)
    num_sec, = struct.unpack_from('<H', data, coff + 2)
    opt_sz, = struct.unpack_from('<H', data, coff + 16)
    opt = coff + 20
    magic, = struct.unpack_from('<H', data, opt)
    dd_off = opt + (0x70 if magic == 0x20b else 0x60)
    res_rva, res_sz = struct.unpack_from('<II', data, dd_off + 2 * 8)
    print(f"machine=0x{machine:04x}  sections={num_sec}  optmagic=0x{magic:x}")
    print(f"resource directory: rva=0x{res_rva:x} size=0x{res_sz:x}")

    secs = []
    so = opt + opt_sz
    for _ in range(num_sec):
        name = data[so:so + 8].rstrip(b'\0').decode('ascii', 'replace')
        vsz, va, rsz, ro = struct.unpack_from('<IIII', data, so + 8)
        secs.append((name, va, vsz, ro, rsz))
        so += 40

    def rva2off(rva):
        for _n, va, vsz, ro, rsz in secs:
            if va <= rva < va + max(vsz, rsz):
                off = ro + (rva - va)
                if 0 <= off < len(data):
                    return off
        return None

    base = rva2off(res_rva)
    if base is None:
        print("no resource section")
        return

    leaves = []  # (path tuple, leaf-name-or-lang, data_rva, data_sz)

    def walk(off, path, depth):
        if depth > 4:
            return
        n_named, n_id = struct.unpack_from('<HH', data, off + 12)
        for i in range(n_named + n_id):
            ent = off + 16 + i * 8
            name_raw, off2 = struct.unpack_from('<II', data, ent)
            if name_raw & 0x80000000:
                noff = base + (name_raw & 0x7fffffff)
                ln, = struct.unpack_from('<H', data, noff)
                nm = data[noff + 2:noff + 2 + ln * 2].decode('utf-16le', 'replace')
            else:
                nm = name_raw
            if off2 & 0x80000000:
                walk(base + (off2 & 0x7fffffff), path + [nm], depth + 1)
            else:
                drva, dsz = struct.unpack_from('<II', data, base + off2)
                leaves.append((tuple(path), nm, drva, dsz))

    walk(base, [], 0)

    TYPE_NAMES = {1: 'CURSOR', 2: 'BITMAP', 3: 'ICON', 4: 'MENU', 5: 'DIALOG',
                  6: 'STRING', 7: 'FONTDIR', 8: 'FONT', 9: 'ACCELERATOR',
                  10: 'RCDATA', 12: 'GRP_CURSOR', 14: 'GRP_ICON',
                  16: 'VERSION', 24: 'MANIFEST'}

    by_type = collections.Counter()
    rcdata = []
    for path, leaf, drva, dsz in leaves:
        if not path:
            continue
        t = path[0]
        by_type[t] += 1
        if t == 10 and len(path) >= 2:
            rcdata.append((path[1], leaf, drva, dsz))

    print("\n== resource entries by type ==")
    for t, c in sorted(by_type.items(), key=lambda kv: (isinstance(kv[0], str), kv[0])):
        label = TYPE_NAMES.get(t, str(t)) if isinstance(t, int) else str(t)
        print(f"  {label:14s} : {c}")

    print(f"\n== RCDATA entries: {len(rcdata)} ==")
    sig = collections.Counter()
    classified = []  # (name, lang, size, kind, head)
    for name, lang, drva, dsz in rcdata:
        off = rva2off(drva)
        head = data[off:off + min(dsz, 48)] if off is not None else b''
        if head[:5] == b'DVCLAL':
            kind = 'DVCLAL'
        elif head[:4] == b'TPF0':
            kind = 'dfm-binary(TPF0)'
        elif head[:6] == b'object':
            kind = 'dfm-text'
        else:
            kind = 'other'
        sig[kind] += 1
        classified.append((name, lang, dsz, kind, head))

    for k, c in sig.most_common():
        print(f"  {k:18s}: {c}")

    forms = [c for c in classified if c[3].startswith('dfm')]
    print(f"\n=> DFM form resources found: {len(forms)}")

    print("\n== form resource names (RCDATA names) ==")
    names = sorted(set(str(n) for n, _, _, _, _ in classified))
    for i in range(0, min(len(names), 160), 4):
        print('  ' + '  '.join(f"{n:28s}" for n in names[i:i + 4]))
    if len(names) > 160:
        print(f"  ... and {len(names) - 160} more")

    # show a text DFM head if any
    for name, lang, dsz, kind, head in classified:
        if kind == 'dfm-text':
            off = rva2off(drva)
            body = data[off:off + 1200]
            print(f"\n== head of text DFM '{name}' ==")
            print(body.decode('utf-8', 'replace'))
            break
    else:
        # binary: extract printable strings
        for name, lang, dsz, kind, head in classified:
            if kind == 'dfm-binary(TPF0)':
                off = rva2off(drva)
                body = data[off:off + 2500]
                strs = re.findall(rb'[\x20-\x7e]{3,}', body)
                print(f"\n== printables from binary DFM '{name}' (first 2500 bytes) ==")
                print(' | '.join(s.decode('latin-1') for s in strs[:80]))
                break

    print("\n== whole-file raw signature counts ==")
    print("  b'TPF0'        :", data.count(b'TPF0'))
    print("  b'object '     :", data.count(b'object '))
    print("  utf16 'object ':", data.count('object '.encode('utf-16le')))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else r'D:\bc-official\app\BCompare.exe')
