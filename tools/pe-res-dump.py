#!/usr/bin/env python3
"""Extract all non-DFM PE resources from BCompare.exe:
  ICON / GRP_ICON / BITMAP / PNG / CURSOR / STRING / VERSION / MANIFEST / others.

Usage: python tools/pe-res-dump.py [exe] [outdir]
"""
import struct, sys, os, json, collections

TYPE_DIR = {1: 'cursor', 2: 'bitmap', 3: 'icon', 4: 'menu', 5: 'dialog',
            6: 'string', 7: 'fontdir', 8: 'font', 9: 'accelerator',
            10: 'rcdata', 11: 'msgtable', 12: 'group_cursor', 14: 'group_icon',
            16: 'version', 17: 'dlginclude', 19: 'plugplay', 20: 'vxd',
            21: 'anicursor', 22: 'aniicon', 23: 'html', 24: 'manifest',
            240: 'dlginit', 241: 'toolbar'}


def main():
    exe = sys.argv[1] if len(sys.argv) > 1 else r'D:\bc-official\app\BCompare.exe'
    outdir = sys.argv[2] if len(sys.argv) > 2 else r'D:\Rea\extracted\resources'
    os.makedirs(outdir, exist_ok=True)
    data = open(exe, 'rb').read()

    e = struct.unpack_from('<I', data, 0x3c)[0]
    coff = e + 4
    num_sec, = struct.unpack_from('<H', data, coff + 2)
    opt_sz, = struct.unpack_from('<H', data, coff + 16)
    opt = coff + 20
    magic, = struct.unpack_from('<H', data, opt)
    dd_off = opt + (0x70 if magic == 0x20b else 0x60)
    res_rva, _ = struct.unpack_from('<II', data, dd_off + 2 * 8)
    secs = []
    so = opt + opt_sz
    for _ in range(num_sec):
        vsz, va, rsz, ro = struct.unpack_from('<IIII', data, so + 8)
        secs.append((va, vsz, ro, rsz))
        so += 40

    def rva2off(rva):
        for va, vsz, ro, rsz in secs:
            if va <= rva < va + max(vsz, rsz):
                off = ro + (rva - va)
                if 0 <= off < len(data):
                    return off
        return None

    base = rva2off(res_rva)
    leaves = []

    def walk(off, path, depth):
        if depth > 4 or off is None:
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

    counts = collections.Counter()
    strings_out = []
    manifest_path = version_path = None
    written = []

    for path, leaf, drva, dsz in leaves:
        if not path:
            continue
        t = path[0]
        off = rva2off(drva)
        if off is None:
            continue
        body = data[off:off + dsz]
        label = TYPE_DIR.get(t, str(t)) if isinstance(t, int) else str(t)
        counts[label] += 1
        name = str(path[1]) if len(path) > 1 else str(leaf)
        lang = path[2] if len(path) > 2 else 0

        if t == 6:  # STRING: UTF-16LE blocks of length-prefixed strings
            i = 0
            while i + 2 <= len(body):
                ln, = struct.unpack_from('<H', body, i)
                if ln == 0:
                    break
                s = body[i + 2:i + 2 + ln * 2].decode('utf-16le', 'replace')
                strings_out.append({'table': name, 'id': leaf, 'index': i, 'text': s})
                i += 2 + ln * 2
        elif t in (3, 1):  # ICON / CURSOR: raw image, write as-is
            ext = 'ico' if t == 3 else 'cur'
            fn = os.path.join(outdir, f'{label}_{name}_{lang}.{ext}')
            with open(fn, 'wb') as f:
                f.write(body)
            written.append(fn)
        elif t == 2:  # BITMAP: raw DIB; wrap with a BMP file header
            if len(body) < 40:
                continue
            bi_size, w, h, planes, bpp = struct.unpack_from('<IiiHH', body, 0)
            if bi_size < 40 or bi_size > len(body) or w == 0 or h == 0 or bpp == 0 or bpp > 32:
                fn = os.path.join(outdir, f'bitmap_{name}_{lang}.dib')
                with open(fn, 'wb') as f:
                    f.write(body)
                written.append(fn)
                continue
            comp, = struct.unpack_from('<I', body, 16)
            xppm, yppm = struct.unpack_from('<ii', body, 20)
            clrused, = struct.unpack_from('<I', body, 28)
            ncolor = clrused if clrused else (1 << bpp if bpp <= 8 else 0)
            pixoff = 14 + bi_size + ncolor * 4
            total = 14 + len(body)

            def u32(v):
                return max(0, min(0xFFFFFFFF, int(v)))

            hdr = b'BM' + struct.pack('<IHHI', u32(total), 0, 0, u32(pixoff))
            dib = struct.pack('<IiiHHIIiiII', bi_size, w, h, planes, bpp, comp, 0,
                              xppm, yppm, clrused, 0)
            fn = os.path.join(outdir, f'bitmap_{name}_{lang}.bmp')
            with open(fn, 'wb') as f:
                f.write(hdr + dib + body[bi_size:])
            written.append(fn)
        elif label == 'png' or (isinstance(t, str) and t.upper() == 'PNG'):
            fn = os.path.join(outdir, f'png_{name}_{lang}.png')
            with open(fn, 'wb') as f:
                f.write(body)
            written.append(fn)
        elif t == 24:
            if manifest_path is None:
                manifest_path = os.path.join(outdir, 'manifest.xml')
                open(manifest_path, 'wb').write(body)
        elif t == 16:
            if version_path is None:
                version_path = os.path.join(outdir, 'version.bin')
                open(version_path, 'wb').write(body)
        elif t in (12, 14):  # GRP_ICON / GRP_CURSOR: directory of the above
            ext = 'ico' if t == 14 else 'cur'
            fn = os.path.join(outdir, f'{label}_{name}_{lang}.{ext}')
            with open(fn, 'wb') as f:
                f.write(body)
            written.append(fn)
        else:
            fn = os.path.join(outdir, f'{label}_{name}_{lang}.bin')
            with open(fn, 'wb') as f:
                f.write(body)
            written.append(fn)

    if strings_out:
        with open(os.path.join(outdir, 'strings.json'), 'w', encoding='utf-8') as f:
            json.dump(strings_out, f, ensure_ascii=False, indent=1)

    print(f'exe      : {exe}')
    print(f'outdir   : {outdir}')
    print(f'leaves   : {len(leaves)}')
    print('\n== counts by type ==')
    for k, c in counts.most_common():
        print(f'  {k:14s}: {c}')
    print(f'\nfiles written   : {len(written)}')
    print(f'strings decoded : {len(strings_out)}')
    if version_path:
        print(f'version         : {version_path}')
    if manifest_path:
        print(f'manifest        : {manifest_path}')
    with open(os.path.join(outdir, 'resources-index.json'), 'w', encoding='utf-8') as f:
        json.dump({'counts': dict(counts), 'files': sorted(os.path.basename(w) for w in written),
                   'strings': len(strings_out)}, f, indent=1)


if __name__ == '__main__':
    main()
