#!/usr/bin/env python3
"""Link DFM event handlers to code via Delphi published-method RTTI strings.

Delphi stores published method names as ShortStrings in the class RTTI tables,
together with the method's code pointer. Finding the name string and the code
pointer that sits near it resolves UI handler -> address -> unit.

Strategy:
  1. read the handler names from the decoded DFMs;
  2. locate each name as a ShortString in the image;
  3. scan a window around it for a plausible code pointer (0x140001000..0x141c9c844);
  4. map that pointer through function-attribution.json for the unit.

Usage: python tools/ui-event-map.py
"""
import os, re, json, sys, struct, collections

FORMS = r'D:\Rea\extracted\forms'
ATTR = r'D:\Rea\extracted\function-attribution.json'
EXE = r'D:\bc-official\app\BCompare.exe'
OUT = r'D:\Rea\extracted\ui-event-map.json'
EVENT_RE = re.compile(r'^\s*(On[A-Z][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\s*$')


def main():
    data = open(EXE, 'rb').read()
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

    def off2va(off):
        for _nm, va, vsz, ro, rsz in secs:
            if ro <= off < ro + rsz:
                return img_base + va + (off - ro)
        return None

    def va2off(va_img):
        rva = va_img - img_base
        for _nm, va, vsz, ro, rsz in secs:
            if va <= rva < va + max(vsz, rsz):
                o = ro + (rva - va)
                if 0 <= o < len(data):
                    return o
        return None

    attr = json.load(open(ATTR, encoding='utf-8'))
    by_entry = {k.lower().replace('0x', ''): v for k, v in attr.items()}

    # text range for code
    code_lo, code_hi = None, None
    for nm, va, vsz, ro, rsz in secs:
        if nm == '.text':
            code_lo, code_hi = img_base + va, img_base + va + vsz

    # ---- collect handlers from DFMs
    events = collections.defaultdict(list)
    per_form = {}
    for fn in sorted(os.listdir(FORMS)):
        if not fn.endswith('.dfm'):
            continue
        form = fn[:-4]
        n = 0
        for line in open(os.path.join(FORMS, fn), encoding='utf-8', errors='ignore'):
            m = EVENT_RE.match(line)
            if m:
                events[m.group(2)].append({'form': form, 'event': m.group(1)})
                n += 1
        if n:
            per_form[form] = n

    # ---- resolve each handler
    rows = []
    resolved = 0
    for handler, uses in sorted(events.items()):
        pat = handler.encode('latin-1')
        # find ShortString occurrences: length byte then the name
        candidates = []
        start = 0
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            start = i + 1
            if i > 0 and data[i - 1] == len(pat):
                candidates.append(i - 1)   # position of the length byte
        addr = None
        for c in candidates:
            # scan the following 0x40 bytes for a code pointer
            for d in range(1, 0x40, 1):
                if c + d + 8 > len(data):
                    break
                v, = struct.unpack_from('<Q', data, c + d)
                if code_lo and code_lo <= v < code_hi:
                    addr = v
                    break
            if addr:
                break
        info = by_entry.get(f'{addr:x}', {}) if addr else {}
        if addr:
            resolved += 1
        rows.append({
            'handler': handler,
            'forms': sorted({u['form'] for u in uses}),
            'events': sorted({u['event'] for u in uses}),
            'address': f'0x{addr:x}' if addr else None,
            'unit': info.get('unit'),
            'size': info.get('size'),
        })

    by_unit = collections.Counter(r['unit'] for r in rows if r['unit'])
    print(f'forms with events : {len(per_form)}')
    print(f'distinct handlers : {len(events)}')
    print(f'resolved to code  : {resolved}')
    print(f'with unit         : {sum(1 for r in rows if r["unit"])}')
    print('\n== handlers by unit (top 30) ==')
    for u, c in by_unit.most_common(30):
        print(f'  {u:30s} {c}')
    print('\n== sample resolved ==')
    shown = 0
    for r in rows:
        if r['unit']:
            print(f"  {r['handler']:36s} {r['address']:>12s}  {r['unit']}")
            shown += 1
            if shown >= 25:
                break

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'forms': per_form, 'handlers': rows}, f, indent=1)
    print(f'\nwritten: {OUT}')


if __name__ == '__main__':
    main()
