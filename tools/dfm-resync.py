#!/usr/bin/env python3
"""Dump a DFM resource fully and try parsing from several start offsets to
isolate a structural anomaly (the child-object boundary encoding)."""
import sys, importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('dfmx', os.path.join(HERE, 'dfm-extract.py'))
dfmx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dfmx)


def get_res(exe, want):
    data = open(exe, 'rb').read()
    leaves, rva2off = dfmx.pe_resource_leaves(data)
    for path, leaf, drva, dsz in leaves:
        if not path or path[0] != 10:
            continue
        name = str(path[1]) if len(path) > 1 else str(leaf)
        if name == want:
            off = rva2off(drva)
            return data[off:off + dsz]
    return None


def dump(buf, lo, hi):
    lo = max(0, lo); hi = min(len(buf), hi)
    for off in range(lo - lo % 16, hi, 16):
        chunk = buf[off:off + 16]
        print(f'{off:6d}  {" ".join(f"{b:02x}" for b in chunk):<47s} |'
              + ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk) + '|')


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else 'TFILEVIEW'
    buf = get_res(r'D:\bc-official\app\BCompare.exe', want)
    print(f'=== {want}: {len(buf)} bytes ===')
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else len(buf)
    dump(buf, lo, hi)

    print('\n--- parse attempts from various offsets ---')
    for start in range(20, 34):
        d = dfmx.Dfm(buf)
        d.r.p = start
        out = []
        try:
            d.read_object(out, '')
            print(f'start={start:3d}: consumed {d.r.p}/{len(buf)}  '
                  f'{"FULL" if d.r.p == len(buf) else "short"}  root={out[0].strip()!r}')
        except Exception as ex:
            print(f'start={start:3d}: FAIL at {d.r.p}: {ex}')

    print('\n--- all 0xF? bytes outside binary blobs (structural escapes) ---')
    i = 0
    while i < len(buf):
        b = buf[i]
        if b in (10,):  # vaBinary: skip the blob
            pass
        i += 1
    # simpler: list offsets of f0..ff with 8 bytes of context
    hits = [i for i, b in enumerate(buf) if 0xf0 <= b <= 0xff]
    print(f'count={len(hits)}')
    for i in hits[:40]:
        ctx = buf[max(0, i - 6):i + 12]
        print(f'  {i:6d}: ' + ' '.join(f'{x:02x}' for x in ctx)
              + '   |' + ''.join(chr(x) if 32 <= x < 127 else '.' for x in ctx) + '|')


if __name__ == '__main__':
    main()
